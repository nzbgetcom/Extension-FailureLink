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
import http.server
import xmlrpc
import threading

POSTPROCESS_SUCCESS=93
POSTPROCESS_NONE=95
POSTPROCESS_ERROR=94

root_dir = dirname(__file__)
tmp_dir = root_dir + '/tmp'
test_data_dir = root_dir + '/test_data'
host = '127.0.0.1'
port = '6789'
username = 'TestUser'
password = 'TestPassword'

def RUN_TESTS():
    TEST('Should not be executed if nzbget version is incompatible', TEST_COMPATIBALE_NZBGET_VERSION)
    TEST('Should be success if no failure and no video check ', TEST_NOT_FAILURE_NOT_VIDEOCHECK)
    TEST('Should be success if no failure link', TEST_NO_FAILURE_LINK)
    TEST('Should delete tmp dir and if no failure', TEST_DELETE_DIR)
    TEST('Should check video corruption without ffprobe', TEST_CHECK_VIDEO_CORRUPTION_WITHOUT_FFPROBE)
    # TODO: Test rpc and download another release

class RequestWithFileId(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-Type", "text/plain")
		self.send_header("Content-Disposition", "attachment;filename=1.nzb")
		self.send_header("X-DNZB-Category", "movie")
		self.end_headers()
		f = open(test_data_dir + '/1.nzb', 'rb')
		self.wfile.write(f.read())
		f.close()

	def do_POST(self):
		self.log_request()
		self.send_response(200)
		self.send_header("Content-Type", "text/xml")
		self.end_headers()
		f = open(test_data_dir + '/test_response.xml', 'rb')
		response = xmlrpc.client.dumps((f.read(),), allow_none=False, encoding=None)
		self.wfile.write(response.encode('utf-8'))
		f.close()

def TEST(statement: str, test_func):
	print('\n********************************************************')
	print('TEST:', statement)
	print('--------------------------------------------------------')

	try:
		test_func()
		print(test_func.__name__, '...SUCCESS')
	except Exception as e:
		print(test_func.__name__, '...FAILED')
		traceback.print_exc()
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
	ret_code = proc.returncode
	return (out.decode(), int(ret_code), err.decode())

def set_default_env():
	# NZBGet global options
	os.environ['NZBOP_TEMPDIR'] = test_data_dir
	os.environ['NZBOP_CONTROLPORT'] = port
	os.environ['NZBOP_CONTROLIP'] = host
	os.environ['NZBOP_CONTROLUSERNAME'] = username
	os.environ['NZBOP_CONTROLPASSWORD'] = password

	os.environ['NZBPP_NZBID'] = '1'
	os.environ['NZBOP_FEEDHISTORY'] = '[]'
	os.environ.pop('NZBPP_PARSTATUS', None)
	os.environ.pop('NZBPO_CHECKVID', None)
	os.environ.pop('NZBPO_TESTVID', None)
	os.environ.pop('NZBPP_DIRECTORY', None)
	os.environ.pop('NZBPO_DELETE', None)
	os.environ.pop('NZBPO_DOWNLOADANOTHERRELEASE', None)
	os.environ.pop('NZBPR__DNZB_FAILURE', None)
	os.environ.pop('NZBPO_MEDIAEXTENSIONS', None)
	os.environ.pop('NZBPO_FFPROBE', None)


def TEST_COMPATIBALE_NZBGET_VERSION():
	os.environ.pop('NZBOP_FEEDHISTORY', None)
	[out, code, err] = run_script()
	assert('*** NZBGet post-processing script ***' in out)
	assert('This script is supposed to be called from nzbget (12.0 or later).' in out)
	assert(code == POSTPROCESS_ERROR)

def TEST_NOT_FAILURE_NOT_VIDEOCHECK():
	set_default_env()
	os.environ['NZBPP_PARSTATUS'] = '0'
	os.environ['NZBPO_CHECKVID'] = 'no'
	[out, code, err] = run_script()
	assert(code == POSTPROCESS_SUCCESS)
	
def TEST_NO_FAILURE_LINK():
	set_default_env()
	os.environ['NZBPP_PARSTATUS'] = '1'
	os.environ['NZBPO_CHECKVID'] = 'no'
	[out, code, err] = run_script()
	assert(code == POSTPROCESS_SUCCESS)
	
def TEST_DELETE_DIR():
	set_default_env()
	os.mkdir(tmp_dir)
	os.environ['NZBPP_PARSTATUS'] = '1'
	os.environ['NZBPP_DIRECTORY'] = tmp_dir
	os.environ['NZBPO_DELETE'] = 'yes'
	[out, code, err] = run_script()
	assert(os.path.isdir(tmp_dir) == False)
	assert(code == POSTPROCESS_SUCCESS)

def TEST_CHECK_VIDEO_CORRUPTION_WITHOUT_FFPROBE():
	set_default_env()
	os.environ['NZBPP_PARSTATUS'] = '0'
	os.environ['NZBPO_DOWNLOADANOTHERRELEASE'] = 'no'
	os.environ['NZBPR__DNZB_FAILURE'] = 'https://link'
	os.environ['NZBPO_CHECKVID'] = 'yes'
	os.environ['NZBPO_MEDIAEXTENSIONS'] = '.mp4'
	os.environ['NZBPO_TESTVID'] = test_data_dir + '/corrupted.mp4'
	os.environ['NZBPP_DIRECTORY'] = test_data_dir
	[out, code, err] = run_script()
	assert('[WARNING] Failed to locate ffprobe, video corruption detection disabled!' in out)
	assert('[WARNING] Install ffmpeg with x264 support to enable this feature  ...' in out)
	assert(code == POSTPROCESS_SUCCESS)
	
def TEST_DOWNLOAD_ANOTHER_RELEASE():
	set_default_env()
	os.environ['NZBPP_PARSTATUS'] = '1'
	os.environ['NZBPO_DOWNLOADANOTHERRELEASE'] = 'yes'
	os.environ['NZBPR__DNZB_FAILURE'] = 'http://127.0.0.1:6789'
	os.environ['NZBPO_CHECKVID'] = 'yes'
	os.environ['NZBPO_MEDIAEXTENSIONS'] = '.mp4'
	os.environ['NZBPO_TESTVID'] = test_data_dir + '/corrupted.mp4'
	os.environ['NZBPP_DIRECTORY'] = test_data_dir
	server = http.server.HTTPServer((host, int(port)), RequestWithFileId)
	thread = threading.Thread(target=server.serve_forever)
	thread.start()
	[out, code, err] = run_script()
	server.shutdown()
	thread.join()
	assert('[INFO] Requesting another release from indexer site' in out)
	assert(code == POSTPROCESS_SUCCESS)

RUN_TESTS()
