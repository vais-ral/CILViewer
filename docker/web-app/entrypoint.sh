#!/usr/bin/env bash

. /home/abc/mambaforge/etc/profile.d/conda.sh
conda activate cilviewer_webapp

xvfb-run -a web_cilviewer $1 --host 0.0.0.0 --server
