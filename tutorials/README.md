# Tutorials

Non-interactive walkthroughs of the pyvisco workflow. Run as either a Jupyter
notebook or a plain Python script — no `ipywidgets` / Voila required.

| File | Scenario | Input domain | Input type |
|---|---|---|---|
| [`tutorial.ipynb`](tutorial.ipynb) | End-to-end walkthrough | frequency | raw measurements (needs shifting) |
| [`freq_master.py`](freq_master.py) | Pre-shifted master curve | frequency | master |
| [`freq_raw.py`](freq_raw.py) | Build master from raw | frequency | raw |
| [`time_master.py`](time_master.py) | Time-domain master curve | time | master |

All four use input files from [`../sample_data/`](../sample_data/).

## Running

```bash
# Notebook
jupyter lab tutorials/tutorial.ipynb

# Scripts (figures saved into tutorials/_figures/)
python tutorials/freq_master.py
python tutorials/freq_raw.py
python tutorials/time_master.py
```
