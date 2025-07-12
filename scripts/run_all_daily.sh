#!/bin/bash
# Master Daily Multi-Book Extraction Runner
# Orchestrates all 4 book extractions with error handling and consolidated logging

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/shahar42/Suumerizing_C_holy_grale_book"
VENV_PATH="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
BOOKS_DIR="$PROJECT_DIR/books"

# Ensure we're in the right directory
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ Failed to change to project directory: $PROJECT_DIR${NC}"
    exit 1
}

# Activate virtual environment
source "$VENV_PATH/bin/activate" || {
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    exit 1
}

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Start master log
MASTER_LOG="$LOG_DIR/master_extraction_$(date +%Y-%m-%d).log"
echo "$(date): Starting master daily extraction..." >> "$MASTER_LOG"

echo -e "${BLUE}🏛️  Master Archaeological Extraction Engine${NC}"
echo -e "${BLUE}📅 Date: $(date)${NC}"
echo ""

# Book extraction configuration
declare -A BOOK_SCRIPTS=(
    ["kernighan_ritchie"]="$BOOKS_DIR/extract_c_concepts.py"
    ["unix_env"]="$BOOKS_DIR/extract_unix_env.py"
    ["linkers_loaders"]="$BOOKS_DIR/extract_linkers_loaders.py"
    ["os_three_pieces"]="$BOOKS_DIR/extract_os_three_pieces.py"
)

declare -A BOOK_NAMES=(
    ["kernighan_ritchie"]="K&R C Programming"
    ["unix_env"]="UNIX Environment"
    ["linkers_loaders"]="Linkers & Loaders"
    ["os_three_pieces"]="Operating Systems"
)

declare -A BOOK_STATUS=(
    ["kernighan_ritchie"]="active"
    ["unix_env"]="pending"
    ["linkers_loaders"]="pending"
    ["os_three_pieces"]="pending"
)

# Counters for summary
TOTAL_BOOKS=0
SUCCESSFUL_BOOKS=0
FAILED_BOOKS=0
declare -A BOOK_RESULTS

# Process each book
for book_key in "${!BOOK_SCRIPTS[@]}"; do
    TOTAL_BOOKS=$((TOTAL_BOOKS + 1))
    script_path="${BOOK_SCRIPTS[$book_key]}"
    book_name="${BOOK_NAMES[$book_key]}"
    book_status="${BOOK_STATUS[$book_key]}"
    
    echo -e "${BLUE}📚 Processing: $book_name${NC}"
    
    # Check if script exists
    if [[ ! -f "$script_path" ]]; then
        echo -e "${RED}❌ Script not found: $script_path${NC}"
        BOOK_RESULTS[$book_key]="SCRIPT_MISSING"
        FAILED_BOOKS=$((FAILED_BOOKS + 1))
        echo "$(date): $book_name - Script missing: $script_path" >> "$MASTER_LOG"
        continue
    fi
    
    # Skip pending books for now (can be enabled later)
    if [[ "$book_status" == "pending" ]]; then
        echo -e "${YELLOW}⏳ Skipping $book_name (status: pending)${NC}"
        BOOK_RESULTS[$book_key]="PENDING"
        continue
    fi
    
    # Run the extraction
    echo -e "${YELLOW}⚡ Running extraction for $book_name...${NC}"
    
    # Create book-specific log
    book_log="$LOG_DIR/${book_key}_$(date +%Y-%m-%d).log"
    
    # Run extraction with timeout and error handling
    timeout 300 python "$script_path" >> "$book_log" 2>&1
    exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        echo -e "${GREEN}✅ $book_name extraction completed successfully${NC}"
        BOOK_RESULTS[$book_key]="SUCCESS"
        SUCCESSFUL_BOOKS=$((SUCCESSFUL_BOOKS + 1))
        echo "$(date): $book_name - Extraction successful" >> "$MASTER_LOG"
    elif [[ $exit_code -eq 124 ]]; then
        echo -e "${RED}❌ $book_name extraction timed out (>5 minutes)${NC}"
        BOOK_RESULTS[$book_key]="TIMEOUT"
        FAILED_BOOKS=$((FAILED_BOOKS + 1))
        echo "$(date): $book_name - Extraction timed out" >> "$MASTER_LOG"
    else
        echo -e "${RED}❌ $book_name extraction failed (exit code: $exit_code)${NC}"
        BOOK_RESULTS[$book_key]="FAILED"
        FAILED_BOOKS=$((FAILED_BOOKS + 1))
        echo "$(date): $book_name - Extraction failed with exit code $exit_code" >> "$MASTER_LOG"
        
        # Show last few lines of error log
        echo -e "${YELLOW}Last error output:${NC}"
        tail -5 "$book_log"
    fi
    
    echo ""
