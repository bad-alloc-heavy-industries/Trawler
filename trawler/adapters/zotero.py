# SPDX-License-Identifier: BSD-3-Clause
"""
zotero.py
---------

This is the zotero meta adapter

"""
import sys
import os

from shutil import copyfile
from tempfile import gettempdir
from datetime import datetime

from orator import Model, orm

from tqdm import tqdm

from .. import config
from ..common import *
from ..net import download_resource
from ..db import Datasheet, DatasheetTag, Scraper


META_ADAPTER = 0

ADAPTER_NAME = 'zotero'
ADAPTER_DESC = 'Trawler zotero meta adapter'

ZOTERO_BACKUP_DIR = gettempdir()
ZOTERO_TRAWLER_ROOT_COLLECTION = 'Trawler'

def gen_key(key_len = 8):
	from random import choice
	from string import ascii_uppercase, digits
	return ''.join(choice(ascii_uppercase + digits) for i in range(key_len))

# ==== Zotero DB Models ==== #

class ZCollectionItem(Model):
	__connection__ = 'zotero'
	__timestamps__ = False
	__table__ = 'collectionItems'
	__primary_key__ = 'collectionID'


class ZCollection(Model):
	__connection__ = 'zotero'
	__timestamps__ = False
	__table__ = 'collections'
	__primary_key__ = 'collectionID'

	@orm.belongs_to_many('collectionItems', 'collectionID', 'itemID')
	def items(self):
		return ZItem


class ZItemType(Model):
	__connection__ = 'zotero'
	__timestamps__ = False
	__table__ = 'itemTypes'
	__primary_key__ = 'itemTypeID'


	@orm.belongs_to_many('items', 'itemTypeID', 'itemID')
	def items(self):
		return ZItem

class ZTag(Model):
	__connection__ = 'zotero'
	__timestamps__ = False
	__table__ = 'tags'
	__primary_key__ = 'tagID'


	@orm.belongs_to_many('itemTags', 'tagID', 'itemID')
	def items(self):
		return ZItem

class ZItem(Model):
	__connection__ = 'zotero'
	__timestamps__ = False
	__table__ = 'items'
	__primary_key__ = 'itemID'

	@orm.belongs_to_many('itemTags', 'itemID', 'tagID')
	def tags(self):
		return ZTag

	def has_tag(self, tag):
		return self.tags().where('tagID', '=', tag.tagID).exists()

	def add_tag(self, tag):
		if not self.has_tag(tag):
			self.tags().attach(tag)

	def remove_tag(self, tag):
		if self.has_tag(tag):
			self.tags().detach(tag)

	@orm.belongs_to_many('itemData', 'itemID', 'valueID')
	def item_data(self):
		return ZItemDataValue

	def has_item_data(self):
		return self.item_data().where('itemID', '=', self.itemID)

	def add_item_data(self, item_data):
		self.item_data().attach(item_data)

	def remove_item_data(self, item_data):
		self.item_data().detach(item_data)

class ZItemTag(Model):
	__connection__ = 'zotero'
	__timestamps__ = False
	__table__ = 'itemTags'
	__primary_key__ = 'itemID'

class ZFieldFormat(Model):
	__connection__ = 'zotero'
	__timestamps__ = False
	__table__ = 'fieldFormats'
	__primary_key__ = 'fieldFormatID'

class ZField(Model):
	__connection__ = 'zotero'
	__timestamps__ = False
	__table__ = 'fields'
	__primary_key__ = 'fieldID'

class ZItemAttachment(Model):
	__connection__ = 'zotero'
	__timestamps__ = False
	__table__ = 'itemAttachments'
	__primary_key__ = 'itemID'

	@orm.belongs_to('itemID')
	def item(self):
		return ZItem

class ZItemData(Model):
	__connection__ = 'zotero'
	__timestamps__ = False
	__table__ = 'itemData'
	__primary_key__ = 'itemID'

class ZItemDataValue(Model):
	__connection__ = 'zotero'
	__timestamps__ = False
	__table__ = 'itemDataValues'
	__primary_key__ = 'valueID'

	@orm.belongs_to('valueID', 'valueID')
	def item_data(self):
		return ZItem

	def has_data(self):
		return self.item_data().where('valueID', '=', self.valueID).exists()


# ==== Adapter Methods ==== #

