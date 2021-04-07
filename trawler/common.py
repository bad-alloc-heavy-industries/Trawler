# SPDX-License-Identifier: BSD-3-Clause
import sys
import os
import collections.abc
from tqdm import tqdm

__all__ = (
	'log', 'err', 'wrn', 'inf', 'dbg',
	'tlog', 'terr', 'twrn', 'tinf', 'tdbg',
	'fixup_title', 'download_resource'
)

def log(str, end = '\n', file = sys.stdout):
	print(f'\x1B[35m[*]\x1B[0m {str}', end = end, file = file)

def err(str, end = '\n', file = sys.stderr):
	print(f'\x1B[31m[!]\x1B[0m {str}', end = end, file = file)

def wrn(str, end = '\n', file = sys.stderr):
	print(f'\x1B[33m[~]\x1B[0m {str}', end = end, file = file)

def inf(str, end = '\n', file = sys.stdout):
	print(f'\x1B[36m[~]\x1B[0m {str}', end = end, file = file)

def dbg(str, end = '\n', file = sys.stdout):
	print(f'\x1B[34m[~]\x1B[0m {str}', end = end, file = file)

def tlog(str, end = '\n', file = sys.stdout):
	tqdm.write(f'\x1B[35m[*]\x1B[0m {str}', end = end, file = file)

def terr(str, end = '\n', file = sys.stderr):
	tqdm.write(f'\x1B[31m[!]\x1B[0m {str}', end = end, file = file)

def twrn(str, end = '\n', file = sys.stderr):
	tqdm.write(f'\x1B[33m[~]\x1B[0m {str}', end = end, file = file)

def tinf(str, end = '\n', file = sys.stdout):
	tqdm.write(f'\x1B[36m[~]\x1B[0m {str}', end = end, file = file)

def tdbg(str, end = '\n', file = sys.stdout):
	tqdm.write(f'\x1B[34m[~]\x1B[0m {str}', end = end, file = file)

def recusive_zip(d, u):
	for k, v in u.items():
		if isinstance(v, collections.abc.Mapping):
			d[k] = _recusive_zip(d.get(k, {}), v)
		else:
			d[k] = v
	return d

def fixup_title(s):
	if len(s) < 18:
		return f'{s}{" "*(18 - len(s))}'
	else:
		return f'{s[:15]}...'

def download_resource(dl_dir, ds):
	import requests
	from requests import utils
	from os import path

	tlog(f'  => Downloading {ds.title} ({ds.id})')
	# try:
	with requests.get(ds.url, allow_redirects = True) as r:
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
	# except:
	# 	terr(f'  => Unable to download datasheet with id {ds.id}')
	# 	return False
	# return True
