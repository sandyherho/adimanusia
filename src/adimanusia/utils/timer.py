"""Timing utilities."""

import time
from contextlib import contextmanager
from typing import Dict


class Timer:
    """Simple timer for profiling."""
    
    def __init__(self):
        self.times: Dict[str, float] = {}
        self._starts: Dict[str, float] = {}
    
    def start(self, name: str):
        """Start timing a section."""
        self._starts[name] = time.time()
    
    def stop(self, name: str):
        """Stop timing a section."""
        if name in self._starts:
            self.times[name] = time.time() - self._starts[name]
            del self._starts[name]
    
    @contextmanager
    def time_section(self, name: str):
        """Context manager for timing."""
        self.start(name)
        try:
            yield
        finally:
            self.stop(name)
    
    def get_times(self) -> Dict[str, float]:
        """Get all recorded times."""
        return self.times.copy()
