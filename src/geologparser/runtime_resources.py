"""Cross-platform process resource reporting used by experiment runners."""
from __future__ import annotations

import os


def peak_process_rss_kib() -> int | None:
    """Return peak resident memory in KiB when the platform exposes it."""
    try:
        import resource
    except ImportError:
        resource = None
    if resource is not None:
        value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        # macOS reports bytes; Linux and the BSD CI images report KiB.
        return value // 1024 if os.sys.platform == "darwin" else value
    try:
        import psutil
    except ImportError:
        return None
    return int(psutil.Process().memory_info().rss // 1024)
