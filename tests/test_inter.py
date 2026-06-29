"""Regression tests for the ``pyvisco.inter`` GUI controller.

The ipywidgets layer is excluded from coverage, but a small slice of the
controller -- the callbacks that mutate ``df_aT``/``df_master`` in response
to user input -- contains real data-handling logic that can regress
silently. These tests bypass ``Control.__init__`` (which builds widgets)
and exercise ``set_inp_aT`` directly on a hand-assembled instance.
"""

from __future__ import annotations

import types
import warnings

import pandas as pd
import pytest

from pyvisco import inter, load, master


@pytest.fixture
def manual_shift_gui(sample_data_dir):
    """Minimal ``inter.Control`` populated with the state ``set_inp_aT``
    reads and writes. ``RefT`` is picked in the middle of the available
    temperature sets so that both ``i_sel < i_ref`` and ``i_sel > i_ref``
    multi-row branches are reachable.
    """
    data = load.file(str(sample_data_dir / "time_user_raw.csv"))
    df_raw, arr_RefT, units = load.user_raw(data, domain="time", modul="E")
    RefT = float(arr_RefT.iloc[len(arr_RefT) // 2])
    df_aT, _dshift = master.get_aT(df_raw, RefT)
    df_master = master.get_curve(df_raw, df_aT, RefT)
    fig, lax = master.plot_shift(df_raw, df_master, units)

    gui = inter.Control.__new__(inter.Control)
    gui.df_raw = df_raw
    gui.df_aT = df_aT
    gui.df_master = df_master
    gui.RefT = RefT
    gui.units = units
    gui.fig_master_shift = fig
    gui.fig_master_shift_lax = lax
    gui.files = {}
    # ``set_inp_aT`` reads .value off these widget-like attrs.
    gui.cb_single = types.SimpleNamespace(value=True)
    gui.inp_T = types.SimpleNamespace(value=float(df_aT["T"].iloc[0]))
    gui.inp_aT = types.SimpleNamespace(value=0.0)
    return gui


def _row_for(gui, T):
    """Positional row index of temperature ``T`` in ``gui.df_aT``."""
    return int(gui.df_aT.index[gui.df_aT["T"] == T][0])


def test_set_inp_aT_single_row_mutates_df_aT(manual_shift_gui):
    """Single-row bump must actually change ``df_aT['log_aT']`` and rebuild
    the master curve.

    Regression: pandas >= 3 enforces Copy-on-Write, so the chained pattern
    ``self.df_aT['log_aT'].iloc[idx] += delta`` operates on a temporary
    copy and silently no-ops. The GUI then redraws an unchanged curve.
    """
    gui = manual_shift_gui
    gui.cb_single.value = True

    target_T = next(float(T) for T in gui.df_aT["T"] if T != gui.RefT)
    gui.inp_T.value = target_T
    row = _row_for(gui, target_T)

    before = gui.df_aT["log_aT"].to_numpy(copy=True)
    new_val = float(before[row]) + 1.5
    gui.set_inp_aT({"new": new_val})

    after = gui.df_aT["log_aT"].to_numpy()
    assert after[row] == pytest.approx(new_val)
    for i in range(len(after)):
        if i == row:
            continue
        assert after[i] == pytest.approx(before[i])

    # Master curve was rebuilt and the file-package side-effects fired.
    assert gui.df_master is not None
    assert {"df_master", "df_aT", "fig_master_shift"}.issubset(gui.files)


def test_set_inp_aT_multi_row_below_RefT_shifts_lower_block(manual_shift_gui):
    """With ``cb_single=False`` and the selected temperature below RefT,
    rows ``0..i_sel`` shift by the same delta and rows above are untouched.
    """
    gui = manual_shift_gui
    gui.cb_single.value = False

    ref_row = _row_for(gui, gui.RefT)
    assert ref_row > 0, "fixture must place RefT in the interior of the set range"
    target_row = ref_row - 1
    gui.inp_T.value = float(gui.df_aT["T"].iloc[target_row])

    before = gui.df_aT["log_aT"].to_numpy(copy=True)
    delta = 0.7
    gui.set_inp_aT({"new": float(before[target_row]) + delta})
    after = gui.df_aT["log_aT"].to_numpy()

    for i in range(0, target_row + 1):
        assert after[i] - before[i] == pytest.approx(delta)
    for i in range(target_row + 1, len(after)):
        assert after[i] == pytest.approx(before[i])


def test_set_inp_aT_multi_row_above_RefT_shifts_upper_block(manual_shift_gui):
    """With ``cb_single=False`` and the selected temperature above RefT,
    rows ``i_sel..n-1`` shift by the same delta and rows below are
    untouched.
    """
    gui = manual_shift_gui
    gui.cb_single.value = False

    ref_row = _row_for(gui, gui.RefT)
    assert ref_row < len(gui.df_aT) - 1
    target_row = ref_row + 1
    gui.inp_T.value = float(gui.df_aT["T"].iloc[target_row])

    before = gui.df_aT["log_aT"].to_numpy(copy=True)
    delta = -0.4
    gui.set_inp_aT({"new": float(before[target_row]) + delta})
    after = gui.df_aT["log_aT"].to_numpy()

    for i in range(0, target_row):
        assert after[i] == pytest.approx(before[i])
    for i in range(target_row, len(after)):
        assert after[i] - before[i] == pytest.approx(delta)


def test_set_inp_aT_noop_when_delta_zero(manual_shift_gui):
    """Setting log_aT to its current value must leave ``df_aT`` untouched
    and skip the master-curve rebuild / file-package update."""
    gui = manual_shift_gui
    gui.cb_single.value = True
    gui.inp_T.value = float(gui.df_aT["T"].iloc[0])
    current = float(gui.df_aT["log_aT"].iloc[0])

    snapshot = gui.df_aT.copy()
    gui.files.clear()
    gui.set_inp_aT({"new": current})

    pd.testing.assert_frame_equal(gui.df_aT, snapshot)
    assert gui.files == {}


def test_set_inp_aT_does_not_emit_chained_assignment_warnings(manual_shift_gui):
    """Belt-and-suspenders: ``set_inp_aT`` must not trip pandas'
    ``ChainedAssignmentError`` across any of its three branches.

    Catches the broader anti-pattern even on inputs where the visible
    output happens to look correct.
    """
    gui = manual_shift_gui

    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")

        gui.cb_single.value = True
        gui.inp_T.value = float(gui.df_aT["T"].iloc[0])
        gui.set_inp_aT({"new": float(gui.df_aT["log_aT"].iloc[0]) + 0.3})

        gui.cb_single.value = False
        ref_row = _row_for(gui, gui.RefT)
        if ref_row > 0:
            r = ref_row - 1
            gui.inp_T.value = float(gui.df_aT["T"].iloc[r])
            gui.set_inp_aT({"new": float(gui.df_aT["log_aT"].iloc[r]) + 0.2})
        if ref_row < len(gui.df_aT) - 1:
            r = ref_row + 1
            gui.inp_T.value = float(gui.df_aT["T"].iloc[r])
            gui.set_inp_aT({"new": float(gui.df_aT["log_aT"].iloc[r]) - 0.2})

    chained = [w for w in recorded if isinstance(w.message, pd.errors.ChainedAssignmentError)]
    assert chained == [], (
        f"Chained assignment regressed in set_inp_aT: {[str(w.message) for w in chained]}"
    )
