"""Runtime compatibility helpers for the backend application."""
from __future__ import annotations

import sys
import typing


def _patch_forward_ref_evaluate() -> None:
    """Patch ``typing.ForwardRef._evaluate`` for Python 3.13 compatibility.

    Python 3.13 made ``recursive_guard`` a required keyword-only argument on
    :meth:`typing.ForwardRef._evaluate`.  Pydantic < 2 still calls the method
    using a positional argument which results in a ``TypeError`` when running
    under Python 3.13.  This patch restores backwards compatible behaviour by
    accepting the positional argument and forwarding it to the original
    implementation.
    """

    forward_ref = getattr(typing, "ForwardRef", None)
    if forward_ref is None:
        return

    original_evaluate = getattr(forward_ref, "_evaluate", None)
    if original_evaluate is None:
        return

    if sys.version_info < (3, 13):
        return

    # Avoid re-applying the patch if this module is imported multiple times.
    if getattr(original_evaluate, "__patched_for_py313__", False):
        return

    def _patched_evaluate(
        self: typing.ForwardRef,
        globalns,
        localns,
        *_type_params,
        recursive_guard=None,
    ):
        """Wrapper compatible with both the pre and post Python 3.13 signatures."""

        # Python 3.13 passes ``type_params`` as a positional argument.  Older
        # versions don't provide it, so we simply ignore the value when present
        # to preserve the behaviour of Pydantic's original patch.
        if recursive_guard is None:
            recursive_guard = set()

        return original_evaluate(
            self,
            globalns,
            localns,
            recursive_guard=recursive_guard,
        )

    _patched_evaluate.__patched_for_py313__ = True  # type: ignore[attr-defined]

    try:
        setattr(forward_ref, "_evaluate", _patched_evaluate)
    except (AttributeError, TypeError):  # pragma: no cover - defensive guard
        pass


_patch_forward_ref_evaluate()

__all__ = ()
