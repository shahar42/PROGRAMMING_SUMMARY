#!/bin/bash

set -e
cd "/home/shahar42/Suumerizing_C_holy_grale_book"
source venv/bin/activate
source config/config.env

echo "$(date): Starting POSIX man page extraction..."

# Run POSIX man page extraction 
echo "$(date): Running POSIX extraction..."
python3 extract_posix_manpages.py

echo "$(date): POSIX man page extraction complete!"
