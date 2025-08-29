from services.coverages.coverage_types import CoverageReport


def detect_language_from_coverage(coverage_data: list[CoverageReport]):
    """Detect language from file extensions in coverage data"""
    extensions = []
    for item in coverage_data:
        if item["level"] == "file":
            ext = item["full_path"].split(".")[-1].lower()
            extensions.append(ext)

    if not extensions:
        return "unknown"

    # Count extensions
    ext_count = {}
    for ext in extensions:
        ext_count[ext] = ext_count.get(ext, 0) + 1

    # Map to language families
    ext_to_lang = {
        "js": "javascript",
        "jsx": "javascript",
        "ts": "javascript",
        "tsx": "javascript",
        "py": "python",
        "php": "php",
        "rb": "ruby",
        "go": "go",
        "java": "java",
        "c": "c",
        "cpp": "cpp",
        "cs": "csharp",
        "swift": "swift",
        "kt": "kotlin",
    }

    # Get most common extension
    most_common_ext = max(ext_count.items(), key=lambda x: x[1])[0]
    return ext_to_lang.get(most_common_ext, "unknown")
