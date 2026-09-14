from mat_data_handler.database import validate_only
from mat_data_handler_data import entries_dir, schemas_dir


def test_bundled_entries_validate():
    with entries_dir() as entries, schemas_dir() as schemas:
        count = validate_only(entries, schemas)
    assert count >= 1
