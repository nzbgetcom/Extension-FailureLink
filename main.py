#!/usr/bin/env python
#
# FailureLink post-processing script for NZBGet
#
# Copyright (C) 2013-2014 Andrey Prygunkov <hugbug@users.sourceforge.net>
# Copyright (c) 2013-2014 Clinton Hall <fock_wulf@hotmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#


import os
import sys
import platform
import subprocess
import json
import ssl
import shutil
import stat
from base64 import standard_b64encode
from xmlrpc.client import ServerProxy
import urllib.request, urllib.error
from urllib.error import HTTPError
from email.message import EmailMessage
import xml.etree.ElementTree as ET

# Exit codes used by NZBGet
POSTPROCESS_SUCCESS=93
POSTPROCESS_NONE=95
POSTPROCESS_ERROR=94

# Check if the script is called from nzbget 12.0 or later
if not 'NZBOP_FEEDHISTORY' in os.environ:
	print('*** NZBGet post-processing script ***')
	print('This script is supposed to be called from nzbget (12.0 or later).')
	sys.exit(POSTPROCESS_ERROR)

# Init script config options
verbose = False
download_another_release=os.environ.get('NZBPO_DOWNLOADANOTHERRELEASE', 'yes') == 'yes'
verbose=os.environ.get('NZBPO_VERBOSE', 'no') == 'yes'
delete=os.environ.get('NZBPO_DELETE', 'no') == 'yes'

nzbget = None

MEDIACONTAINER = (os.environ.get('NZBPO_MEDIAEXTENSIONS', 'False')).split(',')
PROGRAM_DIR = os.path.normpath(os.path.abspath(os.path.join(__file__, os.pardir)))
CHECKVIDEO = os.environ.get('NZBPO_CHECKVID', 'no') == 'yes'
if 'NZBPO_TESTVID' in os.environ and os.path.isfile(os.environ['NZBPO_TESTVID']):
    TEST_FILE = os.environ['NZBPO_TESTVID']
else:
    TEST_FILE = None
FFPROBE = None

if 'NZBPO_FFPROBE' in os.environ and os.environ['NZBPO_FFPROBE'] != "":
    if os.path.isfile(os.environ['NZBPO_FFPROBE']) or os.access(os.environ['NZBPO_FFPROBE'], os.X_OK):
        FFPROBE = os.environ['NZBPO_FFPROBE']
