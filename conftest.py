"""Make the worktree's own source the one under test.

An editable install points `tituli` at the main checkout, so without this a
worktree's tests silently exercise the wrong tree.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
