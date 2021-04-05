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
# TODO: Make use of these settings
DEFAULT_TIMEOUT = 120
DEFAULT_RETRY_COUNT = 3
DEFAULT_DOWNLOAD_DELAY = 3
DEFAULT_PROFILE_DIRECTORY = os.path.join(TRAWLER_CACHE, '.webdriver_profile')
# END TODO

DEFAULT_DATABASE = os.path.join(TRAWLER_CACHE, 'datasheets.db')
DEFAULT_WEBDRIVER = WebdriverBackend.Chrome
DEFAULT_WD_HEADLESS = False

# ==== Database Settings ==== #
DATABASE = {
	'sqlite': {
		'driver': 'sqlite',
		'database': DEFAULT_DATABASE,
	}
}
