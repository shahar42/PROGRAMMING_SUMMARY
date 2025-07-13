#!/bin/bash
# Enhanced Master Daily Multi-Book Extraction Runner
# Updated with Expert C Programming + GPT-4.1 Nano integration
# Optimized for cron execution with file locking and enhanced logging

# Exit on any error for cron reliability
set -euo pipefail

# Colors for output (disabled in cron mode)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    BLUE=''
    YELLOW=''
    NC=''
fi

# Configuration with full paths for cron
PROJECT_DIR="/home/shahar42/Suumerizing_C_holy_grale_book"
VENV_PATH="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
BOOKS_DIR="$PROJECT_DIR/books"
LOCK_FILE="$PROJECT_DIR/extraction.lock"
MASTER_LOG="$LOG_DIR/master_extraction_$(date +%Y-%m-%d).log"

# Function for timestamped logging
log() {
    local level="$1"
    shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $*" | tee -a "$MASTER_LOG"
}

# Function for cleanup on exit
cleanup() {
    if [[ -f "$LOCK_FILE" ]]; then
        rm -f "$LOCK_FILE"
        log "INFO" "Lock file removed"
    fi
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Check for running instance (file locking)
if [[ -f "$LOCK_FILE" ]]; then
    log "ERROR" "Another extraction is already running (lock file exists)"
    exit 1
fi

# Create lock file with PID
echo $$ > "$LOCK_FILE"
log "INFO" "Created lock file with PID $$"

# Ensure we're in the right directory
if [[ ! -d "$PROJECT_DIR" ]]; then
    log "ERROR" "Project directory not found: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR" || {
    log "ERROR" "Failed to change to project directory: $PROJECT_DIR"
    exit 1
}

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Activate virtual environment with full path
if [[ ! -f "$VENV_PATH/bin/activate" ]]; then
    log "ERROR" "Virtual environment not found: $VENV_PATH"
    exit 1
fi

source "$VENV_PATH/bin/activate" || {
    log "ERROR" "Failed to activate virtual environment"
    exit 1
}

# Load environment variables
if [[ -f "config/config.env" ]]; then
    source "config/config.env"
    log "INFO" "Loaded environment configuration"
else
    log "ERROR" "Config file not found: config/config.env"
    exit 1
fi

# Verify API keys are available
if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    log "ERROR" "GEMINI_API_KEY not found in environment"
    exit 1
fi

if [[ -z "${GROK_API_KEY:-}" ]]; then
    log "ERROR" "GROK_API_KEY not found in environment"
    exit 1
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    log "ERROR" "OPENAI_API_KEY not found in environment"
    exit 1
fi

log "INFO" "Starting master daily extraction..."
log "INFO" "Run type: $(if [[ -t 1 ]]; then echo 'Interactive'; else echo 'Automated (cron)'; fi)"

# Book extraction configuration - UPDATED WITH EXPERT C PROGRAMMING
declare -A BOOK_SCRIPTS=(
    ["kernighan_ritchie"]="$BOOKS_DIR/extract_c_concepts.py"
    ["unix_env"]="$BOOKS_DIR/extract_unix_env.py"
    ["linkers_loaders"]="$BOOKS_DIR/extract_linkers_loaders.py"
    ["os_three_pieces"]="$BOOKS_DIR/extract_os_three_pieces.py"
    ["expert_c_programming"]="$BOOKS_DIR/extract_Expert_C_Programming.py"
)

declare -A BOOK_NAMES=(
    ["kernighan_ritchie"]="K&R C Programming"
    ["unix_env"]="UNIX Environment"
    ["linkers_loaders"]="Linkers & Loaders"
    ["os_three_pieces"]="Operating Systems"
    ["expert_c_programming"]="Expert C Programming"
)

declare -A BOOK_STATUS=(
    ["kernighan_ritchie"]="active"
    ["unix_env"]="active"
    ["linkers_loaders"]="active"
    ["os_three_pieces"]="active"
    ["expert_c_programming"]="active"
)

declare -A BOOK_AI_MODEL=(
    ["kernighan_ritchie"]="Gemini"
    ["unix_env"]="Grok"
    ["linkers_loaders"]="Gemini"
    ["os_three_pieces"]="Grok"
    ["expert_c_programming"]="GPT-4.1 Nano"
)

# Counters for summary
TOTAL_BOOKS=0
SUCCESSFUL_BOOKS=0
FAILED_BOOKS=0
declare -A BOOK_RESULTS
declare -A BOOK_DURATIONS
declare -A BOOK_CONCEPTS

log "INFO" "Master Archaeological Extraction Engine"
log "INFO" "Date: $(date)"

# Process each book
for book_key in "${!BOOK_SCRIPTS[@]}"; do
    TOTAL_BOOKS=$((TOTAL_BOOKS + 1))
    script_path="${BOOK_SCRIPTS[$book_key]}"
    book_name="${BOOK_NAMES[$book_key]}"
    book_status="${BOOK_STATUS[$book_key]}"
    ai_model="${BOOK_AI_MODEL[$book_key]}"
    
    log "INFO" "Processing: $book_name ($ai_model)"
    
    # Check if script exists
    if [[ ! -f "$script_path" ]]; then
        log "ERROR" "Script not found: $script_path"
        BOOK_RESULTS[$book_key]="SCRIPT_MISSING"
        FAILED_BOOKS=$((FAILED_BOOKS + 1))
        continue
    fi
    
    # Skip pending books
    if [[ "$book_status" == "pending" ]]; then
        log "INFO" "Skipping $book_name (status: pending)"
        BOOK_RESULTS[$book_key]="PENDING"
        continue
    fi
    
    # Create book-specific log
    book_log="$LOG_DIR/${book_key}_$(date +%Y-%m-%d).log"
    
    # Record start time
    start_time=$(date +%s)
    log "INFO" "Running extraction for $book_name..."
    
    # Run extraction with timeout and enhanced error handling
    if timeout 600 python3 "$script_path" >> "$book_log" 2>&1; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        BOOK_DURATIONS[$book_key]=$duration
        
        # Count extracted concepts from progress file
        progress_file="outputs/$book_key/progress.json"
        if [[ -f "$progress_file" ]]; then
            concepts=$(jq -r '.total_concepts_extracted // 0' "$progress_file" 2>/dev/null || echo "0")
            BOOK_CONCEPTS[$book_key]=$concepts
        else
            BOOK_CONCEPTS[$book_key]="0"
        fi
        
        log "INFO" "$book_name extraction completed successfully (${duration}s, ${BOOK_CONCEPTS[$book_key]} total concepts)"
        BOOK_RESULTS[$book_key]="SUCCESS"
        SUCCESSFUL_BOOKS=$((SUCCESSFUL_BOOKS + 1))
    else
        exit_code=$?
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        BOOK_DURATIONS[$book_key]=$duration
        
        if [[ $exit_code -eq 124 ]]; then
            log "ERROR" "$book_name extraction timed out (>10 minutes)"
            BOOK_RESULTS[$book_key]="TIMEOUT"
        else
            log "ERROR" "$book_name extraction failed (exit code: $exit_code)"
            BOOK_RESULTS[$book_key]="FAILED"
            
            # Log last few lines of error
            if [[ -f "$book_log" ]]; then
                log "ERROR" "Last error output for $book_name:"
                tail -3 "$book_log" | while read -r line; do
                    log "ERROR" "  $line"
                done
            fi
        fi
        FAILED_BOOKS=$((FAILED_BOOKS + 1))
    fi
done

# Generate master summary
log "INFO" "Master Extraction Summary"
log "INFO" "========================="

for book_key in "${!BOOK_RESULTS[@]}"; do
    book_name="${BOOK_NAMES[$book_key]}"
    result="${BOOK_RESULTS[$book_key]}"
    duration="${BOOK_DURATIONS[$book_key]:-0}"
    concepts="${BOOK_CONCEPTS[$book_key]:-0}"
    
    case $result in
        "SUCCESS")
            log "INFO" "✅ $book_name: COMPLETED (${duration}s, $concepts concepts)"
            ;;
        "PENDING")
            log "INFO" "⏳ $book_name: PENDING"
            ;;
        "FAILED")
            log "ERROR" "❌ $book_name: FAILED (${duration}s)"
            ;;
        "TIMEOUT")
            log "ERROR" "⏰ $book_name: TIMEOUT (${duration}s)"
            ;;
        "SCRIPT_MISSING")
            log "ERROR" "📄 $book_name: SCRIPT MISSING"
            ;;
    esac
