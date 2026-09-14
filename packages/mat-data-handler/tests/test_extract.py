from mat_data_handler.extract import export_entry, load_document, parse_mapping
from mat_data_handler_data import entries_dir, mapping_path, schemas_dir


def test_export_copper():
    with entries_dir() as entries, schemas_dir() as schemas, mapping_path() as mapping_file:
        entry = load_document(entries / "copper.yaml")
        mapping = parse_mapping(mapping_file)
        records, notes = export_entry(entry, mapping, schemas)
    assert records[0]["props_position"] == 9
    assert any(r["key"] == "C11" for r in records)
