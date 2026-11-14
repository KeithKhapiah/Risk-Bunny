"""Streamlit entry point for the UPI Fraud Ring & Merchant Analytics dashboard."""

from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Streamlit reruns this file for every widget interaction.  run_path deliberately
# executes dashboard.py on each rerun; a normal import would be cached by Python
# and leave filter selections visually unchanged.
runpy.run_path(str(Path(__file__).with_name("dashboard.py")), run_name="__main__")