done

log "INFO" "Statistics:"
log "INFO" "📚 Total books configured: $TOTAL_BOOKS"
log "INFO" "✅ Successful extractions: $SUCCESSFUL_BOOKS"
log "INFO" "❌ Failed extractions: $FAILED_BOOKS"

# Generate consolidated daily summary
DAILY_SUMMARY="$PROJECT_DIR/outputs/master_daily_summary_$(date +%Y-%m-%d-%H%M).md"

cat > "$DAILY_SUMMARY" << EOF
# 🏛️ Master Daily Extraction Summary

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Total Books:** $TOTAL_BOOKS
**Successful:** $SUCCESSFUL_BOOKS
**Failed:** $FAILED_BOOKS
**Run Type:** $(if [[ -t 1 ]]; then echo 'Interactive'; else echo 'Automated (cron)'; fi)

## Book Status

EOF

for book_key in "${!BOOK_RESULTS[@]}"; do
    book_name="${BOOK_NAMES[$book_key]}"
    result="${BOOK_RESULTS[$book_key]}"
    ai_model="${BOOK_AI_MODEL[$book_key]}"
    duration="${BOOK_DURATIONS[$book_key]:-0}"
    concepts="${BOOK_CONCEPTS[$book_key]:-0}"
    
    echo "### $book_name ($ai_model)" >> "$DAILY_SUMMARY"
    echo "**Status:** $result" >> "$DAILY_SUMMARY"
    if [[ "$result" == "SUCCESS" ]]; then
        echo "**Duration:** ${duration}s | **Total Concepts:** $concepts" >> "$DAILY_SUMMARY"
    fi
    echo "" >> "$DAILY_SUMMARY"
