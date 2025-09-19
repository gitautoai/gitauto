# Quick test of the logic
test_lines = ['platform linux', 'collected items', 'test results', 'After content']
for line in test_lines:
    stripped_line = line.strip()
    looks_like_regular_content = (
        not any(keyword in stripped_line.lower() for keyword in [
            'platform', 'cachedir', 'rootdir', 'plugins', 'asyncio', 'collecting', 'collected',
            'test', 'pytest', 'passed', 'failed', 'skipped', 'error', 'warning', 'coverage'
        ]) and
        '::' not in stripped_line and
        '%]' not in stripped_line and
        len(stripped_line.split()) <= 4 and
        not stripped_line.startswith(('  ', '\t'))
    )
    print(f"'{line}' -> looks_like_regular_content: {looks_like_regular_content}")
\ No newline at end of file
