> **Note:** this repo is a fork of the original github [project](https://github.com/nzbget/FailureLink)
> made by @hugbug.

## NZBGet Versions

- pre-release v23+  [v3.0](https://github.com/nzbgetcom/Extension-FailureLink/releases/tag/v3.0)
- stable  v22 [v2.0](https://github.com/nzbgetcom/Extension-FailureLink/releases/tag/v2.0)
- legacy  v21 [v2.0](https://github.com/nzbgetcom/Extension-FailureLink/releases/tag/v2.0)

> **Note:** This script is compatible with python 3.8.x and above.
If you need support for Python 2.x or older Python3.x versions please use [v1.21](https://github.com/nzbgetcom/Extension-FailureLink/releases/tag/v1.21) release.

# FailureLink
FailureLink [script](https://nzbget.com/documentation/post-processing-scripts/) for [NZBGet](https://nzbget.com).

This script works with nzb indexers supporting HTTP header X-DNZB-FAILURE. If the download fails, the script informs the indexer about the failure and as response the indexer gives another nzb-file for the same title, which is queued then.

Ask your indexer's staff if the indexer supports X-DNZB-FAILURE header.
