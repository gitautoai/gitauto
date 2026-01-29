#!/bin/bash
(git diff --name-only; git diff --name-only --staged; git ls-files --others --exclude-standard) | sort -u
