# SPDX-License-Identifier: BSD-3-Clause
import sys
import os
import collections.abc
from tqdm import tqdm

__all__ = (
	'log', 'err', 'wrn', 'inf', 'dbg',
	'tlog', 'terr', 'twrn', 'tinf', 'tdbg',
	'fixup_title'
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
