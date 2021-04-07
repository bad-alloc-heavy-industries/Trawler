# SPDX-License-Identifier: BSD-3-Clause
import sys
import time
import re

from os import path

import requests
from requests import utils

from . import config
from .common import *


__all__ = (
	'download_resource', 'get_content'
)

def get_content(url, args):
	try_count = 0
	while try_count < args.retry:
		try:
			if args.delay > 0:
				time.sleep(args.delay)

			with requests.get(
				url,
				allow_redirects = True,
				timeout = args.timeout,
				headers = {
					'User-Agent': args.user_agent
				}
			) as r:
				return r.content

		except Exception as e:
			if isinstance(e, KeyboardInterrupt):
				sys.quit()
			else:
				try_count += 1

	if try_count != 0:
		return False

def download_resource(dl_dir, ds, args):
	tlog(f'  => Downloading {ds.title} ({ds.id})')
	try_count = 0
	while try_count < args.retry:
		try:
			if args.delay > 0:
				time.sleep(args.delay)

			with requests.get(
				ds.url,
				allow_redirects = True,
				timeout = args.timeout,
				headers = {
					'User-Agent': args.user_agent
				}
			) as r:
				fname = ''
				if 'content-disposition' in r.headers.keys():
					fname = re.findall('filename=(.*)', r.headers['content-disposition'])[0]
				else:
					fname = ds.url.split('/')[-1]

				ds.filename = fname
				if not ds.dl_location.endswith(fname):
					ds.dl_location = path.join(ds.dl_location, fname)
				ds.save()
				tlog(f'    ==> Saving {fname} to {ds.dl_location}')
				with open(ds.dl_location, 'wb') as file:
					file.write(r.content)

				ds.downloaded = True
				ds.save()
				break
		except Exception as e:
			if isinstance(e, KeyboardInterrupt):
				sys.quit()
			else:
				twrn(f'  => Download failed {e}, retrying')
				try_count += 1

	if try_count != 0:
		terr(f'  => Unable to download datasheet with id {ds.id}')
		return False

	return True
