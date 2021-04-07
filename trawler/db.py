# SPDX-License-Identifier: BSD-3-Clause
from orator import Model, orm
from orator.migrations import Migrator, Migration, DatabaseMigrationRepository

from . import config
from .common import *

# ==== Models ==== #

class CacheMetadata(Model):
	__connection__ = 'trawler_cache'
	__fillable__ = ['name', 'value']

class DatasheetTag(Model):
	__fillable__ = ['scraper_id', 'name']
	__connection__ = 'trawler_cache'

	@orm.belongs_to_many('tag_links', 'tag_id', 'datasheet_id')
	def datasheets(self):
		return Datasheet

class Datasheet(Model):
	__fillable__ = [
		'scraper_id', 'title', 'url', 'filename',
		'dl_location', 'version', 'found', 'last_seen',
		'downloaded', 'src'
	]
	__connection__ = 'trawler_cache'

	def has_tag(self, tag):
		return self.tags().where('tag_id', '=', tag.id).exists()

	def add_tag(self, tag):
		if not self.has_tag(tag):
			self.tags().attach(tag)

	def remove_tag(self, tag):
		if self.has_tag(tag):
			self.tags().detach(tag)

	@orm.belongs_to_many('tag_links', 'datasheet_id', 'tag_id')
	def tags(self):
		return DatasheetTag

class Scraper(Model):
	__fillable__ = ['name', 'last_run']
	__connection__ = 'trawler_cache'

	@orm.has_many
	def datasheets(self):
		return Datasheet

# ==== Migration ==== #

class CreateDatasheetTable(Migration):
	def up(self):
		with self.schema.create('datasheets') as table:
			table.increments('id').unique()
			table.integer('scraper_id').unsigned()
			table.foreign('scraper_id').references('id').on('scrapers').on_delete('cascade')
			table.string('title').nullable()
			table.string('url').nullable()
			table.string('src').nullable()
			table.string('filename').nullable()
			table.string('dl_location').nullable()
			table.string('version').nullable()
			table.boolean('downloaded').nullable()
			table.datetime('last_seen').nullable()
			table.datetime('found')
			table.timestamps()

	def update(self, from_version):
		with self.schema.table('datasheets') as table:
			pass

	def down(self):
		self.schema.drop('datasheets')

class CreateScraperTable(Migration):
	def up(self):
		with self.schema.create('scrapers') as table:
			table.increments('id').unique()
			table.string('name')
			table.datetime('last_run').nullable()
			table.boolean('meta').nullable()
			table.timestamps()

	def update(self, from_version):
		with self.schema.table('scrapers') as table:
			# All the fields added in v0.2
			if from_version < 1:
				table.boolean('meta').nullable()

	def down(self):
		self.schema.drop('scrapers')

class CreateDatasheetTagTable(Migration):
	def up(self):
		with self.schema.create('datasheet_tags') as table:
			table.increments('id').unique()
			table.integer('scraper_id').unsigned()
			table.foreign('scraper_id').references('id').on('scrapers').on_delete('cascade')
			table.string('name')
			table.timestamps()

	def update(self, from_version):
		with self.schema.table('datasheet_tags') as table:
			pass

	def down(self):
		self.schema.drop('datasheet_tags')

class CreateTagLinkTable(Migration):
	def up(self):
		with self.schema.create('tag_links') as table:
			table.increments('id').unique()
			table.integer('tag_id').unsigned()
			table.foreign('tag_id').references('id').on('datasheet_tags').on_delete('cascade')
			table.integer('datasheet_id').unsigned()
			table.foreign('datasheet_id').references('id').on('datasheets').on_delete('cascade')
			table.timestamps()

	def update(self, from_version):
		with self.schema.table('tag_links') as table:
			pass

	def down(self):
		self.schema.drop('tag_links')

class CreateCacheMetadataTable(Migration):
	def up(self):
		with self.schema.create('cache_metadata') as table:
			table.increments('id').unique()
			table.string('name')
			table.string('value').nullable()
			table.timestamps()

	def update(self, from_version):
		with self.schema.table('cache_metadata') as table:
			pass

	def down(self):
		self.schema.drop('cache_metadata')


_MIGRATIONS = (
	CreateDatasheetTable,
	CreateScraperTable,
	CreateDatasheetTagTable,
	CreateTagLinkTable,
	CreateCacheMetadataTable,
)

def check_schema(dbm):
	# If we don't have the cache metadata table, we absolutely need to run migrations
	try:
		dbm.table('cache_metadata').exists()
	except:
		wrn('Trawler schema is massively out of date, updating')
		run_migration(dbm, CreateCacheMetadataTable)
	finally:
		try:
			sv = CacheMetadata.where('name', '=', 'schema_version').first_or_fail()
		except:
			sv = CacheMetadata()
			sv.name = 'schema_version'
			sv.value = 0 # We plan to run an upgrade anyway so
			sv.save()

		if int(sv.value) < config.TRAWLER_SCHEMA_VERSION:
			# The schema version is out of date, run the update
			run_update(dbm, int(sv.value))

			# The update ran, save the new schema version
			sv.value = config.TRAWLER_SCHEMA_VERSION
			sv.save()



def run_migration(dbm, m):
	dbm_repo = DatabaseMigrationRepository(dbm, 'migrations')

	mi = m()
	mi.set_connection(dbm_repo.get_connection())

	if mi.transactional:
		with mi.db.transaction():
			mi.up()
	else:
		mi.up()


def run_migrations(dbm):
	dbm_repo = DatabaseMigrationRepository(dbm, 'migrations')

	for m in _MIGRATIONS:
		mi = m()
		mi.set_connection(dbm_repo.get_connection())

		if mi.transactional:
			with mi.db.transaction():
				mi.up()
		else:
			mi.up()

def run_update(dbm, from_version):
	dbm_repo = DatabaseMigrationRepository(dbm, 'migrations')
	inf(f'Updating Trawler schema from v{from_version} to v{config.TRAWLER_SCHEMA_VERSION}')

	for m in _MIGRATIONS:
		mi = m()
		mi.set_connection(dbm_repo.get_connection())

		if mi.transactional:
			with mi.db.transaction():
				mi.update(from_version)
		else:
			mi.update(from_version)
