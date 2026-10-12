#!/usr/bin/env python3
#
# Test for FailureLink post-processing script for NZBGet.
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
# along with the program.  If not, see <https://www.gnu.org/licenses/>.
#

import sys
from os.path import dirname
import os
import subprocess
import http.server
import json
import xmlrpc
import xmlrpc.server
import threading
import unittest
from unittest.mock import patch

POSTPROCESS_SUCCESS=93
POSTPROCESS_NONE=95
POSTPROCESS_ERROR=94

root_dir = dirname(__file__)
test_data_dir = root_dir + '/test_data'
host = '127.0.0.1'
port = '6789'
username = 'TestUser'
password = 'TestPassword'

class HttpServerMock(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		with open(test_data_dir + '/1.nzb', 'rb') as f:
			data = f.read()
		self.send_response(200)
		self.send_header("Content-Type", "text/plain")
		self.send_header("Content-Disposition", "attachment;filename=1.nzb")
		self.send_header("X-DNZB-Category", "movie")
		self.send_header("Content-Length", str(len(data)))
		self.end_headers()
		self.wfile.write(data)

	def do_POST(self):
		self.log_request()
		with open(test_data_dir + '/test_response.xml', 'rb') as f:
			file_data = f.read()
		response = xmlrpc.client.dumps((file_data,), allow_none=False, encoding=None)
		body = response.encode('utf-8')
		self.send_response(200)
		self.send_header("Content-Type", "text/xml")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

def get_python(): 
	if os.name == 'nt':
		return 'python'
	return 'python3'

def run_script():
	sys.stdout.flush()
	proc = subprocess.Popen([get_python(), root_dir + '/main.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ.copy())
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

class Tests(unittest.TestCase):
	def test_compitable_nzbget_version(self):
		os.environ.pop('NZBOP_FEEDHISTORY', None)
		[out, code, err] = run_script()
		self.assertEqual(code, POSTPROCESS_ERROR)

	def test_not_failure_not_videocheck(self):
		set_default_env()
		os.environ['NZBPP_PARSTATUS'] = '0'
		os.environ['NZBPO_CHECKVID'] = 'no'
		[out, code, err] = run_script()
		self.assertEqual(code, POSTPROCESS_SUCCESS)
		
	def test_no_failure_link(self):
		set_default_env()
		os.environ['NZBPP_PARSTATUS'] = '1'
		os.environ['NZBPO_CHECKVID'] = 'no'
		[out, code, err] = run_script()
		self.assertEqual(code, POSTPROCESS_SUCCESS)

	def test_check_video_corruption_without_ffprobe(self):
		set_default_env()
		os.environ['NZBPP_PARSTATUS'] = '0'
		os.environ['NZBPO_DOWNLOADANOTHERRELEASE'] = 'no'
		os.environ['NZBPR__DNZB_FAILURE'] = 'https://link'
		os.environ['NZBPO_CHECKVID'] = 'yes'
		os.environ['NZBPO_MEDIAEXTENSIONS'] = '.mp4'
		os.environ['NZBPO_TESTVID'] = test_data_dir + '/corrupted.mp4'
		os.environ['NZBPP_DIRECTORY'] = test_data_dir
		[out, code, err] = run_script()
		self.assertEqual(code, POSTPROCESS_SUCCESS)
		
	def test_downlaod_another_release(self):
		set_default_env()
		os.environ['NZBPP_PARSTATUS'] = '1'
		os.environ['NZBPO_DOWNLOADANOTHERRELEASE'] = 'yes'
		os.environ['NZBPR__DNZB_FAILURE'] = 'http://127.0.0.1:6789'
		os.environ['NZBPO_CHECKVID'] = 'yes'
		os.environ['NZBPO_MEDIAEXTENSIONS'] = '.mp4'
		os.environ['NZBPO_TESTVID'] = test_data_dir + '/corrupted.mp4'
		os.environ['NZBPP_DIRECTORY'] = test_data_dir
		server = http.server.HTTPServer((host, int(port)), HttpServerMock)
		thread = threading.Thread(target=server.serve_forever)
		thread.start()
		[out, code, err] = run_script()
		server.shutdown()
		server.server_close()
		thread.join()
		self.assertEqual(code, POSTPROCESS_SUCCESS)

	def test_download_another_release_special_chars_password(self):
		set_default_env()
		os.environ['NZBOP_CONTROLPASSWORD'] = 'p@ss#w0rd%test$'
		os.environ['NZBPP_PARSTATUS'] = '1'
		os.environ['NZBPO_DOWNLOADANOTHERRELEASE'] = 'yes'
		os.environ['NZBPR__DNZB_FAILURE'] = 'http://127.0.0.1:6789'
		os.environ['NZBPO_CHECKVID'] = 'yes'
		os.environ['NZBPO_MEDIAEXTENSIONS'] = '.mp4'
		os.environ['NZBPO_TESTVID'] = test_data_dir + '/corrupted.mp4'
		os.environ['NZBPP_DIRECTORY'] = test_data_dir
		server = http.server.HTTPServer((host, int(port)), HttpServerMock)
		thread = threading.Thread(target=server.serve_forever)
		thread.start()
		[out, code, err] = run_script()
		server.shutdown()
		server.server_close()
		thread.join()
		self.assertEqual(code, POSTPROCESS_SUCCESS)
		self.assertNotIn('Traceback', err + out)


def _load_main():
	import importlib.util
	spec = importlib.util.spec_from_file_location('main', root_dir + '/main.py')
	module = importlib.util.module_from_spec(spec)
	try:
		spec.loader.exec_module(module)
	except SystemExit:
		pass
	return module


class UnitTests(unittest.TestCase):
	def test_connectToNzbGet_encodes_special_chars(self):
		os.environ['NZBOP_FEEDHISTORY'] = '[]'
		os.environ['NZBOP_CONTROLIP'] = host
		os.environ['NZBOP_CONTROLPORT'] = port
		os.environ['NZBOP_CONTROLUSERNAME'] = 'user@test'
		os.environ['NZBOP_CONTROLPASSWORD'] = 'p@ss#w0rd%test$'
		os.environ['NZBPP_PARSTATUS'] = '0'
		os.environ['NZBPO_CHECKVID'] = 'no'

		module = _load_main()

		with patch.object(module, 'ServerProxy') as mock_proxy:
			module.connectToNzbGet()
			url = mock_proxy.call_args[0][0]

		self.assertIn('user%40test', url)
		self.assertIn('p%40ss%23w0rd%25test%24', url)
		self.assertIn('127.0.0.1:6789', url)
		self.assertIn('/xmlrpc', url)

	def test_connectToNzbGet_normal_password(self):
		os.environ['NZBOP_FEEDHISTORY'] = '[]'
		os.environ['NZBOP_CONTROLIP'] = host
		os.environ['NZBOP_CONTROLPORT'] = port
		os.environ['NZBOP_CONTROLUSERNAME'] = username
		os.environ['NZBOP_CONTROLPASSWORD'] = password
		os.environ['NZBPP_PARSTATUS'] = '0'
		os.environ['NZBPO_CHECKVID'] = 'no'

		module = _load_main()

		with patch.object(module, 'ServerProxy') as mock_proxy:
			module.connectToNzbGet()
			url = mock_proxy.call_args[0][0]

		self.assertIn('TestUser:TestPassword@', url)
		self.assertIn('127.0.0.1:6789', url)
		self.assertIn('/xmlrpc', url)

	def test_manifest(self):
		with open(root_dir + '/manifest.json', encoding='utf-8') as file:
			try:
				json.loads(file.read())
			except ValueError as e:
				self.fail('manifest.json is not valid.')

if __name__ == '__main__':
	unittest.main()
