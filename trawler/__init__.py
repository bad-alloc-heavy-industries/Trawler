# SPDX-License-Identifier: BSD-3-Clause

__all__ = ('main')

def _init_directories():
	from . import config

	from os import path, mkdir

	dirs = (
		# Core Directories
		config.TRAWLER_DATA,
		config.TRAWLER_CACHE,
		# Sub directories
		config.TRAWLER_USER_ADAPTERS,
	)

	for d in dirs:
		if not path.exists(d):
			mkdir(d)

def _populate_webdriver_opts(args):
	from .config import WebdriverBackend

	from selenium.webdriver import firefox
	from selenium.webdriver import chrome

	opts = None

	if args.webdriver == WebdriverBackend.Chrome:
		opts = firefox.options.Options()


	elif args.webdriver == WebdriverBackend.FireFox:
		opts = chrome.options.Options()

	return opts

def _collect_adapters():
	import pkgutil

	from . import db
	from . import adapters

	adpts = []
	# Load the built-in internal adapters
	for _, name, is_pkg in pkgutil.iter_modules(path = getattr(adapters, '__path__')):
		if not is_pkg:
			__import__(f'{getattr(adapters, "__name__")}.{name}')
			if not hasattr(getattr(adapters, name), 'DONT_LOAD'):
				adpts.append({
					'name': getattr(adapters, name).ADAPTER_NAME,
					'description': getattr(adapters, name).ADAPTER_DESC,
					'parser_init': getattr(adapters, name).parser_init,
					'main': getattr(adapters, name).adapter_main
				})
	# Load the adapters from the share
	# TODO: this

	return adpts


