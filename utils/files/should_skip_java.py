import re


def should_skip_java(content: str) -> bool:
    """
    Determines if a Java/Kotlin/Scala file should be skipped for test generation.

    Returns True if the file contains only:
    - Package declarations and imports
    - Interface definitions
    - Annotation definitions
    - Data classes/records (immutable data carriers)
    - Constants
    - Object declarations (Scala/Kotlin)

    Returns False if the file contains:
    - Method implementations
    - Class implementations with logic
    - Any executable code beyond declarations
    """
    lines = content.split("\n")
    in_interface_or_class = False
    in_annotation = False

    for line in lines:
        line = line.strip()
        # Skip comments
        if line.startswith("//") or line.startswith("/*") or line.startswith("*"):
            continue
        # Skip empty lines
        if not line:
            continue
        # Skip package declaration
        if line.startswith("package "):
            continue
        # Skip imports
        if line.startswith("import "):
            continue

        # Handle annotation definitions
        if (
            line.startswith("@interface ") or line.startswith("public @interface ")
        ) and "{" in line:
            in_annotation = True
            continue
        if in_annotation:
            if "}" in line:
                in_annotation = False
            continue

        # Handle interface definitions (Java/Kotlin)
        if re.match(r"^(public\s+)?interface\s+\w+", line):
            if "{" in line:
                in_interface_or_class = True
            continue

        # Handle data class definitions (Kotlin)
        if re.match(r"^(data\s+)?class\s+\w+\(", line):
            in_interface_or_class = True
            continue

        # Handle case class definitions (Scala)
        if re.match(r"^case\s+class\s+\w+\(", line):
            in_interface_or_class = True
            continue

        # Handle record definitions (Java 14+)
        if re.match(r"^(public\s+)?record\s+\w+\(", line):
            # Records are immutable data carriers, no logic
            in_interface_or_class = True
            continue

        if in_interface_or_class:
            if "}" in line or (line.endswith(")") and not line.startswith("(")):
                in_interface_or_class = False
            continue

        # Skip module exports (Java 9+)
        if line.startswith("exports ") or line.startswith("opens "):
            continue
        # Skip constants (Java/Kotlin/Scala)
        if re.match(
            r"^(public\s+|private\s+|protected\s+)?(static\s+)?(final\s+)?(const\s+|val\s+)?[\w\<\>\[\],\s]+\s+[A-Z_][A-Z0-9_]*\s*=",
            line,
        ):
            continue
        # Skip object declarations (Scala/Kotlin)
        if line.startswith("object ") and "{" in line:
            continue
        if line == "}":
            continue
        # Skip annotations usage
        if line.startswith("@"):
            continue
        # If we find any other code, it's not export-only
        return False

    return True
