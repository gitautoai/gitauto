from utils.files.is_dependency_file import DEPENDENCY_DIRS

GREP_EXCLUDE_DIRS = [
    # IDE / framework caches
    "--exclude-dir=.angular",
    "--exclude-dir=.cache",
    "--exclude-dir=.git",
    "--exclude-dir=.gradle",
    "--exclude-dir=.mypy_cache",
    "--exclude-dir=.next",
    "--exclude-dir=.nuxt",
    "--exclude-dir=.parcel-cache",
    "--exclude-dir=.phpunit.cache",
    "--exclude-dir=.pytest_cache",
    "--exclude-dir=.svelte-kit",
    "--exclude-dir=.tox",
    "--exclude-dir=.turbo",
    "--exclude-dir=.yarn",
    "--exclude-dir=__pycache__",
    # Build outputs
    "--exclude-dir=bin",
    "--exclude-dir=build",
    "--exclude-dir=coverage",
    "--exclude-dir=dist",
    "--exclude-dir=obj",
    "--exclude-dir=out",
    "--exclude-dir=target",
    # Third-party dependencies
    *[f"--exclude-dir={d}" for d in DEPENDENCY_DIRS],
]
