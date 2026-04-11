import os

# Fallback Node.js version when a repo doesn't declare one (.nvmrc, .node-version, engines).
# Read from Dockerfile ENV FALLBACK_NODE_VERSION; falls back to "22" for local dev.
FALLBACK_NODE_VERSION = os.environ.get("FALLBACK_NODE_VERSION", "22")
