# SPDX-License-Identifier: BSD-3-Clause
#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
	name = 'Trawler',
	version = '0.1',
	description = 'Bulk scrape and download datasheets from various vendors (insult)',
	license = 'BSD-3-Clause',
	python_requires = '~=3.7',
	install_requires = [
		'requests',
		'tqdm',
		'selenium',
		'orator',
		'beautifulsoup4',
		'lxml'
	],
	packages = find_packages(),
	project_urls = {
		'Source Code': 'https://github.com/bad-alloc-heavy-industries/Trawler',
		'Bug Tracker': 'https://github.com/bad-alloc-heavy-industries/Trawler/issues'
	}
)
