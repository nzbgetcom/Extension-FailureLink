> **Note:** this repo is a fork of the original github [project](https://github.com/nzbget/FailureLink)
> made by @hugbug.

## Requirements

- NZBGet v23+ and Python 3.8+
- Legacy NZBGet v22: use [v2.0](https://github.com/nzbgetcom/Extension-FailureLink/releases/tag/v2.0) release
- Python 2.x or older Python 3.x: use [v1.21](https://github.com/nzbgetcom/Extension-FailureLink/releases/tag/v1.21) release
- Optional: `ffprobe` (or `avprobe`) for video corruption detection

# FailureLink

FailureLink [script](https://nzbget.com/documentation/extension-scripts/) for [NZBGet](https://nzbget.com).

Authors:
- Andrey Prygunkov <hugbug@users.sourceforge.net>
- Clinton Hall
- dogzipp

This script works with nzb indexers supporting HTTP header `X-DNZB-FAILURE` (or `X-DNZB-FailureLink`). If the download fails or video files are corrupt, the script informs the indexer about the failure and, in response, the indexer provides another nzb-file for the same release to be added to the queue.

Ask your indexer's staff if the indexer supports `X-DNZB-FAILURE` header.

## Installation

- Download the newest version from [releases page](https://github.com/nzbgetcom/Extension-FailureLink/releases).
- Unpack into pp-scripts directory. Your pp-scripts directory now should have folder "FailureLink" with file "main.py";
- Open settings tab in NZBGet web-interface and define settings for FailureLink;
- Save changes and restart NZBGet.

## Options

### DownloadAnotherRelease

If the NZB download of a Movie or TV Show fails, request an alternate NZB-file of the same release and add it to queue. If disabled the indexer site is still informed about the failure but no other nzb-file is queued (`yes`, `no`).

### Delete

Cleanup directory. Set this to `yes` in order to delete all corrupt and failed files (`yes`, `no`).

### Verbose

Print more logging messages for debugging or if you need to report a bug (`yes`, `no`).

### CheckVid

Check videos for corruption. If disabled, ignore the settings below (`yes`, `no`).

### ffprobe

Absolute path for ffprobe or avprobe, or leave blank to search your system path.

### testVid

Absolute path for known good video. This is optional and is only needed to test if ffprobe is correctly compiled and working.

### mediaExtensions

Comma-separated list of video/media extensions that will be checked for corruption (default: `.mkv,.avi,.divx,.xvid,.mov,.wmv,.mp4,.mpg,.mpeg,.vob,.ts`).

## Credits

This script is part of the [NZBGet](https://nzbget.com) project.
