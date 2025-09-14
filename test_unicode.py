from json import dumps

# Test unicode escaping
test_string = "Fïx ïssüé wïth äüthéntïcätïön"
json_output = dumps({"issue_title": test_string})
print("JSON output:", json_output)
print("Contains escaped unicode:", "F\\u00efx \\u00efss\\u00fc\\u00e9 w\\u00efth \\u00e4\\u00fcth\\u00e9nt\\u00efc\\u00e4t\\u00ef\\u00f6n" in json_output)
print("Contains raw unicode:", test_string in json_output)