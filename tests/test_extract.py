from mat_data_handler.data_source import entries_dir, mapping_path, schemas_dir
from mat_data_handler.extract import export_entry, load_document, parse_mapping


def test_export_copper():
    entry = load_document(entries_dir() / "copper.yaml")
    mapping = parse_mapping(mapping_path())
    records, notes = export_entry(entry, mapping, schemas_dir())
    assert records[0]["props_position"] == 9
    assert any(r["key"] == "C11" for r in records)
