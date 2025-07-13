#!/bin/bash
# Multi-Book Processor Verification Script
# Verifies all 4 extraction processors are properly configured

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/shahar42/Suumerizing_C_holy_grale_book"
VENV_PATH="$PROJECT_DIR/venv"
CONFIG_FILE="$PROJECT_DIR/config/config.env"

echo -e "${BLUE}🔍 Multi-Book Processor Verification${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Check project directory
if [[ ! -d "$PROJECT_DIR" ]]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_DIR${NC}"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1
echo -e "${GREEN}✅ Project directory: $PROJECT_DIR${NC}"

# Check virtual environment
if [[ ! -d "$VENV_PATH" ]]; then
    echo -e "${RED}❌ Virtual environment not found: $VENV_PATH${NC}"
    exit 1
fi

source "$VENV_PATH/bin/activate" || {
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    exit 1
}
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Check config file and API keys
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo -e "${RED}❌ Config file not found: $CONFIG_FILE${NC}"
    exit 1
fi

source "$CONFIG_FILE"
echo -e "${GREEN}✅ Config file loaded${NC}"

# Verify API keys
echo -e "\n${BLUE}🔑 API Key Verification${NC}"
if [[ -n "$GEMINI_API_KEY" ]]; then
    echo -e "${GREEN}✅ GEMINI_API_KEY present (${#GEMINI_API_KEY} chars)${NC}"
else
    echo -e "${RED}❌ GEMINI_API_KEY missing${NC}"
fi

if [[ -n "$GROK_API_KEY" ]]; then
    echo -e "${GREEN}✅ GROK_API_KEY present (${#GROK_API_KEY} chars)${NC}"
else
    echo -e "${RED}❌ GROK_API_KEY missing${NC}"
fi

# Define processors
declare -A PROCESSORS=(
    ["kernighan_ritchie"]="books/extract_c_concepts.py|Gemini|K&R C Programming"
    ["unix_env"]="books/extract_unix_env.py|Grok|UNIX Environment"
    ["linkers_loaders"]="books/extract_linkers_loaders.py|Gemini|Linkers & Loaders"
    ["os_three_pieces"]="books/extract_os_three_pieces.py|Grok|Operating Systems"
)

# Define required PDFs
declare -A PDF_FILES=(
    ["kernighan_ritchie"]="The C Programming Language (Kernighan Ritchie).pdf"
    ["unix_env"]="Advanced Programming in the UNIX Environment 3rd Edition.pdf"
    ["linkers_loaders"]="LinkersAndLoaders (1).pdf"
    ["os_three_pieces"]="Operating Systems - Three Easy Pieces.pdf"
)

echo -e "\n${BLUE}📚 Processor Script Verification${NC}"
TOTAL_PROCESSORS=0
WORKING_PROCESSORS=0

for processor_key in "${!PROCESSORS[@]}"; do
    TOTAL_PROCESSORS=$((TOTAL_PROCESSORS + 1))
    IFS='|' read -r script_path ai_model book_name <<< "${PROCESSORS[$processor_key]}"
    
    echo -e "\n${YELLOW}🔍 Checking: $book_name ($ai_model)${NC}"
    
    # Check script exists
    if [[ ! -f "$script_path" ]]; then
        echo -e "${RED}❌ Script missing: $script_path${NC}"
        continue
    fi
    echo -e "${GREEN}✅ Script found: $script_path${NC}"
    
    # Check PDF exists
    pdf_file="${PDF_FILES[$processor_key]}"
    if [[ ! -f "$pdf_file" ]]; then
        echo -e "${RED}❌ PDF missing: $pdf_file${NC}"
        continue
    fi
    echo -e "${GREEN}✅ PDF found: $pdf_file${NC}"
    
    # Check output directory
    output_dir="outputs/$processor_key"
    if [[ ! -d "$output_dir" ]]; then
        mkdir -p "$output_dir"
        echo -e "${YELLOW}⚠️  Created output directory: $output_dir${NC}"
    else
        echo -e "${GREEN}✅ Output directory exists: $output_dir${NC}"
    fi
    
    # Check progress file
    progress_file="$output_dir/progress.json"
    if [[ -f "$progress_file" ]]; then
        concepts_count=$(jq -r '.total_concepts_extracted // 0' "$progress_file" 2>/dev/null || echo "0")
        last_page=$(jq -r '.last_processed_page // 0' "$progress_file" 2>/dev/null || echo "0")
        echo -e "${GREEN}✅ Progress: $concepts_count concepts, page $last_page${NC}"
    else
        echo -e "${YELLOW}⚠️  No progress file (new processor)${NC}"
    fi
    
    # Test script syntax
    if python3 -m py_compile "$script_path" 2>/dev/null; then
        echo -e "${GREEN}✅ Script syntax valid${NC}"
        WORKING_PROCESSORS=$((WORKING_PROCESSORS + 1))
    else
        echo -e "${RED}❌ Script syntax error${NC}"
    fi
done

echo -e "\n${BLUE}📊 Verification Summary${NC}"
echo -e "${BLUE}=======================${NC}"
echo -e "📚 Total processors: $TOTAL_PROCESSORS"
echo -e "✅ Working processors: $WORKING_PROCESSORS"
echo -e "❌ Failed processors: $((TOTAL_PROCESSORS - WORKING_PROCESSORS))"

if [[ $WORKING_PROCESSORS -eq $TOTAL_PROCESSORS ]]; then
    echo -e "\n${GREEN}🎉 All processors verified successfully!${NC}"
    echo -e "${GREEN}Ready for automated twice-daily execution.${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  Some processors have issues. Fix them before automation.${NC}"
    exit 1
fi
