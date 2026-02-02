#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies
apt-get update
apt-get install -y libsndfile1 ffmpeg

# Upgrade pip
pip install --upgrade pip

# Install Python packages
pip install -r requirements.txt
