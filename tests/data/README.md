# Test data

ANSYS APDL material card files used by the `verify.py` test suite.
Both cards contain the same 30-term Prony series (in `SHEAR` mode) for the
"E1 - Unexposed" material from Springer (2020); they differ only in the
shift function (WLF vs. user-supplied polynomial). They exercise the
`TBDATA` parsing paths in `verify.load_prony_ANSYS` (3-, 4-, and 5-field
records) and the `nterms` validation against the `TB,PRONY,...,nterms`
header.
