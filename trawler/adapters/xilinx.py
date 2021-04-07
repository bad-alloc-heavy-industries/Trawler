#!/usr/bin/env python
# SPDX-License-Identifier: BSD-3-Clause
"""
xilinx.py
---------

This script is designed to scrape all of the datasheets from xilinx.com

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
from selenium import webdriver

from ..common import *
from ..db import Datasheet, DatasheetTag, Scraper

from bs4 import BeautifulSoup

ADAPTER_NAME = 'xilinx'
ADAPTER_DESC = 'Xilinx datasheet adapter'

XILINX_DOCNAV_ROOT = 'https://xilinx.com/support/documentation/navigator'
XILINX_HUBS_INDEX = f'{XILINX_DOCNAV_ROOT}/xhubs.xml'
XILINX_DOCS_INDEX = f'{XILINX_DOCNAV_ROOT}/xdocs.xml'

def docnav_collect_docs():
	log(f'Downloading doc index from {XILINX_DOCS_INDEX}')
	catalogs = []
	with requests.get(XILINX_DOCS_INDEX) as r:
		soup = BeautifulSoup(r.content, "xml")
		for catalog in soup.find_all('catalog'):
			# ニャ！
			cat = {
				'catalog': catalog['label'],
				'product': catalog['productName'],
				'collection': catalog['collection'],
				'groups': []
			}

			inf(f'  => Found catalog {cat["catalog"]}')
			for group in catalog.find_all('group'):
				grp = {
					'title': group['label'],
					'docs': []
				}

				inf(f'      => Found group {grp["title"]}')
				for doc in group.find_all('document'):
					title = doc.find('title')
					loc = doc.find('webLocation')
					doc_id = doc.find('docID')
					doc_type = doc.find('docType')
					desc = doc.find('tooltip')
					tags = doc.find('functionTags')

					grp['docs'].append({
						'title': title.get_text() if title is not None else '',
						'location': loc.get_text() if loc is not None  else '',
						'doc_id': doc_id.get_text()  if doc_id is not None else '',
						'type': doc_type.get_text() if doc_type is not None  else '',
						'desc': desc.get_text() if desc is not None else '',
						'tags': tags.get_text().split(',') if tags is not None else [],
					})

				cat['groups'].append(grp)
			catalogs.append(cat)

	return catalogs

def docnav_populate(args, docs, dl_dir):
	inf('Populating datasheet database')
	sc_id = Scraper.where('name', '=', ADAPTER_NAME).first_or_fail().id
	for cat in docs:
		inf(f'  => Populating from catalog {cat["catalog"]}')
		try:
			cat_tag = DatasheetTag \
					.where('scraper_id', '=', sc_id) \
					.where('name', '=', cat['catalog']) \
					.first_or_fail()
		except:
			cat_tag = DatasheetTag()
			cat_tag.scraper_id = sc_id
			cat_tag.name = cat['catalog']
			cat_tag.save()

		for grp in cat['groups']:
			inf(f'      => Populating {len(grp["docs"])} docs from group {cat["catalog"]}/{grp["title"]}')
			try:
				grp_tag = DatasheetTag \
						.where('scraper_id', '=', sc_id) \
						.where('name', '=', grp['title']) \
						.first_or_fail()
			except:
				grp_tag = DatasheetTag()
				grp_tag.scraper_id = sc_id
				grp_tag.name = grp['title']
				grp_tag.save()

			for doc in grp['docs']:
				try:
					ds = Datasheet \
						.where('title', '=', doc['title']) \
						.where('scraper_id', '=', sc_id) \
						.first_or_fail()

				except:
					ds = Datasheet()
					ds.scraper_id = sc_id
					ds.found = datetime.now()
					ds.src = doc['location']
					ds.url = doc['location']
					ds.title = doc['title']

				if not args.xilinx_doc_group:
					c_dir = path.join(dl_dir, cat['catalog'].replace('/', '_'))
					g_dir = path.join(c_dir, grp['title'].replace('/', '_'))
					if not path.exists(c_dir):
						log(f'  => Catalog {cat["catalog"]} does not exist, creating')
						mkdir(c_dir)

					if not path.exists(g_dir):
						log(f'  => Group {cat["catalog"]}/{grp["title"]} does not exist, creating')
						mkdir(g_dir)

					ds.dl_location = g_dir
				ds.save()

				ds.add_tag(cat_tag)
				ds.add_tag(grp_tag)
				for tag in doc['tags']:
					try:
						ds_tag = DatasheetTag \
								.where('scraper_id', '=', sc_id) \
								.where('name', '=', tag) \
								.first_or_fail()
					except:
						ds_tag = DatasheetTag()
						ds_tag.scraper_id = sc_id
						ds_tag.name = tag
						ds_tag.save()

					ds.add_tag(ds_tag)
				ds.save()

def docnav_runner(args, dl_dir):
	inf('Downloading datasheets from DocNav')
	sc = Scraper.where('name', '=', ADAPTER_NAME).first_or_fail()

	if not args.skip_collect:
		docs = docnav_collect_docs()
		if docs is None:
			err('Unable to collect Xilinx hubs')
			return 1

		# Populate the datasheet database
		docnav_populate(args, docs, dl_dir)

	# Now we have all the datasheets, we can download them
	if not args.skip_download:
		sheets = Datasheet.where('url', '!=', 'NULL').where('scraper_id', '=', sc.id).get()
		with tqdm(
				miniters = 1, total = len(sheets),
			) as bar:
				for ds in sheets:
					bar.set_description(fixup_title(ds.title))
					if ds.url[-4:] == 'html' and args.xilinx_get_web_only:
						if download_resource(dl_dir, ds, timeout = args.timeout, retry = args.retry, delay = args.delay):
							bar.update(1)
					else:
						if download_resource(dl_dir, ds, timeout = args.timeout, retry = args.retry, delay = args.delay):
							bar.update(1)

	sc.last_run = datetime.now()
	sc.save()

	return 0


def parser_init(parser):
	xilinx_options = parser.add_argument_group('Xilinx adapter options')

	xilinx_options.add_argument(
		'--dont-group', '-G',
		dest = 'xilinx_doc_group',
		default = False,
		action = 'store_true',
		help = 'Don\'t group the datasheets when using DocNav as the document source'
	)

	xilinx_options.add_argument(
		'--collect-web-only', '-W',
		dest = 'xilinx_get_web_only',
		default = False,
		action = 'store_true',
		help = 'Also archive the web-only content and monolithic HTML pages',
	)

def adapter_main(args, driver, dl_dir):
	return docnav_runner(args, dl_dir)
