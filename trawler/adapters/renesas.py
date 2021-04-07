# SPDX-License-Identifier: BSD-3-Clause
"""
renesas.py
---------

This script is designed to scrape all of the datasheets from https://www.renesas.com/us/en/support/document-search

"""
import sys
import time
import enum
import re

from enum import Enum, Flag
from os import getcwd, path, mkdir
from datetime import datetime, timedelta

import requests
from requests import utils

from tqdm import tqdm

from ..common import *
from ..net import download_resource, get_content
from ..db import Datasheet, DatasheetTag, Scraper

from bs4 import BeautifulSoup

ADAPTER_NAME = 'renesas'
ADAPTER_DESC = 'Renesas datasheet adapter'

RENESAS_ROOT = 'https://www.renesas.com'
RENESAS_DOCS_ROOT = f'{RENESAS_ROOT}/us/en/support/document-search'

def collect_datasheets(args, dl_dir):
	sc_id = Scraper.where('name', '=', ADAPTER_NAME).first_or_fail().id
	log('Collecting datasheets... this might take a while')

	page_index = 0
	has_next_page = True
	datasheets = 0
	start_time = datetime.now()

	while has_next_page:
		inf(f'  => On page index {page_index+1}, total so far {datasheets}')
		url = f'{RENESAS_DOCS_ROOT}?page={page_index}'

		content = get_content(url, args)
		soup = BeautifulSoup(content, 'lxml')
		try:
			doc_tab = soup.find('table').find('tbody')
		except Exception as e:
			if isinstance(e, KeyboardInterrupt):
				sys.quit()
			else:
				has_next_page = False
				break

		for doc in tqdm(doc_tab.find_all('tr')):
			tds = doc.find_all('td')
			is_locked = tds[0].find('span') is not None
			url = tds[1].find_all('a')[1]['href']
			title = tds[1].find_all('a')[1].text

			if not is_locked:
				try:
					ds = Datasheet \
						.where('title', '=', title) \
						.where('scraper_id', '=', sc_id) \
						.first_or_fail()
				except:
					ds = Datasheet()
					ds.scraper_id = sc_id
					ds.found = datetime.now()
					ds.src = f'{RENESAS_ROOT}/{url}'
					ds.url = f'{RENESAS_ROOT}/{url}'
					ds.dl_location = dl_dir
					ds.title = title

				ds.last_seen = datetime.now()
				ds.save()
				datasheets += 1

		page_index += 1

	end_time = datetime.now()

	log(f'Found {datasheets} datasheets in {end_time - start_time}')


def parser_init(parser):
	renesas_options = parser.add_argument_group('Renesas adapter options')

def adapter_main(args, driver, driver_options, dl_dir):
	sc_id = Scraper.where('name', '=', ADAPTER_NAME).first_or_fail().id

	if not args.skip_collect:
		collect_datasheets(args, dl_dir)

	if not args.skip_download:
		sheets = Datasheet.where('src', '!=', 'NULL').where('scraper_id', '=', sc_id).get()
		with tqdm(
				miniters = 1, total = len(sheets),
			) as bar:
				for ds in sheets:
					bar.set_description(fixup_title(ds.title))
					if download_resource(dl_dir, ds, args):
						bar.update(1)

	return 0