done

# Generate master summary
echo -e "${BLUE}📊 Master Extraction Summary${NC}"
echo -e "${BLUE}════════════════════════════${NC}"
echo ""

for book_key in "${!BOOK_RESULTS[@]}"; do
    book_name="${BOOK_NAMES[$book_key]}"
    result="${BOOK_RESULTS[$book_key]}"
    
    case $result in
        "SUCCESS")
            echo -e "✅ $book_name: ${GREEN}COMPLETED${NC}"
            ;;
        "PENDING")
            echo -e "⏳ $book_name: ${YELLOW}PENDING${NC}"
            ;;
        "FAILED")
            echo -e "❌ $book_name: ${RED}FAILED${NC}"
            ;;
        "TIMEOUT")
            echo -e "⏰ $book_name: ${RED}TIMEOUT${NC}"
            ;;
        "SCRIPT_MISSING")
            echo -e "📄 $book_name: ${RED}SCRIPT MISSING${NC}"
            ;;
    esac
done

echo ""
echo -e "${BLUE}Statistics:${NC}"
echo -e "📚 Total books configured: $TOTAL_BOOKS"
echo -e "✅ Successful extractions: $SUCCESSFUL_BOOKS"
echo -e "❌ Failed extractions: $FAILED_BOOKS"

# Write final status to master log
echo "$(date): Master extraction completed - Success: $SUCCESSFUL_BOOKS, Failed: $FAILED_BOOKS" >> "$MASTER_LOG"

# Generate consolidated daily summary
DAILY_SUMMARY="$PROJECT_DIR/outputs/master_daily_summary_$(date +%Y-%m-%d).md"

cat > "$DAILY_SUMMARY" << EOF
# 🏛️ Master Daily Extraction Summary

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Total Books:** $TOTAL_BOOKS
**Successful:** $SUCCESSFUL_BOOKS
**Failed:** $FAILED_BOOKS

## Book Status

EOF

for book_key in "${!BOOK_RESULTS[@]}"; do
    book_name="${BOOK_NAMES[$book_key]}"
    result="${BOOK_RESULTS[$book_key]}"
    
    echo "### $book_name" >> "$DAILY_SUMMARY"
    echo "**Status:** $result" >> "$DAILY_SUMMARY"
    echo "" >> "$DAILY_SUMMARY"
done

cat >> "$DAILY_SUMMARY" << EOF

## Logs
- **Master Log:** \`logs/master_extraction_$(date +%Y-%m-%d).log\`
- **Individual Logs:** \`logs/{book}_$(date +%Y-%m-%d).log\`

## Next Steps
Run this script again tomorrow to continue multi-book extraction.

---
*Generated by Master Archaeological Extraction Engine*
EOF

echo ""
echo -e "${GREEN}📋 Master summary saved: $DAILY_SUMMARY${NC}"

# Optional: Check API usage and warn about limits
echo ""
echo -e "${BLUE}💡 Next Run Suggestions:${NC}"
if [[ $SUCCESSFUL_BOOKS -gt 0 ]]; then
    echo "✅ Consider enabling more 'pending' books in config/books_config.json"
fi
if [[ $FAILED_BOOKS -gt 0 ]]; then
    echo "🔧 Check individual logs for failed books and fix issues"
fi

echo -e "${GREEN}🎉 Master daily extraction complete!${NC}"
