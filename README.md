> **Note:** this repo is a fork of the original github [project](https://github.com/nzbget/FailureLink)
> made by @hugbug.

> **Note:** This script is compatible with python 3.9.x and above.

> **Note:** If you need support for Python 2.x or older Python3.x versions please use [v1.21](https://github.com/nzbgetcom/Extension-FailureLink/releases/tag/v1.21) release.

> **Note:** [Here](https://github.com/nzbgetcom/nzbget/discussions/56) you can discuss problems with different versions of Python.


# FailureLink
FailureLink [script](https://nzbget.com/documentation/post-processing-scripts/) for [NZBGet](https://nzbget.com).

This script works with nzb indexers supporting HTTP header X-DNZB-FAILURE. If the download fails, the script informs the indexer about the failure and as response the indexer gives another nzb-file for the same title, which is queued then.

Ask your indexer's staff if the indexer supports X-DNZB-FAILURE header.
