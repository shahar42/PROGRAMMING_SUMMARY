#!/bin/bash
# Automated Cron Setup for 5-Book Extraction System
# Updated with Expert C Programming + GPT-4.1 Nano integration
# Sets up cron jobs for 11:00 and 23:00 daily execution

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/home/shahar42/Suumerizing_C_holy_grale_book"
MASTER_SCRIPT="$PROJECT_DIR/scripts/run_all_daily.sh"
CRON_LOG_DIR="$PROJECT_DIR/logs/cron"

echo -e "${BLUE}🕐 Updated Cron Setup for 5-Book Extraction System${NC}"
echo -e "${BLUE}===================================================${NC}"
echo -e "${GREEN}Now includes: Expert C Programming + GPT-4.1 Nano${NC}"
echo ""

# Verify project setup
if [[ ! -d "$PROJECT_DIR" ]]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_DIR${NC}"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1

# Create cron log directory
mkdir -p "$CRON_LOG_DIR"

# Verify master script exists
if [[ ! -f "$MASTER_SCRIPT" ]]; then
    echo -e "${RED}❌ Master script not found: $MASTER_SCRIPT${NC}"
    echo -e "${YELLOW}📝 Please ensure the updated master script is in place${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Master script found with 5-book configuration${NC}"

# Backup current crontab
echo -e "${YELLOW}📋 Backing up current crontab...${NC}"
crontab -l > "$PROJECT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "No existing crontab found"

# Create new cron entries with updated paths
CRON_ENTRIES="# Automated C Programming Book Concept Extraction
# Updated for 5 books: K&R, UNIX, Linkers, OS, Expert C
# AI Models: Gemini, Grok, GPT-4.1 Nano
# Runs twice daily at 11:00 and 23:00
# Logs are stored in $CRON_LOG_DIR

# Morning extraction at 11:00 AM
0 11 * * * cd $PROJECT_DIR && $MASTER_SCRIPT >> $CRON_LOG_DIR/morning_\$(date +\\%Y-\\%m-\\%d).log 2>&1

# Evening extraction at 11:00 PM  
0 23 * * * cd $PROJECT_DIR && $MASTER_SCRIPT >> $CRON_LOG_DIR/evening_\$(date +\\%Y-\\%m-\\%d).log 2>&1

# Weekly cleanup of old cron logs (keep last 14 days)
0 1 * * 0 find $CRON_LOG_DIR -name '*.log' -mtime +14 -delete

# Monthly API usage summary report
0 9 1 * * echo \"Monthly extraction report for \$(date +'\\%B \\%Y')\" | mail -s \"5-Book Extraction Monthly Report\" your-email@domain.com

"

# Function to install cron jobs
install_cron() {
    echo -e "${YELLOW}⚙️  Installing updated 5-book cron jobs...${NC}"
    
    # Get current crontab (if any)
    current_cron=$(crontab -l 2>/dev/null || true)
    
    # Check if our jobs already exist
    if echo "$current_cron" | grep -q "Automated C Programming Book"; then
        echo -e "${YELLOW}⚠️  Existing extraction cron jobs found${NC}"
        echo -e "${BLUE}Current cron jobs related to extraction:${NC}"
        echo "$current_cron" | grep -A 10 -B 2 "Automated C Programming Book" || true
        echo ""
        read -p "Replace existing extraction cron jobs with 5-book version? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}⏭️  Skipping cron installation${NC}"
            return 0
        fi
        
        # Remove existing extraction jobs
        current_cron=$(echo "$current_cron" | grep -v "Automated C Programming Book" | grep -v "$MASTER_SCRIPT" | grep -v "find $CRON_LOG_DIR")
    fi
    
    # Add new cron jobs
    echo "$current_cron" > temp_crontab
    echo "$CRON_ENTRIES" >> temp_crontab
    
    # Install new crontab
    if crontab temp_crontab; then
        echo -e "${GREEN}✅ 5-book cron jobs installed successfully${NC}"
        rm temp_crontab
    else
        echo -e "${RED}❌ Failed to install cron jobs${NC}"
        rm temp_crontab
        exit 1
    fi
}

# Function to show current cron status
show_cron_status() {
    echo -e "\n${BLUE}📅 Current 5-Book Cron Configuration${NC}"
    echo -e "${BLUE}====================================${NC}"
    
    if crontab -l 2>/dev/null | grep -q "Automated C Programming Book"; then
        echo -e "${GREEN}✅ 5-book extraction cron jobs are installed:${NC}"
        crontab -l | grep -A 15 -B 2 "Automated C Programming Book" || true
    else
        echo -e "${YELLOW}⚠️  No book extraction cron jobs found${NC}"
    fi
    
    echo -e "\n${BLUE}📚 Books in daily automation:${NC}"
    echo -e "  1. K&R C Programming (Gemini)"
    echo -e "  2. UNIX Environment (Grok)" 
    echo -e "  3. Linkers & Loaders (Gemini)"
    echo -e "  4. Operating Systems (Grok)"
    echo -e "  5. ${GREEN}Expert C Programming (GPT-4.1 Nano)${NC} ← NEW"
    
    echo -e "\n${BLUE}Next scheduled runs:${NC}"
    current_hour=$(date +%H)
    if [[ $current_hour -lt 11 ]]; then
        echo -e "🌅 Next morning run: Today at 11:00 (all 5 books)"
        echo -e "🌙 Next evening run: Today at 23:00 (all 5 books)"
    elif [[ $current_hour -lt 23 ]]; then
        echo -e "🌙 Next evening run: Today at 23:00 (all 5 books)"
        echo -e "🌅 Next morning run: Tomorrow at 11:00 (all 5 books)"
    else
        echo -e "🌅 Next morning run: Tomorrow at 11:00 (all 5 books)"
        echo -e "🌙 Next evening run: Tomorrow at 23:00 (all 5 books)"
    fi
}

