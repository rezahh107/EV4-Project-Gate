from __future__ import annotations

import os


def pytest_configure(config):
    """Keep GitHub Actions diagnostics concise without changing execution."""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        config.option.verbose = -1
        config.option.tbstyle = "line"
        config.option.disable_warnings = True
