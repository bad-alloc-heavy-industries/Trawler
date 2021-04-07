# SPDX-License-Identifier: BSD-3-Clause
"""
arm.py
---------

This script is designed to scrape all of the datasheets from https://developer.arm.com/documentation

"""
import sys
import time
import enum

from enum import Enum, Flag
from os import getcwd, path, mkdir
from datetime import datetime, timedelta

import requests
from requests import utils

from tqdm import tqdm
from selenium import webdriver

from ..common import *
from ..net import download_resource
from ..db import Datasheet, DatasheetTag, Scraper

@enum.unique
class DocumentType(Enum):
	ReferenceManual          = enum.auto()
	Architecture             = enum.auto()
	Guide                    = enum.auto()
	ApplicationNote          = enum.auto()
	KnowledgeBaseArticle     = enum.auto()
	ReleaseNote              = enum.auto()
	SoftwareErrata           = enum.auto()

	def __str__(self) -> str:
		return self.name

	@staticmethod
	def from_string(s):
		try:
			return DocumentType[s]
		except KeyError:
			raise ValueError()

	def filter_name(self):
		if self.value == DocumentType.ReferenceManual.value:
			return 'Technical%20Reference%20Manual'
		if self.value == DocumentType.Architecture.value:
			return 'Architecture%20Document'
		if self.value == DocumentType.Guide.value:
			return 'Guide'
		if self.value == DocumentType.ApplicationNote.value:
			return 'Application%20Note'
		if self.value == DocumentType.KnowledgeBaseArticle.value:
			return 'Knowledge%20Base%20Article'
		if self.value == DocumentType.ReleaseNote.value:
			return 'Release%20Note'
		if self.value == DocumentType.SoftwareErrata.value:
			return 'Software%20Developer%20Errata%20Notice'


ADAPTER_NAME = 'arm'
ADAPTER_DESC = 'arm datasheet adapter'

ARM_DOCS_ROOT_URL = 'https://developer.arm.com/documentation'


def extract_datasheet(driver, ds):
	tlog(f'  => Extracting datasheet {ds.id} from {ds.src}')
	driver.get(ds.src)
	time.sleep(3.5)
	try:
		driver.find_element_by_xpath('/html/body/div/div/div[2]/main/div/div[1]/div/div/div[1]/div/button').click()
		dl_loc = driver.find_element_by_xpath('/html/body/div/div/div[2]/main/div/div[1]/div/div/div[1]/div[2]/a')
	except Exception as e:
		if isinstance(e, KeyboardInterrupt):
			sys.quit()
		else:
			terr(f'  => Error: Unable to extract datasheet with id {ds.id}')
			return False

	ds.url = dl_loc.get_attribute('href')
	ds.save()
	return True



def collect_datasheets(driver, doc_types):
	sc_id = Scraper.where('name', '=', ADAPTER_NAME).first_or_fail().id

	dt_string = ','.join(map(lambda dt: (DocumentType.from_string(dt)).filter_name(), doc_types))
	doc_url = f'sort=relevancy&f:@navigationhierarchiescontenttype=[{dt_string}]'
	has_next_page = True
	page_index = 0
	datasheets = 0
	start_time = datetime.now()

	log('Collecting datasheets... this might take a while')
	while has_next_page:
		inf(f'  => On page index {(page_index//10)+1}, total so far {datasheets}')
		# We need to wait because ajax and frames and just bad.
		driver.get(f'{ARM_DOCS_ROOT_URL}/#first={page_index}&{doc_url}')
		time.sleep(3)

		doc_list = driver.find_elements_by_xpath('//*[@id="search"]/div[2]/div[2]/div[10]/div/*')

		for doc in doc_list:
			card_link = doc.find_element_by_xpath('.//div[1]/div/div[2]/div[1]/div/div/a')
			try:
				tags_row = doc.find_element_by_css_selector('div.documentTagsContainer')
			except:
				tags_row = None

			title = card_link.get_attribute('title')
			url = card_link.get_attribute('href')

			try:
				ds = Datasheet \
					.where('title', '=', title) \
					.where('scraper_id', '=', sc_id) \
					.first_or_fail()

			except:
				ds = Datasheet()
				ds.scraper_id = sc_id
				ds.found = datetime.now()
				ds.src = url
				ds.title = title

			ds.last_seen = datetime.now()
			ds.save()

			if tags_row is not None:
				tags = tags_row.find_elements_by_xpath('.//span')
				for tag in tags:
					for t in tag.text.split(' '):
						if t != '':
							try:
								te = DatasheetTag \
									.where('scraper_id', '=', sc_id) \
									.where('name', '=', t) \
									.first_or_fail()
							except:
								te = DatasheetTag()
								te.scraper_id = sc_id
								te.name = t
								te.save()

							ds.add_tag(te)

			ds.save()

			datasheets += 1

		try:
			driver.find_element_by_xpath('//*[@id="search"]/div[2]/div[2]/div[11]/ul/li[6]')
			page_index += 10
		except:
			has_next_page = False

	end_time = datetime.now()

	log(f'Found {datasheets} datasheets in {end_time - start_time}')


def parser_init(parser):
	arm_options = parser.add_argument_group('arm adapter options')

	arm_options.add_argument(
		'--arm-document-type', '-A',
		dest = 'arm_doc_type',
		type = DocumentType.from_string,
		choices = list(DocumentType),
		default = [ 'ReferenceManual', 'Architecture' ],
		help = 'ARM Documentation types to download'
	)

def adapter_main(args, driver, driver_options, dl_dir):
	sc_id = Scraper.where('name', '=', ADAPTER_NAME).first_or_fail().id
	if not args.skip_collect or not args.skip_extract:
		with driver(options = driver_options) as wd:
			if not args.skip_collect:
				collect_datasheets(wd, args.arm_doc_type)

			if not args.skip_extract:
				sheets = Datasheet.where('src', '!=', 'NULL').where('scraper_id', '=', sc_id).get()
				with tqdm(
						miniters = 1, total = len(sheets),
					) as bar:
						for ds in sheets:
							bar.set_description(fixup_title(ds.title))
							if extract_datasheet(wd, ds):
								bar.update(1)

	if not args.skip_download:
		sheets = Datasheet.where('url', '!=', 'NULL').where('scraper_id', '=', sc_id).get()
		with tqdm(
				miniters = 1, total = len(sheets),
			) as bar:
				for ds in sheets:
					bar.set_description(fixup_title(ds.title))
					if download_resource(dl_dir, ds, args):
						bar.update(1)


	return 0