# Function to test the 5-book setup
test_5_book_setup() {
    echo -e "\n${YELLOW}🧪 Testing 5-book extraction setup...${NC}"
    
    # Test API keys
    if [[ -f "config/config.env" ]]; then
        source "config/config.env"
        api_count=0
        
        if [[ -n "${GEMINI_API_KEY:-}" ]]; then
            echo -e "${GREEN}✅ Gemini API key configured${NC}"
            api_count=$((api_count + 1))
        else
            echo -e "${RED}❌ Gemini API key missing${NC}"
        fi
        
        if [[ -n "${GROK_API_KEY:-}" ]]; then
            echo -e "${GREEN}✅ Grok API key configured${NC}"
            api_count=$((api_count + 1))
        else
            echo -e "${RED}❌ Grok API key missing${NC}"
        fi
        
        if [[ -n "${OPENAI_API_KEY:-}" ]]; then
            echo -e "${GREEN}✅ OpenAI API key configured${NC}"
            api_count=$((api_count + 1))
        else
            echo -e "${RED}❌ OpenAI API key missing${NC}"
        fi
        
        echo -e "${BLUE}📊 API Status: $api_count/3 configured${NC}"
    else
        echo -e "${RED}❌ Config file missing${NC}"
    fi
    
    # Test book extractors
    book_count=0
    extractors=(
        "books/extract_c_concepts.py"
        "books/extract_unix_env.py"
        "books/extract_linkers_loaders.py"
        "books/extract_os_three_pieces.py"
        "books/extract_Expert_C_Programming.py"
    )
    
    echo -e "\n${YELLOW}📚 Checking book extractors...${NC}"
    for extractor in "${extractors[@]}"; do
        if [[ -f "$extractor" ]]; then
            echo -e "${GREEN}✅ $(basename "$extractor")${NC}"
            book_count=$((book_count + 1))
        else
            echo -e "${RED}❌ $(basename "$extractor")${NC}"
        fi
    done
    
    echo -e "${BLUE}📊 Extractor Status: $book_count/5 available${NC}"
    
    # Test master script syntax
    echo -e "\n${YELLOW}🧪 Testing master script syntax...${NC}"
    if bash -n "$MASTER_SCRIPT"; then
        echo -e "${GREEN}✅ Master script syntax is valid${NC}"
    else
        echo -e "${RED}❌ Master script has syntax errors${NC}"
        return 1
    fi
    
    if [[ $api_count -eq 3 && $book_count -eq 5 ]]; then
        echo -e "\n${GREEN}🎉 5-book setup is complete and ready!${NC}"
        return 0
    else
        echo -e "\n${YELLOW}⚠️  Setup incomplete - fix missing components${NC}"
        return 1
    fi
}

# Main execution
case "${1:-setup}" in
    "setup")
        echo -e "${BLUE}Setting up automated 5-book extraction...${NC}"
        
        if test_5_book_setup; then
            install_cron
            show_cron_status
            
            echo -e "\n${GREEN}🎉 5-Book automated setup complete!${NC}"
            echo -e "\n${BLUE}📋 Summary:${NC}"
            echo -e "• Master script: $MASTER_SCRIPT"
            echo -e "• Cron logs: $CRON_LOG_DIR"
            echo -e "• Morning runs: 11:00 daily (all 5 books)"
            echo -e "• Evening runs: 23:00 daily (all 5 books)"
            echo -e "• Log cleanup: Weekly (Sundays at 1:00 AM)"
            echo -e "• NEW: Expert C Programming with GPT-4.1 Nano"
            
            echo -e "\n${BLUE}💡 Useful commands:${NC}"
            echo -e "• View cron jobs: crontab -l"
            echo -e "• Edit cron jobs: crontab -e"
            echo -e "• View cron logs: tail -f $CRON_LOG_DIR/*.log"
            echo -e "• Test 5-book extraction: $MASTER_SCRIPT"
        else
            echo -e "\n${RED}❌ Setup failed due to missing components${NC}"
            echo -e "Fix the issues and run the setup again"
            exit 1
        fi
        ;;
        
    "status")
        show_cron_status
        ;;
        
    "test")
        test_5_book_setup
        ;;
        
    "remove")
        echo -e "${YELLOW}🗑️  Removing extraction cron jobs...${NC}"
        if crontab -l 2>/dev/null | grep -q "Automated C Programming Book"; then
            current_cron=$(crontab -l 2>/dev/null | grep -v "Automated C Programming Book" | grep -v "$MASTER_SCRIPT" | grep -v "find $CRON_LOG_DIR")
            echo "$current_cron" | crontab -
            echo -e "${GREEN}✅ Extraction cron jobs removed${NC}"
        else
            echo -e "${YELLOW}⚠️  No extraction cron jobs found to remove${NC}"
        fi
        ;;
        
    "help"|*)
        echo -e "${BLUE}Usage: $0 [command]${NC}"
        echo ""
        echo -e "${BLUE}Commands:${NC}"
        echo -e "  setup   - Set up automated 5-book extraction (default)"
        echo -e "  status  - Show current cron configuration"
        echo -e "  test    - Test 5-book setup without installing cron"
        echo -e "  remove  - Remove extraction cron jobs"
        echo -e "  help    - Show this help message"
        echo ""
        echo -e "${BLUE}5-Book System:${NC}"
        echo -e "  1. K&R C Programming (Gemini)"
        echo -e "  2. UNIX Environment (Grok)"
        echo -e "  3. Linkers & Loaders (Gemini)"
        echo -e "  4. Operating Systems (Grok)"
        echo -e "  5. Expert C Programming (GPT-4.1 Nano)"
        ;;
esac
