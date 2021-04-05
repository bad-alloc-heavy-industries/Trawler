# SPDX-License-Identifier: BSD-3-Clause
from orator import Model, orm
from orator.migrations import Migrator, Migration, DatabaseMigrationRepository

# ==== Models ==== #

class DatasheetTag(Model):
	__fillable__ = ['scraper_id', 'name']

	@orm.belongs_to_many('tag_links', 'tag_id', 'datasheet_id')
	def datasheets(self):
		return Datasheet

class Datasheet(Model):
	__fillable__ = [
		'scraper_id', 'title', 'url', 'filename',
		'dl_location', 'version', 'found', 'last_seen',
		'downloaded', 'src'
	]


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

	@orm.has_many
	def datasheets(self):
		return Datasheet

# ==== Migration ==== #

class CreateDatasheetTable(Migration):
	def up(self):
		with self.schema.create('datasheets') as table:
			table.increments('id').unique()
			table.integer('scraper_id').unsigned()
			table.foreign('scraper_id').references('id').on('scrapers')
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

	def down(self):
		self.schema.drop('datasheets')

class CreateScraperTable(Migration):
	def up(self):
		with self.schema.create('scrapers') as table:
			table.increments('id').unique()
			table.string('name')
			table.datetime('last_run').nullable()
			table.timestamps()

	def down(self):
		self.schema.drop('scrapers')

class CreateDatasheetTagTable(Migration):
	def up(self):
		with self.schema.create('datasheet_tags') as table:
			table.increments('id').unique()
			table.integer('scraper_id').unsigned()
			table.foreign('scraper_id').references('id').on('scrapers')
			table.string('name')
			table.timestamps()

	def down(self):
		self.schema.drop('datasheet_tags')

class CreateTagLinkTable(Migration):
	def up(self):
		with self.schema.create('tag_links') as table:
			table.increments('id').unique()
			table.integer('tag_id').unsigned()
			table.foreign('tag_id').references('id').on('datasheet_tags')
			table.integer('datasheet_id').unsigned()
			table.foreign('datasheet_id').references('id').on('datasheets')
			table.timestamps()

	def down(self):
		self.schema.drop('tag_links')

_MIGRATIONS = (
	CreateDatasheetTable,
	CreateScraperTable,
	CreateDatasheetTagTable,
	CreateTagLinkTable,
)

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
