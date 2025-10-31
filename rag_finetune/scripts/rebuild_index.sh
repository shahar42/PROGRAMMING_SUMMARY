#!/bin/bash
# Rebuild concept index with venv activated

cd /home/shahar42/Suumerizing_C_holy_grale_book
source venv/bin/activate
python rag_finetune/scripts/build_concept_index.py
