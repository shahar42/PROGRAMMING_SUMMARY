#!/bin/bash
# Cleanup script for obsolete dataset files and intermediate outputs
# Run this after V7 dataset is confirmed ready for training

set -e

echo "🧹 Cleaning up obsolete dataset files..."
echo "This will free up ~100MB+ of disk space"
echo ""

# Calculate current size
echo "📊 Current disk usage:"
du -sh fine_tuning_llama_ver2/ fine_tuning_llama_v4_dedup/ fine_tuning_llama_v6_base/ fine_tuning_llama_v6_enhanced_final/ fine_tuning_llama_v7_sizeof/ 2>/dev/null || true
echo ""

read -p "Continue with cleanup? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "🗑️  Removing obsolete files..."

# 1. Obsolete V2 dataset
if [ -d "fine_tuning_llama_ver2" ]; then
    echo "  → Removing V2 dataset directory..."
    rm -rf fine_tuning_llama_ver2/
fi

# 2. V4/V5 intermediate files
echo "  → Removing V4/V5 intermediate files..."
rm -f fine_tuning_llama_v4_dedup/train_v4_original.json
rm -f fine_tuning_llama_v4_dedup/val_v4_original.json
rm -f fine_tuning_llama_v4_dedup/train_v5.json
rm -f fine_tuning_llama_v4_dedup/val_v5.json
rm -f fine_tuning_llama_v4_dedup/train_v5_with_contrastive.json
rm -f fine_tuning_llama_v4_dedup/train_v5_reclassified.json
rm -f fine_tuning_llama_v4_dedup/val_v5_reclassified.json
rm -f fine_tuning_llama_v4_dedup/train_v5_final.json
rm -f fine_tuning_llama_v4_dedup/val_v5_final.json

# 3. V6 assembly generation scripts (replaced by V7 real compiler approach)
echo "  → Removing V6 assembly workers..."
rm -f assembly_worker_grok.py
rm -f assembly_worker_openai.py
rm -f launch_assembly_workers.sh
rm -f integrate_assembly_enhancements.py
rm -f fix_missing_assembly.py
rm -f merge_assembly_results.py

# 4. V6 AI-generated assembly results (unreliable)
echo "  → Removing V6 AI-generated assembly data..."
rm -f assembly_enhanced_answers.json
rm -f assembly_openai_results.json
rm -f enhanced_grok.json
rm -f questions_needing_assembly.json
rm -f assembly_batch_gemini.json

# 5. V6 base/intermediate files
echo "  → Removing V6 intermediate files..."
if [ -d "fine_tuning_llama_v6_base" ]; then
    rm -rf fine_tuning_llama_v6_base/
fi
rm -f fine_tuning_llama_v6_enhanced_final/train_before_assembly.json
rm -f fine_tuning_llama_v6_enhanced_final/train_corrupted.json

# 6. V7 intermediate/debug files
echo "  → Removing V7 build intermediates..."
rm -f fine_tuning_llama_v7_sizeof/train_v6_base.json
rm -f fine_tuning_llama_v7_sizeof/train_before_assembly_fix.json
rm -f fine_tuning_llama_v7_sizeof/train_before_syscalls.json
rm -f fine_tuning_llama_v7_sizeof/train_before_format_fix.json
rm -f fine_tuning_llama_v7_sizeof/val_before_syscalls.json
rm -f fine_tuning_llama_v7_sizeof/debug_batch_*.txt

# 7. Old generation scripts (superseded)
echo "  → Removing old generation scripts..."
rm -f prepare_dataset.py
rm -f prepare_dataset_v4.py
rm -f prepare_dataset_v4_dedup.py
rm -f prepare_v6_dataset.py

# 8. V5 improvement scripts (already applied)
echo "  → Removing V5 improvement scripts..."
rm -f fine_tuning_llama_v4_dedup/improve_dataset_v5.py
rm -f fine_tuning_llama_v4_dedup/apply_templates.py
rm -f fine_tuning_llama_v4_dedup/cleanup_v5_contamination.py

# 9. Analysis/audit output files
echo "  → Removing audit reports..."
rm -f fine_tuning_llama_v4_dedup/cleanup_report_train.json
rm -f fine_tuning_llama_v4_dedup/cleanup_report_val.json
rm -f fine_tuning_llama_v4_dedup/hallucination_audit.json
rm -f fine_tuning_llama_v4_dedup/confusing_topics_analysis.json
rm -f fine_tuning_llama_v6_enhanced_final/dataset_stats.json
rm -f fine_tuning_llama_v6_enhanced_final/validation_report.json
rm -f fine_tuning_llama_v6_enhanced_final/assembly_integration_stats.json
rm -f shallow_concepts.json

# 10. Log files
echo "  → Removing log files..."
rm -f assembly_openai.log
rm -f assembly_grok.log
rm -f edge_openai.log
rm -f dataset_generation.log

# 11. Edge case generation (if already integrated)
echo "  → Removing edge case generation files..."
rm -f edge_cases.json
rm -f generate_edge_cases.py
rm -f generate_advanced_edge_cases.py
rm -f edge_cases_parallel_openai.py
rm -f enhance_parallel_openai.py

# 12. Other integration scripts (already used)
echo "  → Removing one-time integration scripts..."
rm -f integrate_all_enhancements.py
rm -f integrate_datasets.py

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 New disk usage:"
du -sh fine_tuning_llama_v4_dedup/ fine_tuning_llama_v6_enhanced_final/ fine_tuning_llama_v7_sizeof/ 2>/dev/null || true
echo ""
echo "📦 Kept files:"
echo "  ✅ V7 final dataset: fine_tuning_llama_v7_sizeof/{train,val}.json"
echo "  ✅ V7 generation scripts (for reproducibility)"
echo "  ✅ V5.1 dataset: fine_tuning_llama_v4_dedup/{train,val}.json (currently deployed)"
echo "  ✅ Deployment scripts: deploy-v2-model.sh, download-v6-from-drive.sh, etc."
echo ""
echo "🎯 Ready for V7 training!"
