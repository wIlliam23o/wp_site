#!/bin/bash

# Runs python, ignoring all warnings.
# Used only for manage.py and wrun.py shebang executable.
# TODO: This method should be removed when Django gets it's stuff under control
python3 -W ignore $@