if CHECKVIDEO and not FFPROBE:
    if platform.system() == 'windows': 
        if os.path.isfile(os.path.join(PROGRAM_DIR, 'ffprobe.exe')):
            FFPROBE = os.path.join(PROGRAM_DIR, 'ffprobe.exe')
    elif os.path.isfile(os.path.join(PROGRAM_DIR, 'ffprobe')) or os.access(os.path.join(PROGRAM_DIR, 'ffprobe'), os.X_OK): 
        FFPROBE = os.path.join(PROGRAM_DIR, 'ffprobe')
    elif os.path.isfile(os.path.join(PROGRAM_DIR, 'avprobe')) or os.access(os.path.join(PROGRAM_DIR, 'avprobe'), os.X_OK): 
        FFPROBE = os.path.join(PROGRAM_DIR, 'avprobe')
    else:
        try:
            FFPROBE = subprocess.Popen(['which', 'ffprobe'], stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
        except: pass
        if not FFPROBE: 
            try:
                FFPROBE = subprocess.Popen(['which', 'avprobe'], stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
            except: pass
if CHECKVIDEO and FFPROBE:
    result = 1
    devnull = open(os.devnull, 'w')
    try:
        command = [FFPROBE, '-h']
        proc = subprocess.Popen(command, stdout=devnull, stderr=devnull)
        out, err = proc.communicate()
        result = proc.returncode
    except:
        FFPROBE = None
    devnull.close()
    if result:
        FFPROBE = None
if CHECKVIDEO and not FFPROBE:
    print('[WARNING] Failed to locate ffprobe, video corruption detection disabled!')
    print('[WARNING] Install ffmpeg with x264 support to enable this feature  ...')

def isVideoGood(videofile):
    fileNameExt = os.path.basename(videofile)
    fileName, fileExt = os.path.splitext(fileNameExt)
    disable = False
    if fileExt not in MEDIACONTAINER or not FFPROBE:
        return True

    print('[INFO] Checking [%s] for corruption, please stand by ...' % (fileNameExt))
    video_details, result = getVideoDetails(videofile)

    if result != 0:
        print('[Error] FAILED: [%s] is corrupted!' % (fileNameExt))
        return False
    if video_details.get("error"):
        print('[INFO] FAILED: [%s] returned error [%s].' % (fileNameExt, str(video_details.get("error"))))
        return False
    if video_details.get("streams"):
        videoStreams = [item for item in video_details["streams"] if item["codec_type"] == "video"]
        audioStreams = [item for item in video_details["streams"] if item["codec_type"] == "audio"]
        if len(videoStreams) > 0 and len(audioStreams) > 0:
            print('[INFO] SUCCESS: [%s] has no corruption.' % (fileNameExt))
            return True
        else:
            print('[INFO] FAILED: [%s] has %s video streams and %s audio streams. Assume corruption.' % (fileNameExt, str(len(videoStreams)), str(len(audioStreams))))
            return False

def getVideoDetails(videofile):
    video_details = {}
    result = 1
    if not FFPROBE:
        return video_details, result
    if 'avprobe' in FFPROBE:
        print_format = '-of'
    else:
        print_format = '-print_format'
    try:
        command = [FFPROBE, '-v', 'quiet', print_format, 'json', '-show_format', '-show_streams', '-show_error', videofile]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        result = proc.returncode
        video_details = json.loads(out)
    except: pass
    if not video_details:
        try:
            command = [FFPROBE, '-v', 'quiet', print_format, 'json', '-show_format', '-show_streams', videofile]
            proc = subprocess.Popen(command, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            result = proc.returncode
            video_details = json.loads(out)
        except:
            print('[ERROR] Checking [%s] has failed' % (videofile))
    return video_details, result


def corruption_check():
    corrupt = False
    if not CHECKVIDEO:
        return corrupt
    if not TEST_FILE: 
        ffprobe_Tested = False
    elif isVideoGood(TEST_FILE):
        ffprobe_Tested = True
    else:
        print('[INFO] DISABLED: ffprobe failed to analyse streams from test file. Stopping corruption check.')
        return corrupt
   
    num_files = 0
    good_files = 0
    for dir, dirs, files in os.walk(os.environ['NZBPP_DIRECTORY']):
        for file in files:
            if os.path.split(dir)[1][0] == '.':  # hidden directory.
                continue
            filepath = os.path.join(dir, file)
            num_files += 1
            if isVideoGood(filepath):
                good_files += 1
    if num_files > 0 and good_files < num_files:
        print('[INFO] Corrupt video file found.')
        corrupt = True
        # check for NZBGet V14+
        NZBGetVersion=os.environ['NZBOP_VERSION']
        if NZBGetVersion[0:5] >= '14.0':
            print('[NZB] MARK=BAD')
    return corrupt

def downloadNzb(failure_link):
	# Contact indexer site
	if download_another_release:
		print('[INFO] Requesting another release from indexer site')
	else:
		print('[INFO] Sending failure status to indexer site')
	sys.stdout.flush()
	
	nzbcontent = None
	headers = None
	
	try:
		headers = {'User-Agent' : 'NZBGet (FailureLink)'}
		req = urllib.request.Request(failure_link, None, headers)
		try:
			response = urllib.request.urlopen(req)
		except:
			print('[WARNING] SSL certificate verify failed, retry with bypass SSL cert.')
			context = ssl._create_unverified_context()
			response = urllib.request.urlopen(req, context=context)
		else:
			pass
		if download_another_release:
			nzbcontent = response.read()
			headers = response.info()
	except HTTPError as e:
		if e.code == 404:
			print('[INFO] No other releases found') 
		else:
			print('[ERROR] %s' % e.code)
			sys.exit(POSTPROCESS_ERROR)
	except Exception as err:
		print('[ERROR] %s' % err)
		sys.exit(POSTPROCESS_ERROR)

	return nzbcontent, headers


def connectToNzbGet():
	global nzbget
	
	# First we need to know connection info: host, port and password of NZBGet server.
	# NZBGet passes all configuration options to post-processing script as
	# environment variables.
	host = os.environ['NZBOP_CONTROLIP']
	port = os.environ['NZBOP_CONTROLPORT']
	username = os.environ['NZBOP_CONTROLUSERNAME']
	password = os.environ['NZBOP_CONTROLPASSWORD']
	
	if host == '0.0.0.0': host = '127.0.0.1'
	
	# Build an URL for XML-RPC requests
	# TODO: encode username and password in URL-format
	rpcUrl = 'http://%s:%s@%s:%s/xmlrpc' % (username, password, host, port)
	
	# Create remote server object
	nzbget = ServerProxy(rpcUrl)


def queueNzb(filename, category, nzbcontent64):
	# Adding nzb-file to queue
	# Signature:
	# append(string NZBFilename, string Category, int Priority, bool AddToTop, string Content,
	#     bool AddPaused, string DupeKey, int DupeScore, string DupeMode)
	nzbget.append(filename, category, 0, True, nzbcontent64, True, '', 0, 'ALL')

	# We need to find the id of the added nzb-file
	root = ET.fromstring(nzbget.listgroups().data)
	groups = root.findall('.//struct')

	for group in groups:
		nzb_id = group.find(".//member[name='NZBID']/value/i4").text
		nzb_filename = group.find(".//member[name='NZBFilename']/value/string").text

		if verbose:
			print(f'NZBID: {nzb_id}, NZBFilename: {nzb_filename}')

		if nzb_filename == filename:
			groupid = int(nzb_id)
			break

	if verbose:
		print('GroupID: %i' % groupid)

	return groupid


def setupDnzbHeaders(groupid, headers):
	for header in headers:
		if verbose:
			print(header.strip())
		if header[0:7] == 'X-DNZB-':
			name = header.split(':')[0].strip()
			value = headers.get(name)
			if verbose:
				print('%s=%s' % (name, value))
				
			# Setting "X-DNZB-" as post-processing parameter
			param = '*DNZB:%s=%s' % (name[7:], value)
			nzbget.editqueue('GroupSetParameter', 0, param, [groupid])


def unpauseGroup(groupid):
	nzbget.editqueue('GroupResume', 0, '', [groupid])

def onerror(func, path, exc_info):
	"""
	Error handler for ``shutil.rmtree``.

	If the error is due to an access error (read only file)
	it attempts to add write permission and then retries.

	If the error is for another reason it re-raises the error.
 
	Usage : ``shutil.rmtree(path, onerror=onerror)``
	"""
	if not os.access(path, os.W_OK):
		# Is the error an access error ?
		os.chmod(path, stat.S_IWUSR)
		func(path)
	else:
		raise

def rmDir(dirName):
	print('[INFO] Deleting %s' % (dirName))
	try:
		shutil.rmtree(dirName, onerror=onerror)
	except:
		print('[ERROR] Unable to delete folder %s' % (dirName))

def main():
        # Check par and unpack status for errors.
        #  NZBPP_PARSTATUS    - result of par-check:
        #                       0 = not checked: par-check is disabled or nzb-file does
        #                           not contain any par-files;
        #                       1 = checked and failed to repair;
        #                       2 = checked and successfully repaired;
        #                       3 = checked and can be repaired but repair is disabled.
        #                       4 = par-check needed but skipped (option ParCheck=manual);
        #  NZBPP_UNPACKSTATUS - result of unpack:
        #                       0 = unpack is disabled or was skipped due to nzb-file
        #                           properties or due to errors during par-check;
        #                       1 = unpack failed;
        #                       2 = unpack successful.
	
        failure = os.environ.get('NZBPP_PARSTATUS', 'False') == '1' or os.environ.get('NZBPP_UNPACKSTATUS', 'False') == '1' or os.environ.get('NZBPP_PPSTATUS_FAKE') == 'yes'
        failure_link = os.environ.get('NZBPR__DNZB_FAILURE')
        if failure:
            corrupt = False
        else:
            corrupt = corruption_check()
            if corrupt and failure_link:
                failure_link = failure_link + '&corrupt=true'

        if not (failure or corrupt):
                sys.exit(POSTPROCESS_SUCCESS)

        if delete and os.path.isdir(os.environ['NZBPP_DIRECTORY']):
                rmDir(os.environ['NZBPP_DIRECTORY'])

        if not failure_link:
                sys.exit(POSTPROCESS_SUCCESS)

        nzbcontent, headers = downloadNzb(failure_link)

        if not download_another_release:
                sys.exit(POSTPROCESS_SUCCESS)

        if verbose:
                print(headers)

        if not nzbcontent or nzbcontent[0:5] != b'<?xml':
                print('[INFO] No other releases found')
                if verbose and nzbcontent:
                        print(nzbcontent)
                sys.exit(POSTPROCESS_SUCCESS)

        print('[INFO] Another release found, adding to queue')
        sys.stdout.flush()

        # Parsing filename from header
        msg = EmailMessage()
        msg['Content-Disposition'] = headers.get('Content-Disposition', '')
        filename = msg.get_filename()

        if verbose:
                print('filename: %s' % filename)

        # Parsing category from headers

        category = headers.get('X-DNZB-Category', '')
        if verbose:
                print('category: %s' % category)

        # Encode nzb-file content into base64
        nzbcontent64=standard_b64encode(nzbcontent)
        nzbcontent = None

        connectToNzbGet()
        groupid = queueNzb(filename, category, nzbcontent64)
        if groupid == 0:
                print('[WARNING] Could not find added nzb-file in the list of downloads')
                sys.stdout.flush()
                sys.exit(POSTPROCESS_ERROR)

        setupDnzbHeaders(groupid, headers)
        unpauseGroup(groupid)
main()

# All OK, returning exit status 'POSTPROCESS_SUCCESS' (int <93>) to let NZBGet know
# that our script has successfully completed.
sys.exit(POSTPROCESS_SUCCESS)
