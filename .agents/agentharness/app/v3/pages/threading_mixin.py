"""Shared background-thread helper for all page mixins."""
import threading as _t
from typing import Callable, Any, Optional


class ThreadingMixin:
    def _bg(self, fn: Callable, on_success: Optional[Callable] = None, on_error: Optional[Callable] = None):
        """Run fn() in a daemon thread; on_success(result) and on_error(exc) are called via _ui_queue."""
        def _run():
            try:
                result = fn()
                if on_success:
                    self._ui_queue.put(("call_with_arg", on_success, result))
            except Exception as e:
                if on_error:
                    self._ui_queue.put(("call_with_arg", on_error, e))
                else:
                    self._ui_queue.put(("toast", f"Error: {e}", "error"))
        _t.Thread(target=_run, daemon=True).start()