def sync_scraper(tcol, sc):
	log(f'  => Syncing datasheets from {sc.name}')
	date_added = datetime.now()
	# Try to check if the scraper collection already exists, or create it
	try:
		scol = ZCollection \
			.where('collectionName', '=', sc.name) \
			.where('parentCollectionID', '=', tcol.collectionID) \
			.first_or_fail()
	except:
		scol = ZCollection()
		scol.collectionName = sc.name
		scol.parentCollectionID = tcol.collectionID
		scol.libraryID = tcol.libraryID
		scol.key = gen_key()
		scol.save()

	for ds in tqdm(Datasheet.where('scraper_id', '=', sc.id).get(), desc = f'Zotero sync: {sc.name}'):
		tlog(f'  ==> Adding datasheet {ds.title}')

		try:
			name = ZItemDataValue.where('value', '=', ds.filename).first_or_fail()
		except:
			name = ZItemDataValue()
			name.value = ds.filename
			name.save()

		try:
			title = ZItemDataValue.where('value', '=', ds.title).first_or_fail()
		except:
			title = ZItemDataValue()
			title.value = ds.title
			title.save()

		try:
			url = ZItemDataValue.where('value', '=', ds.url).first_or_fail()
		except:
			url = ZItemDataValue()
			url.value = ds.url
			url.save()

		try:
			da = ZItemDataValue.where('value', '=', date_added).first_or_fail()
		except:
			da = ZItemDataValue()
			da.value = date_added
			da.save()

		# Check to see the the data values we just created are linked with an item
		if not ZItemData.where('valueID', '=', name.valueID).exists():
			# If not, then we can assume that the item doesn't exist, so we create one
			item = ZItem()
			item.itemTypeID = 12
			item.libraryID = scol.libraryID
			item.key = gen_key()
			item.save()

			i_title = ZItemData()
			i_title.itemID = item.itemID
			i_title.valueID = title.valueID
			i_title.fieldID = 1
			i_title.save()

			i_url = ZItemData()
			i_url.itemID = item.itemID
			i_url.valueID = url.valueID
			i_url.fieldID = 13
			i_url.save()

			i_da = ZItemData()
			i_da.itemID = item.itemID
			i_da.valueID = da.valueID
			i_da.fieldID = 6
			i_da.save()

			# Attach tags to item
			for tag in ds.tags().get():
				if tag.name != '':
					zt = ZTag.where('name', '=', tag.name).first_or_fail()

					zit = ZItemTag()
					zit.itemID = item.itemID
					zit.tagID = zt.tagID
					zit.type = 0
					zit.save()

			# Create the attachment item and then the attachment link
			aitm = ZItem()
			aitm.itemTypeID = 2
			aitm.libraryID = scol.libraryID
			aitm.key = gen_key()
			aitm.save()

			att_name = ZItemData()
			att_name.itemID = aitm.itemID
			att_name.valueID = name.valueID
			att_name.fieldID = 1
			att_name.save()

			att = ZItemAttachment()
			att.itemID = aitm.itemID
			att.parentItemID = item.itemID
			att.linkMode = 2
			att.path = ds.dl_location
			att.contentType = 'application/pdf'
			att.save()

			# Finally link it to the collection
			col = ZCollectionItem()
			col.collectionID = scol.collectionID
			col.itemID = item.itemID
			col.save()







def sync_database(args, dl_dir):
	inf('Syncing Zotero with Trawler cache')

	if args.zotero_sync_backup:
		backup_file = os.path.join(args.zotero_sync_backup_dir, 'zotero_backup.sqlite')

		log(f'  => Backing up Zotero db to {backup_file}')
		copyfile(args.zotero_db_loc, backup_file)

	# Get the Trawler Zotero collection, or create it otherwise
	try:
		tcol = ZCollection.where('collectionName', '=', ZOTERO_TRAWLER_ROOT_COLLECTION).first_or_fail()
	except:
		tcol = ZCollection()
		tcol.collectionName = ZOTERO_TRAWLER_ROOT_COLLECTION
		tcol.key = gen_key()
		tcol.libraryID = 1
		tcol.save()

	# Sync the tags
	log(f'  => Syncing Trawler tags to Zotero')
	for tag in tqdm(DatasheetTag.all(), desc = 'Zotero sync: tags'):
		if tag.name != '':
			try:
				zt = ZTag.where('name', '=', tag.name).first_or_fail()
			except:
				zt = ZTag()
				zt.name = tag.name
				zt.save()

	for sc in Scraper.all():
		if not sc.meta:
			sync_scraper(tcol, sc)

ZOTERO_ACTIONS = {
	'sync': sync_database
}

def parser_init(parser):
	zotero_options = parser.add_argument_group('zotero meta adapter options')

	zotero_options.add_argument(
		'--zotero-db-location',
		dest = 'zotero_db_loc',
		type = str,
		default = config.ZOTERO_DB,
		help = 'The location of the Zotero SQLite database'
	)

	zotero_actions = parser.add_subparsers(
		dest = 'zotero_action'
	)

	zsync = zotero_actions.add_parser('sync', help = 'Sync Zotero with Trawler')

	zsync.add_argument(
		'--backup',
		dest = 'zotero_sync_backup',
		default = False,
		action = 'store_true',
		help = 'Create a backup of the Zotero database before syncing'
	)

	zsync.add_argument(
		'--backup-dir',
		dest = 'zotero_sync_backup_dir',
		type = str,
		default = ZOTERO_BACKUP_DIR,
		help = 'Specify the location for the Zotero backup file'
	)

def adapter_main(args, dl_dir):
	if not os.path.exists(args.zotero_db_loc):
		err(f'Unable to find the Zotero database at {args.zotero_db_loc}')
		err(f'To override the default lookup location use \'--zotero-db-location\'')
		return 1

	wrn('This will lock the Zotero database, ensure that Zotero is not being used!')

	# Invoke the given action
	act = ZOTERO_ACTIONS.get(args.zotero_action, lambda: 1)
	return act(args, dl_dir)

