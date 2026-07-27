from __future__ import annotations

import sys

from .runners import pcvp_owner as _implementation

# Preserve the historical import path while locating all external process
# execution inside the repository's runner boundary. The runner owns the
# locked npm invocation and TemporaryDirectory lifecycle; this facade executes
# neither and exists only for import compatibility.
sys.modules[__name__] = _implementation
