#!/bin/bash
# Simple Daily Extraction Runner
# Runs CSAPP book extraction + POSIX man page extraction

set -e
cd "/home/shahar42/Suumerizing_C_holy_grale_book"
source venv/bin/activate
source config/config.env

echo "$(date): Starting daily extraction..."

# Run CSAPP extraction
echo "$(date): Running CSAPP extraction..."
python3 books/extract_csapp_2016.py

# Run POSIX man page extraction  
echo "$(date): Running POSIX extraction..."
python3 extract_posix_manpages.py

echo "$(date): Daily extraction complete!"
