#!/bin/bash

set -e

current_dir=$(pwd)

python -m pip install --upgrade pip

echo checking SERVER...
cd "$current_dir/easyNetVisibility/server/server_django"
pip install -r requirements.txt
pip install flake8
pip install bandit[toml]
echo "Running Flake..."
flake8 . --count --max-line-length=200 --show-source --statistics --exclude='*/migrations/*,*/tests/*,*/scripts/*'
echo "Running Bandit..."
bandit -r . -ll -x "*/migrations/*,*/tests/*"

echo checking CLIENT...
cd "$current_dir/easyNetVisibility/client"
pip install -r requirements.txt
echo "Running Flake..."
flake8 . --count --max-line-length=200 --show-source --statistics --exclude='tests'
