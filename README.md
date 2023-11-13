> **Note:** this repo is a fork of the original github [project](https://github.com/nzbget/FailureLink)
> made by @hugbug.

> **Note:** This script is compatible with python 3.11.x. 
> If you need compatibility with Python 2.x, then you should look into the original [repository](https://github.com/nzbget/FailureLink).

# FailureLink
FailureLink [script](https://nzbget.com/documentation/post-processing-scripts/) for [NZBGet](https://nzbget.com).

This script works with nzb indexers supporting HTTP header X-DNZB-FAILURE. If the download fails, the script informs the indexer about the failure and as response the indexer gives another nzb-file for the same title, which is queued then.

Ask your indexer's staff if the indexer supports X-DNZB-FAILURE header.
