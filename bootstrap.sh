#!/bin/bash

set -e
mkdir tmp_buildout
PYTHONPATH=`pwd`/tmp_buildout pip install --egg --install-option="--install-purelib=`pwd`/tmp_buildout" zc.buildout
PYTHONPATH=tmp_buildout python -c 'import zc.buildout.buildout;zc.buildout.buildout.main()' bootstrap
rm -rf tmp_buildout
