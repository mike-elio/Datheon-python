"""Run with: python main.py invoice examples/invoice.txt"""

import sys

from analyzer.cli import main

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
