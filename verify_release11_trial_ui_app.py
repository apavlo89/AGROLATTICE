"""Trial-designer Streamlit harness used by verify_release11_0_ui.py."""
from __future__ import annotations

import os
from pathlib import Path

from maize_pollination_lab import PollinationDatabase, render_trial_designer_page


database = PollinationDatabase(Path(os.environ.get("AGROLATTICE_UI_TEST_DB", "/tmp/agrolattice_release11_ui.sqlite")))
render_trial_designer_page(db=database, project=None, locations=None, field_db=None)
