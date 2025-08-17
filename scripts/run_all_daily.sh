#!/bin/bash

set -e
cd "/home/shahar42/Suumerizing_C_holy_grale_book"
source venv/bin/activate
source config/config.env

echo "$(date): Starting C++ Standard extraction..."

# Run C++ Standard extraction
echo "$(date): Running C++ Standard extraction..."
python3 books/extract_cpp_standard.py

echo "$(date): C++ Standard extraction complete!"