def read_xml_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()
