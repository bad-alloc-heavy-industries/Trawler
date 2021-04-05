#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause

import sys
from pathlib import Path

trawler_path = Path(sys.argv[0]).resolve()

if (trawler_path.parent / 'trawler').is_dir():
	sys.path.insert(0, str(trawler_path.parent))

from trawler import main

if __name__ == '__main__':
	sys.exit(main())