done

cat >> "$DAILY_SUMMARY" << EOF

## Logs
- **Master Log:** \`logs/master_extraction_$(date +%Y-%m-%d).log\`
- **Individual Logs:** \`logs/{book}_$(date +%Y-%m-%d).log\`

## Next Steps
- Next automated run: $(if [[ $(date +%H) -lt 11 ]]; then echo "Today at 11:00"; elif [[ $(date +%H) -lt 23 ]]; then echo "Today at 23:00"; else echo "Tomorrow at 11:00"; fi)
- Check individual book logs for any issues
- Monitor API usage and rate limits

---
*Generated by Master Archaeological Extraction Engine*
EOF

log "INFO" "Master summary saved: $DAILY_SUMMARY"

# Performance and health metrics
total_duration=0
for duration in "${BOOK_DURATIONS[@]}"; do
    total_duration=$((total_duration + duration))
done

log "INFO" "Performance Metrics:"
log "INFO" "💡 Total execution time: ${total_duration}s"
log "INFO" "💡 Average per book: $((total_duration / TOTAL_BOOKS))s"
log "INFO" "💡 Success rate: $((SUCCESSFUL_BOOKS * 100 / TOTAL_BOOKS))%"

# API usage warnings
if [[ $FAILED_BOOKS -gt 0 ]]; then
    log "WARN" "Some extractions failed - check API rate limits"
fi

# Final status
if [[ $SUCCESSFUL_BOOKS -eq $TOTAL_BOOKS ]]; then
    log "INFO" "🎉 All book extractions completed successfully!"
    exit 0
else
    log "WARN" "Some extractions had issues (Success: $SUCCESSFUL_BOOKS/$TOTAL_BOOKS)"
    exit 1
fi
