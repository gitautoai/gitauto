from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def find_common_prefix(lcov_content: str, repo_files: set[str]):
    for line in lcov_content.splitlines():
        line = line.strip()
        if not line.startswith("SF:"):
            continue

        sf_path = line[3:]
        # On Linux (all CI environments), absolute paths start with "/".
        # Absolute paths have a prefix (e.g. /home/kf/app/) that needs stripping
        # to match repo_files which are relative paths from GitHub API.
        if not sf_path.startswith("/"):
            continue

        parts = sf_path.split("/")
        # Try stripping progressively more leading components until we find a match
        # /home/kf/app/php/file.php -> home/kf/app/php/file.php -> kf/app/php/file.php -> ...
        for i in range(1, len(parts)):
            candidate = "/".join(parts[i:])
            if candidate in repo_files:
                prefix = "/".join(parts[:i])
                return prefix + "/"

    return ""
