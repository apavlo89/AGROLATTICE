"""Streamlit render verification for AGROLATTICE 11.1 maize UI."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from streamlit.testing.v1 import AppTest


def _verify_analysis() -> None:
    app = AppTest.from_file("verify_release11_ui_app.py").run(timeout=45)
    if app.exception:
        raise AssertionError("Streamlit UI raised exceptions: " + " | ".join(str(item.value) for item in app.exception))
    labels = [tab.label for tab in app.tabs]
    expected = {"Parent physiology", "Mechanistic simulator", "Sowing strategy", "Genomics (optional)"}
    missing = expected.difference(labels)
    if missing:
        raise AssertionError(f"Mechanistic tabs are missing: {sorted(missing)}")


def _verify_trial_designer() -> None:
    trial_app = AppTest.from_file("verify_release11_trial_ui_app.py").run(timeout=45)
    if trial_app.exception:
        raise AssertionError("Trial-designer UI raised exceptions: " + " | ".join(str(item.value) for item in trial_app.exception))
    trial_labels = [tab.label for tab in trial_app.tabs]
    if "Leaf & ear development" not in trial_labels:
        raise AssertionError("Leaf & ear development protocol tab is missing.")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--child":
        {"analysis": _verify_analysis, "trial": _verify_trial_designer}[sys.argv[2]]()
        return
    with tempfile.TemporaryDirectory(prefix="agrolattice11_1-ui-") as temporary:
        environment = os.environ.copy()
        environment["AGROLATTICE_UI_TEST_DB"] = str(Path(temporary) / "ui.sqlite")
        script = str(Path(__file__).resolve())
        subprocess.run([sys.executable, script, "--child", "analysis"], check=True, env=environment)
        # Streamlit's AppTest/PyArrow runner is intentionally process-isolated:
        # two complex apps in one interpreter can crash inside Arrow teardown.
        subprocess.run([sys.executable, script, "--child", "trial"], check=True, env=environment)
        print("AGROLATTICE 11.1 Streamlit UI verification passed")


if __name__ == "__main__":
    main()
