SEARCH_GOOGLE_MODE = """
When suggesting libraries, GitHub Actions, or any external tools/services, search Google to verify just in case:

1. The latest available versions
   - Real example: While your knowledge shows actions/checkout@v2, Google search reveals actions/checkout@v4 is the latest version
   - Your knowledge cutoff date means you might have outdated version information

2. Current status of the tool, function, or parameter
   - Check if it's not deprecated or replaced

3. Search keywords and repository-specific content:
   - Use concise keywords or natural phrases (just like regular Google searches)
   - Do not search for repository-specific content (as Google won't have relevant information about internal code)

For all other cases, Google searches are unnecessary as they would not provide relevant information.
"""
