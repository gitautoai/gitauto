#!/bin/bash
cd "$(dirname "$0")"
python -m pytest utils/files/test_should_skip_ruby.py -v