def main():
	from . import config
	from . import db
	from .common import log, err, wrn, inf, dbg

	import os
	from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

	from orator import DatabaseManager, Model
	from selenium import webdriver

	_init_directories()

	ADAPTERS = _collect_adapters()

	parser = ArgumentParser(formatter_class = ArgumentDefaultsHelpFormatter, description = f'Trawler datasheet scraper')

	scraper_options = parser.add_argument_group('Global scraper options')

	scraper_options.add_argument(
		'--output', '-o',
		type = str,
		default = config.DEFAULT_OUTPUT_DIR,
		help = 'Datasheet download root'
	)

	scraper_options.add_argument(
		'--timeout', '-t',
		type = int,
		default = config.DEFAULT_TIMEOUT,
		help = 'Entry timeout in seconds'
	)

	scraper_options.add_argument(
		'--retry', '-r',
		type = int,
		default = config.DEFAULT_RETRY_COUNT,
		help = 'Download retry count'
	)

	scraper_options.add_argument(
		'--delay', '-d',
		type = int,
		default = config.DEFAULT_DOWNLOAD_DELAY,
		help = 'Download delay in seconds'
	)

	scraper_options.add_argument(
		'--cache-database', '-c',
		type = str,
		default = config.DEFAULT_DATABASE,
		help = 'Cache database'
	)

	scraper_options.add_argument(
		'--skip-collect', '-C',
		default = False,
		action = 'store_true',
		help = 'Skip the datasheet collection stage'
	)

	scraper_options.add_argument(
		'--skip-extract', '-E',
		default = False,
		action = 'store_true',
		help = 'Skip the datasheet extraction stage'
	)

	scraper_options.add_argument(
		'--skip-download', '-D',
		default = False,
		action = 'store_true',
		help = 'Skip the datasheet extraction stage'
	)

	wd_options = parser.add_argument_group('Selenium WebDriver Settings')

	wd_options.add_argument(
		'--profile-directory', '-p',
		type = str,
		default = config.DEFAULT_PROFILE_DIRECTORY,
		help = 'Selenium WebDriver profile directory'
	)

	wd_options.add_argument(
		'--webdriver', '-w',
		type = config.WebdriverBackend.from_string,
		choices = list(config.WebdriverBackend),
		default = config.DEFAULT_WEBDRIVER,
		help = 'Selenium WebDriver to use'
	)

	wd_options.add_argument(
		'--headless', '-H',
		default = config.DEFAULT_WD_HEADLESS,
		action = 'store_true',
		help = 'Run the Selenium WebDriver heedlessly'
	)

	wd_options.add_argument(
		'--headless-height', '-Y',
		type = str,
		default = config.DEFAULT_WD_HEADLESS_RES[0],
		help = 'Specify the hight of the headless window'
	)

	wd_options.add_argument(
		'--headless-width', '-X',
		type = str,
		default = config.DEFAULT_WD_HEADLESS_RES[1],
		help = 'Specify the width of the headless window'
	)

	# Maybe one day
	# wd_options.add_argument(
	# 	'--proxy', '-P',
	# 	type = str,
	# 	default = None,
	# 	help = 'Proxy to use for the Selenium WebDriver',
	# )

	adapter_parser = parser.add_subparsers(
			dest = 'adapter',
			required = True
		)

	# Add the adapter settings
	for adpt in ADAPTERS:
		ap = adapter_parser.add_parser(
				adpt['name'],
				help = adpt['description']
			)
		adpt['parser_init'](ap)

	# Actually parse the arguments
	args = parser.parse_args()

	# Initialize the download directory if not done so
	if not os.path.exists(args.output):
		wrn(f'Output directory {args.output} does not exist, creating')
		os.mkdirs(args.output)

	# Initialize the Database
	dbc = config.DATABASE
	dbc['sqlite']['database'] = args.cache_database

	dbm = DatabaseManager(config.DATABASE)
	Model.set_connection_resolver(dbm)

	if not os.path.exists(args.cache_database):
		common.wrn('Cache database does not exists, creating')
		db.run_migrations(dbm)
	inf(f'Cache database located at {args.cache_database}')

	# Initialize the datasheet directory
	if not os.path.exists(args.output):
		log(f'Datasheet download directory {args.output} does not exist, creating')
		os.mkdir(args.output)

	# Initialize the profile directory
	if not os.path.exists(args.profile_directory):
		log(f'WebDriver profile \'{args.profile_directory}\' does not exist, creating')
		os.mkdir(args.profile_directory)

	# WebDriver Initialization
	inf(f'Using the {args.webdriver} WebDriver')
	if args.webdriver == config.WebdriverBackend.Chrome:
		wd_opts = webdriver.chrome.options.Options()
		wd = webdriver.Chrome
		if args.headless:
			wd_opts.add_argument('--headless')
			wd_opts.add_argument(f'--window-size={args.headless_width},{args.headless_height}')
	elif args.webdriver == config.WebdriverBackend.FireFox:
		wd = webdriver.Firefox
		wd_opts = webdriver.firefox.options.Options()

	else:
		err('Unknown WebDriver, what?')
		return 1

	# Ensure the database is properly populated w/ known adapters
	for adapter in ADAPTERS:
		try:
			db.Scraper.where('name', '=', adapter['name']).first_or_fail()
		except:
			s = db.Scraper()
			s.name = adapter['name']
			s.save()

	# Get the adapter we need to run
	if args.adapter not in map(lambda a: a['name'], ADAPTERS):
		err(f'Unknown adapter {args.adapter}')
		err(f'Known adapters: {", ".join(map(lambda a: a["name"], ADAPTERS))}')
		return 1
	else:
		adpt = list(filter(lambda a: a['name'] == args.adapter, ADAPTERS))[0]

	# Initialize the adapter download directory
	dl_dir = os.path.join(args.output, adpt['name'])
	if not os.path.exists(dl_dir):
		wrn(f'Adapter datasheet directory {dl_dir} does not exist, creating...')
		os.mkdir(dl_dir)

	# Actually run the adapter
	return adpt['main'](args, wd, wd_opts, dl_dir)
