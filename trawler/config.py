# SPDX-License-Identifier: BSD-3-Clause
import os
import enum
from enum import Enum

@enum.unique
class WebdriverBackend(Enum):
	Chrome  = enum.auto()
	FireFox = enum.auto()

	def __str__(self) -> str:
		return self.name

	@staticmethod
	def from_string(s: str):
		try:
			return WebdriverBackend[s]
		except KeyError:
			raise ValueError()

# ==== Various constants ==== #
TRAWLER_NAME = 'trawler'
TRAWLER_VERSION = 'v0.2'
TRAWLER_SCHEMA_VERSION = 1

# ==== Directories ==== #
XDG_CACHE_DIR = os.path.join(os.path.expanduser('~'), '.cache') if 'XDG_CACHE_HOME' not in os.environ else os.environ['XDG_CACHE_HOME']
XDG_DATA_HOME = os.path.join(os.path.expanduser('~'), '.local/share') if 'XDG_DATA_HOME' not in os.environ else os.environ['XDG_DATA_HOME']
XDG_DOCUMENTS_DIR = os.path.join(os.path.expanduser('~'), 'Documents') if 'XDG_DOCUMENTS_DIR' not in os.environ else os.environ['XDG_DOCUMENTS_DIR']

TRAWLER_DATA = os.path.join(XDG_DATA_HOME, TRAWLER_NAME)
TRAWLER_CACHE = os.path.join(XDG_CACHE_DIR, TRAWLER_NAME)

TRAWLER_USER_ADAPTERS = os.path.join(TRAWLER_DATA, 'adapters')
TRAWLER_DL_DIR = os.path.join(XDG_DOCUMENTS_DIR, TRAWLER_NAME)

# ==== Default Settings ==== #
DEFAULT_OUTPUT_DIR = TRAWLER_DL_DIR
DEFAULT_TIMEOUT = 120
DEFAULT_RETRY_COUNT = 3
DEFAULT_DOWNLOAD_DELAY = 3
DEFAULT_PROFILE_DIRECTORY = os.path.join(TRAWLER_CACHE, '.webdriver_profile')
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.9999.9999 Safari/537.36'

DEFAULT_DATABASE = os.path.join(TRAWLER_CACHE, 'datasheets.db')
DEFAULT_WEBDRIVER = WebdriverBackend.Chrome
DEFAULT_WD_HEADLESS = False
DEFAULT_WD_HEADLESS_RES = (1920, 1080)

# ==== Zotero Stuff ==== #
ZOTERO_ROOT = os.path.join(os.path.expanduser('~'), 'Zotero')
ZOTERO_DB = os.path.join(ZOTERO_ROOT, 'zotero.sqlite')

# ==== Database Settings ==== #
DATABASE = {
	'default': 'trawler_cache',
	'trawler_cache': {
		'driver': 'sqlite',
		'database': DEFAULT_DATABASE,
	},
	'zotero': {
		'driver': 'sqlite',
		'database': ZOTERO_DB,
	}
}
