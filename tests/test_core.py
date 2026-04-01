"""
Integration test for autoloop core loop.
Uses a mock agent backend — no Claude/Codex required.
Tests: loop runs, improvements kept, regressions discarded, broken code penalized.

Run: python3 tests/test_core.py
"""

import sys
import os
import tempfile
import subprocess
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from autoloop.core import AutoLoop
from autoloop.backends import BaseBackend

IMPROVEMENTS = [
    ("""
def fibonacci(n, _cache={}):
    if n in _cache:
        return _cache[n]
    if n <= 1:
        return n
    _cache[n] = fibonacci(n - 1) + fibonacci(n - 2)
    return _cache[n]

result = fibonacci(30)
""", "Add memoization with dict cache"),

    ("""
def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

result = fibonacci(30)
""", "Switch to iterative approach"),

    ("""
def fibonacci(n):
    return 999  # wrong answer
result = fibonacci(30)
""", "Wrong shortcut — should be discarded"),

    ("""
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

result = fibonacci(30)
""", "Use functools.lru_cache decorator"),
]


class MockBackend(BaseBackend):
    def __init__(self):
        self._idx = 0

    def propose_and_apply(self, target, directives, history, experiment_id):
        if self._idx >= len(IMPROVEMENTS):
            return "no change"
        code, description = IMPROVEMENTS[self._idx]
        self._idx += 1
        Path(target).write_text(code.strip())
        return description


def timing_metric(target_path: str) -> float:
    times = []
    for _ in range(3):
        start = time.perf_counter()
        result = subprocess.run(
            ['python3', '-c', f"""
exec(open("{target_path}").read())
assert fibonacci(10) == 55, f"Wrong: {{fibonacci(10)}}"
assert fibonacci(0) == 0
assert fibonacci(1) == 1
"""],
            capture_output=True, text=True, timeout=10
        )
        elapsed = time.perf_counter() - start
        if result.returncode != 0:
            return -999.0
        times.append(elapsed)
    return -min(times)


def test_core_loop():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = os.path.join(tmpdir, "fibonacci.py")
        Path(target).write_text("""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
result = fibonacci(30)
""".strip())

        loop = AutoLoop(
            target=target,
            metric=timing_metric,
            directives="program.md",
            backend=MockBackend(),
            results_dir=os.path.join(tmpdir, "results"),
            higher_is_better=True,
            verbose=True,
        )

        loop.run(experiments=4)

        assert len(loop.results) == 4
        kept = [r for r in loop.results if r.improved]
        discarded = [r for r in loop.results if not r.improved]
        assert len(kept) >= 1, "At least one improvement should be kept"
        broken = next((r for r in loop.results if r.score == -999.0), None)
        assert broken is not None and not broken.improved, "Broken code must be discarded"
        assert loop.best_score > -0.1717, f"Best score should beat baseline, got {loop.best_score}"

        print("\n✅ All assertions passed!")
        print(f"   Kept: {[r.description for r in kept]}")
        print(f"   Discarded: {[r.description for r in discarded]}")
        print(f"   Best score: {loop.best_score:.4f} (baseline was -0.1717)")


if __name__ == "__main__":
    test_core_loop()
