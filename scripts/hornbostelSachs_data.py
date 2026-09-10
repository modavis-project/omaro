#!/usr/bin/env python3
"""Deprecated compatibility entry point for a complete MIMO data refresh."""

from __future__ import annotations

import warnings

from omaro.cli import main


if __name__ == "__main__":
    warnings.warn(
        "hornbostelSachs_data.py is deprecated; use "
        "`omaro refresh-source` followed by `build`.",
        DeprecationWarning,
        stacklevel=1,
    )
    main(["refresh-source"])
    raise SystemExit(main(["build"]))
