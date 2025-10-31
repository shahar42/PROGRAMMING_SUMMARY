#!/bin/bash
# Validate downloaded model and deploy V10
# This script checks file integrity before deploying

set -e

# Activate Python venv for llama.cpp conversion
VENV_PATH="/home/shahar42/Suumerizing_C_holy_grale_book/venv"
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
else
    echo "⚠️  Warning: venv not found at $VENV_PATH"
fi

# Set PATH for cron environment
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$HOME/.local/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="/mnt/external/models/v10_model_merged"
LOG_FILE="$SCRIPT_DIR/v10_deployment.log"

# Redirect all output to log file
exec > >(tee -a "$LOG_FILE") 2>&1

echo ""
echo "========================================================================"
echo "V10 VALIDATION AND DEPLOYMENT - $(date)"
echo "========================================================================"
echo ""

# Step 1: Check if model directory exists
echo "📂 Step 1: Checking model directory..."
if [ ! -d "$MODEL_DIR" ]; then
    echo "❌ Model directory not found: $MODEL_DIR"
    echo "   Download may not have completed yet"
    echo "   Exiting - will retry on next cron run"
    exit 1
fi
echo "✅ Model directory exists"
echo ""

# Step 2: Validate expected files
echo "🔍 Step 2: Validating downloaded files..."

REQUIRED_FILES=(
    "config.json"
    "tokenizer.json"
    "tokenizer_config.json"
)

MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$MODEL_DIR/$file" ]; then
        echo "❌ Missing required file: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo "✅ Found: $file"
    fi
done

# Check for model shard files (at least one should exist)
SHARD_COUNT=$(find "$MODEL_DIR" -name "model-*.safetensors" 2>/dev/null | wc -l)
if [ "$SHARD_COUNT" -eq 0 ]; then
    echo "❌ No model shard files found (model-*.safetensors)"
    MISSING_FILES=$((MISSING_FILES + 1))
else
    echo "✅ Found $SHARD_COUNT model shard file(s)"
fi

if [ $MISSING_FILES -gt 0 ]; then
    echo ""
    echo "❌ Validation failed: $MISSING_FILES missing file(s)"
    echo "   Download may still be in progress"
    echo "   Exiting - will retry on next cron run"
    exit 1
fi
echo ""

# Step 3: Validate file sizes (check if files are complete)
echo "📊 Step 3: Validating file sizes..."

# Check if any shard files are suspiciously small (< 100MB = likely incomplete)
INCOMPLETE=0
for shard in "$MODEL_DIR"/model-*.safetensors; do
    if [ -f "$shard" ]; then
        SIZE=$(stat -c%s "$shard" 2>/dev/null || stat -f%z "$shard" 2>/dev/null)
        SIZE_MB=$((SIZE / 1024 / 1024))

        if [ $SIZE_MB -lt 100 ]; then
            echo "⚠️  $(basename "$shard"): ${SIZE_MB}MB (suspiciously small, may be incomplete)"
            INCOMPLETE=$((INCOMPLETE + 1))
        else
            echo "✅ $(basename "$shard"): ${SIZE_MB}MB"
        fi
    fi
done

if [ $INCOMPLETE -gt 0 ]; then
    echo ""
    echo "❌ Validation failed: $INCOMPLETE file(s) appear incomplete"
    echo "   Download may still be in progress"
    echo "   Exiting - will retry on next cron run"
    exit 1
fi
echo ""

# Step 4: Check if gdown process is still running (download in progress)
echo "🔍 Step 4: Checking if download is still in progress..."
if pgrep -f "gdown.*v10_model_merged" > /dev/null; then
    echo "⚠️  gdown process still running - download in progress"
    echo "   Exiting - will retry on next cron run"
    exit 1
fi
echo "✅ No active download process found"
echo ""

# Step 5: Final validation - check total directory size
echo "📊 Step 5: Checking total download size..."
TOTAL_SIZE=$(du -sm "$MODEL_DIR" | cut -f1)
echo "Total size: ${TOTAL_SIZE}MB"

if [ $TOTAL_SIZE -lt 10000 ]; then
    echo "⚠️  Total size < 10GB - download may be incomplete"
    echo "   Expected: ~16GB (16,000MB)"
    echo "   Exiting - will retry on next cron run"
    exit 1
fi
echo "✅ Size validation passed (${TOTAL_SIZE}MB >= 10GB)"
echo ""

# All validations passed - proceed with deployment
echo "========================================================================"
echo "✅ ALL VALIDATIONS PASSED - STARTING DEPLOYMENT"
echo "========================================================================"
echo ""

# Run deployment script
cd "$SCRIPT_DIR"
bash ./deploy-v10-model.sh

echo ""
echo "========================================================================"
echo "✅ DEPLOYMENT COMPLETE - $(date)"
echo "========================================================================"
echo ""
echo "📝 Full log saved to: $LOG_FILE"
