"""Point tests at a local mat-data checkout instead of fetching over the network.

Assumes the sibling layout used during development:
``~/Codes/mat-data-handler`` and ``~/Codes/mat-data``. CI instead sets
``MAT_DATA_LOCAL_PATH`` itself after checking out the ``mat-data`` repo.
"""

import os
from pathlib import Path

import pytest

_SIBLING_MAT_DATA = Path(__file__).resolve().parents[3] / "mat-data"


@pytest.fixture(autouse=True, scope="session")
def _mat_data_local_path():
    if "MAT_DATA_LOCAL_PATH" not in os.environ and _SIBLING_MAT_DATA.is_dir():
        os.environ["MAT_DATA_LOCAL_PATH"] = str(_SIBLING_MAT_DATA)
    if "MAT_DATA_LOCAL_PATH" not in os.environ:
        pytest.skip("MAT_DATA_LOCAL_PATH not set and no sibling mat-data checkout found")
    yield
