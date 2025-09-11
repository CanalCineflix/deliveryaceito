#!/usr/bin/env bash

Exit on first error
set -o errexit

Install dependencies from requirements.txt
pip install -r requirements.txt

Create initial migration
Esse comando cria as tabelas se a migração ainda não existe
flask db upgrade
