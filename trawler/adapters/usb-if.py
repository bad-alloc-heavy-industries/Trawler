# SPDX-License-Identifier: BSD-3-Clause
"""
usb-if.py
---------

This script is designed to scrape all of the datasheets from https://www.usb.org/documents

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

ADAPTER_NAME = 'usb-if'
ADAPTER_DESC = 'USB-IF datasheet adapter'

USB_DOCS_ROOT_URL = 'https://www.usb.org/documents'
USB_DOCS_ALL = f'{USB_DOCS_ROOT_URL}?search=&items_per_page=All'


def collect_datasheets(args, dl_dir):
	sc_id = Scraper.where('name', '=', ADAPTER_NAME).first_or_fail().id
	log('Collecting datasheets... this might take a while')
	datasheets = 0
	start_time = datetime.now()

	content = get_content(USB_DOCS_ALL, args)
	soup = BeautifulSoup(content, 'lxml')

	# We assume that there is only one table on this page, I know I know
	doc_tab = soup.find('table').find('tbody')
	for doc in tqdm(doc_tab.find_all('tr')):
		tds = doc.find_all('td')
		try:
			file = tds[0].find('span').find_all('span')[2].find('a')['href']
		except Exception as e:
			if isinstance(e, KeyboardInterrupt):
				sys.quit()
			else:
				continue

		title = tds[0].find_all('a')[1].text

		try:
			ds = Datasheet \
				.where('title', '=', title) \
				.where('scraper_id', '=', sc_id) \
				.first_or_fail()
		except:
			ds = Datasheet()
			ds.scraper_id = sc_id
			ds.found = datetime.now()
			ds.src = file
			ds.url = file
			ds.dl_location = dl_dir
			ds.title = title

		ds.last_seen = datetime.now()
		ds.save()
		datasheets += 1

		# Try to pull out the "tags"
		t_tags = list(map(lambda t: t.strip(), tds[4].text.split(','))) + [
			tds[1].text.strip() if tds[1] is not None else '',
			tds[2].text.strip() if tds[2] is not None else ''
		]

		for tag in t_tags:
			if tag != '':
				try:
					te = DatasheetTag \
						.where('scraper_id', '=', sc_id) \
						.where('name', '=', tag) \
						.first_or_fail()
				except:
					te = DatasheetTag()
					te.scraper_id = sc_id
					te.name = tag
					te.save()

				ds.add_tag(te)

	end_time = datetime.now()
	log(f'Found {datasheets} datasheets in {end_time - start_time}')

def parser_init(parser):
	usbif_options = parser.add_argument_group('USB-IF adapter options')


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
