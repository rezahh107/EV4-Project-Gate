from __future__ import annotations

import os


def pytest_report_teststatus(report, config):
    """Keep CI logs focused on failures without changing test execution.

    The full suite still runs with ``pytest -vv``. On GitHub Actions, successful
    test-status lines are suppressed so connector-visible logs retain the
    failure traceback and summary instead of thousands of pass-only lines.
    """
    if os.environ.get("GITHUB_ACTIONS") == "true" and report.passed:
        return "", "", ""
    return None
