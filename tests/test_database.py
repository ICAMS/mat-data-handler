from mat_data_handler.data_source import entries_dir, schemas_dir
from mat_data_handler.database import validate_only


def test_bundled_entries_validate():
    count = validate_only(entries_dir(), schemas_dir())
    assert count >= 1
