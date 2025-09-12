#!/usr/bin/env bash

Exit on first error
set -o errexit

Install dependencies from requirements.txt
pip install -r requirements.txt

flask db upgrade
