#!/bin/bash
# Daily C Concept Extraction Runner
# Generated on Sat Jul 12 03:22:35 AM IDT 2025

# Change to project directory
cd "/home/shahar42/Suumerizing_C_holy_grale_book"

# Activate virtual environment
source "/home/shahar42/Suumerizing_C_holy_grale_book/venv/bin/activate"

# Run extraction with logging
echo "$(date): Starting daily C concept extraction..." >> "/home/shahar42/Suumerizing_C_holy_grale_book/logs/extraction.log"

python "/home/shahar42/Suumerizing_C_holy_grale_book/extract_c_concepts.py" >> "/home/shahar42/Suumerizing_C_holy_grale_book/logs/daily_$(date +%Y-%m-%d).log" 2>&1

# Check if extraction was successful
if [ $? -eq 0 ]; then
    echo "$(date): Daily extraction completed successfully" >> "/home/shahar42/Suumerizing_C_holy_grale_book/logs/extraction.log"
else
    echo "$(date): Daily extraction failed!" >> "/home/shahar42/Suumerizing_C_holy_grale_book/logs/extraction.log"
fi

# Optional: Send notification (uncomment if you want email notifications)
# echo "Daily C extraction completed at $(date)" | mail -s "C Concept Extraction" your-email@example.com
