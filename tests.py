#!/usr/bin/env python3
#
# Test for VideoSort post-processing script for NZBGet.
#
# Copyright (C) 2023 Denis <denis@nzbget.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with the program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
from os.path import dirname
import os
import traceback
import subprocess
import json
import http.server
import xmlrpc.server
import threading
import json

POSTPROCESS_SUCCESS=93
POSTPROCESS_NONE=95
POSTPROCESS_ERROR=94

root_dir = dirname(__file__)
test_data_dir = root_dir + '/test_data'
host = '127.0.0.1'
port = '6789'
username = 'TestUser'
password = 'TestPassword'

def RUN_TESTS():
	TEST('Should not be executed if nzbget version is incompatible', TEST_COMPATIBALE_NZBGET_VERSION)
	# clean_up()

class RequestEmpty(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-Type", "application/json")
		self.end_headers()
		self.wfile.write(b'{}')

class RequestWithFileId(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		f = open(test_data_dir + '/nzbget_response.json')
		data = json.load(f)
		self.send_header("Content-Type", "application/json")
		self.end_headers()
		formatted = json.dumps(data, separators=(',\n', ' : '), indent=0)
		self.wfile.write(formatted.encode('utf-8'))
		f.close()

	def do_POST(self):
		self.log_request()
		self.send_response(200)
		self.send_header("Content-Type", "text/xml")
		self.end_headers()
		data = '<?xml version="1.0" encoding="UTF-8"?><nzb></nzb>'
		response = xmlrpc.client.dumps((data,), allow_none=False, encoding=None)
		self.wfile.write(response.encode('utf-8'))

def TEST(statement: str, test_func):
	print('\n********************************************************')
	print('TEST:', statement)
	print('--------------------------------------------------------')

	try:
		test_func()
		print(test_func.__name__, '...SUCCESS')
	except Exception as e:
		print(test_func.__name__, '...FAILED')
		traceback.print_exception(e)
	finally:
		print('********************************************************\n')

def get_python(): 
	if os.name == 'nt':
		return 'python'
	return 'python3'

def clean_up():
	for root, dirs, files in os.walk(tmp_dir, topdown=False):
		for name in files:
			file_path = os.path.join(root, name)
			os.remove(file_path)
		for name in dirs:
			dir_path = os.path.join(root, name)
			os.rmdir(dir_path)
	os.rmdir(tmp_dir)

def run_script():
	sys.stdout.flush()
	proc = subprocess.Popen([get_python(), root_dir + '/FailureLink.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ.copy())
	out, err = proc.communicate()
	proc.pid
	ret_code = proc.returncode
	return (out.decode(), int(ret_code), err.decode())

def set_defaults_env():
	# NZBGet global options
	os.environ['NZBOP_SCRIPTDIR'] = 'test'
	os.environ['NZBOP_ARTICLECACHE'] = '64'
	os.environ['NZBOP_TEMPDIR'] = tmp_dir
	os.environ['NZBOP_CONTROLPORT'] = port
	os.environ['NZBOP_CONTROLIP'] = host
	os.environ['NZBOP_CONTROLUSERNAME'] = username
	os.environ['NZBOP_CONTROLPASSWORD'] = password

	# script options
	os.environ['NZBPO_BANNEDEXTENSIONS'] = '.mkv,.mp4'

	os.environ['NZBPP_DIRECTORY'] = tmp_dir
	os.environ['NZBPP_NZBNAME'] = 'test'
	os.environ['NZBPP_PARSTATUS'] = '2'
	os.environ['NZBPP_UNPACKSTATUS'] = '2'
	os.environ['NZBPP_CATEGORY'] = ''
	os.environ['NZBPP_NZBID'] = '8'

	os.environ['NZBPR__DNZB_USENZBNAME'] = 'no'
	os.environ['NZBPR__DNZB_PROPERNAME'] = ''
	os.environ['NZBPR__DNZB_EPISODENAME'] = ''

	os.environ['NZBNA_EVENT'] = 'NZB_ADDED'
	os.environ.pop('NZBPR_PPSTATUS_FAKEBAN', None)
	os.environ.pop('NZBPP_STATUS', None)

def TEST_COMPATIBALE_NZBGET_VERSION():
	os.environ.pop('NZBOP_FEEDHISTORY', None)
	[out, code, err] = run_script()
	assert('*** NZBGet post-processing script ***' in out)
	assert('This script is supposed to be called from nzbget (12.0 or later).' in out)
	assert(code == POSTPROCESS_ERROR)

def TEST_DETECT_FAKE_FILES():
	set_defaults_env()
	file_name = 'nzb_test_file'
	os.environ['NZBNA_NZBNAME'] = file_name
	os.environ['NZBNA_CATEGORY'] = 'movies'
	os.environ['NZBNA_NZBID'] = '8'
	os.environ['NZBPR_PPSTATUS_FAKEBAN'] = '.nzb,.json,.mp4'
	os.environ['NZBNA_DIRECTORY'] = test_data_dir
	os.environ['NZBNA_EVENT'] = 'FILE_DOWNLOADED'
	os.environ['NZBPR_FAKEDETECTOR_SORTED'] = 'no'

	server = http.server.HTTPServer((host, int(port)), RequestWithFileId)
	thread = threading.Thread(target=server.serve_forever)
	thread.start()
	[out, code, err] = run_script()
	server.shutdown()
	thread.join()
	assert('[WARNING] Download has media files and executables' in out)
	assert('[NZB] NZBPR_PPSTATUS_FAKE=yes' in out)
	assert('[NZB] MARK=BAD' in out)
	assert('[DETAIL] Detecting completed for %s' % file_name in out)
	assert(code == POSTPROCESS_SUCCESS)

RUN_TESTS()
