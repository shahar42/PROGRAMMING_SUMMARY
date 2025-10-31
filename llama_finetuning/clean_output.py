#!/usr/bin/env python3 -u
"""
Clean llama.cpp output by removing garbage tokens after EOT
-u flag forces unbuffered output for real-time streaming
"""
import sys
import re

# Patterns that indicate garbage after EOT token
garbage_patterns = [
    r'[а-яА-ЯёЁ]+',  # Cyrillic characters
    r'[\u0400-\u04FF]+',  # Unicode Cyrillic range
    r'ыџN',
    r'user.*ілмакт.*',
    r'<\|eot_id\|>.*',  # Everything after literal eot_id marker
]

# Read from stdin as bytes to handle non-UTF8 from llama.cpp
for line in sys.stdin.buffer:
    # Decode with error handling for invalid UTF-8
    try:
        text = line.decode('utf-8', errors='replace')
    except:
        continue

    # Stop at any garbage pattern
    for pattern in garbage_patterns:
        match = re.search(pattern, text)
        if match:
            # Output everything before the garbage
            clean = text[:match.start()].rstrip()
            if clean:
                print(clean, flush=True)
            break
    else:
        # No garbage found, output the line
        print(text, end='', flush=True)
