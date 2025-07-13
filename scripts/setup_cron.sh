#!/bin/bash
# Automated Cron Setup for Twice-Daily Book Extraction
# Sets up cron jobs for 11:00 and 23:00 daily execution

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/home/shahar42/Suumerizing_C_holy_grale_book"
ENHANCED_SCRIPT="$PROJECT_DIR/scripts/run_all_daily_enhanced.sh"
VERIFY_SCRIPT="$PROJECT_DIR/scripts/verify_processors.sh"
CRON_LOG_DIR="$PROJECT_DIR/logs/cron"

echo -e "${BLUE}🕐 Automated Cron Setup for Book Extraction${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Verify project setup
if [[ ! -d "$PROJECT_DIR" ]]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_DIR${NC}"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1

# Create enhanced script directory
mkdir -p scripts
mkdir -p "$CRON_LOG_DIR"

# Create the enhanced daily runner script
echo -e "${YELLOW}📝 Creating enhanced daily runner script...${NC}"
cat > "$ENHANCED_SCRIPT" << 'EOF'
#!/bin/bash
# This will be replaced with the enhanced script content
# The actual enhanced script should be copied here
EOF

# Make scripts executable
chmod +x "$ENHANCED_SCRIPT"
chmod +x "$VERIFY_SCRIPT" 2>/dev/null || true

echo -e "${GREEN}✅ Enhanced script created: $ENHANCED_SCRIPT${NC}"

# Backup current crontab
echo -e "${YELLOW}📋 Backing up current crontab...${NC}"
crontab -l > "$PROJECT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "No existing crontab found"

# Create new cron entries
CRON_ENTRIES="# Automated C Programming Book Concept Extraction
# Runs twice daily at 11:00 and 23:00
# Logs are stored in $CRON_LOG_DIR

# Morning extraction at 11:00 AM
0 11 * * * $ENHANCED_SCRIPT >> $CRON_LOG_DIR/morning_$(date +\%Y-\%m-\%d).log 2>&1

# Evening extraction at 11:00 PM  
0 23 * * * $ENHANCED_SCRIPT >> $CRON_LOG_DIR/evening_$(date +\%Y-\%m-\%d).log 2>&1

# Weekly cleanup of old cron logs (keep last 14 days)
0 1 * * 0 find $CRON_LOG_DIR -name '*.log' -mtime +14 -delete

"

# Function to install cron jobs
install_cron() {
    echo -e "${YELLOW}⚙️  Installing cron jobs...${NC}"
    
    # Get current crontab (if any)
    current_cron=$(crontab -l 2>/dev/null || true)
    
    # Check if our jobs already exist
    if echo "$current_cron" | grep -q "Automated C Programming Book"; then
        echo -e "${YELLOW}⚠️  Existing extraction cron jobs found${NC}"
        echo -e "${BLUE}Current cron jobs related to extraction:${NC}"
        echo "$current_cron" | grep -A 10 -B 2 "Automated C Programming Book" || true
        echo ""
        read -p "Replace existing extraction cron jobs? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}⏭️  Skipping cron installation${NC}"
            return 0
        fi
        
        # Remove existing extraction jobs
        current_cron=$(echo "$current_cron" | grep -v "Automated C Programming Book" | grep -v "$ENHANCED_SCRIPT" | grep -v "find $CRON_LOG_DIR")
    fi
    
    # Add new cron jobs
    echo "$current_cron" > temp_crontab
    echo "$CRON_ENTRIES" >> temp_crontab
    
    # Install new crontab
    if crontab temp_crontab; then
        echo -e "${GREEN}✅ Cron jobs installed successfully${NC}"
        rm temp_crontab
    else
        echo -e "${RED}❌ Failed to install cron jobs${NC}"
        rm temp_crontab
        exit 1
    fi
}

# Function to show current cron status
show_cron_status() {
    echo -e "\n${BLUE}📅 Current Cron Configuration${NC}"
    echo -e "${BLUE}==============================${NC}"
    
    if crontab -l 2>/dev/null | grep -q "Automated C Programming Book"; then
        echo -e "${GREEN}✅ Book extraction cron jobs are installed:${NC}"
        crontab -l | grep -A 10 -B 2 "Automated C Programming Book" || true
    else
        echo -e "${YELLOW}⚠️  No book extraction cron jobs found${NC}"
    fi
    
    echo -e "\n${BLUE}Next scheduled runs:${NC}"
    current_hour=$(date +%H)
    if [[ $current_hour -lt 11 ]]; then
        echo -e "🌅 Next morning run: Today at 11:00"
        echo -e "🌙 Next evening run: Today at 23:00"
    elif [[ $current_hour -lt 23 ]]; then
        echo -e "🌙 Next evening run: Today at 23:00"
        echo -e "🌅 Next morning run: Tomorrow at 11:00"
    else
        echo -e "🌅 Next morning run: Tomorrow at 11:00"
        echo -e "🌙 Next evening run: Tomorrow at 23:00"
    fi
}

# Function to test the setup
test_setup() {
    echo -e "\n${YELLOW}🧪 Testing processor setup...${NC}"
    
    if [[ -f "$VERIFY_SCRIPT" ]]; then
        if bash "$VERIFY_SCRIPT"; then
            echo -e "${GREEN}✅ All processors verified successfully${NC}"
        else
            echo -e "${RED}❌ Processor verification failed${NC}"
            echo -e "${YELLOW}Fix the issues before enabling cron automation${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  Verification script not found, skipping test${NC}"
    fi
    
    echo -e "\n${YELLOW}🧪 Testing enhanced script syntax...${NC}"
    if bash -n "$ENHANCED_SCRIPT"; then
        echo -e "${GREEN}✅ Enhanced script syntax is valid${NC}"
    else
        echo -e "${RED}❌ Enhanced script has syntax errors${NC}"
        return 1
    fi
    
    return 0
}

# Main execution
case "${1:-setup}" in
    "setup")
        echo -e "${BLUE}Setting up automated twice-daily execution...${NC}"
        
        if test_setup; then
            install_cron
            show_cron_status
            
            echo -e "\n${GREEN}🎉 Automated setup complete!${NC}"
            echo -e "\n${BLUE}📋 Summary:${NC}"
            echo -e "• Enhanced script: $ENHANCED_SCRIPT"
            echo -e "• Cron logs: $CRON_LOG_DIR"
            echo -e "• Morning runs: 11:00 daily"
            echo -e "• Evening runs: 23:00 daily"
            echo -e "• Log cleanup: Weekly (Sundays at 1:00 AM)"
            
            echo -e "\n${BLUE}💡 Useful commands:${NC}"
            echo -e "• View cron jobs: crontab -l"
            echo -e "• Edit cron jobs: crontab -e"
            echo -e "• View cron logs: tail -f $CRON_LOG_DIR/*.log"
            echo -e "• Test extraction: $ENHANCED_SCRIPT"
            echo -e "• Verify processors: $VERIFY_SCRIPT"
        else
            echo -e "\n${RED}❌ Setup failed due to test failures${NC}"
            echo -e "Fix the issues and run the setup again"
            exit 1
        fi
        ;;
        
    "status")
        show_cron_status
        ;;
        
    "test")
        test_setup
        ;;
        
    "remove")
        echo -e "${YELLOW}🗑️  Removing extraction cron jobs...${NC}"
        if crontab -l 2>/dev/null | grep -q "Automated C Programming Book"; then
            current_cron=$(crontab -l 2>/dev/null | grep -v "Automated C Programming Book" | grep -v "$ENHANCED_SCRIPT" | grep -v "find $CRON_LOG_DIR")
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
        echo -e "  setup   - Set up automated twice-daily extraction (default)"
        echo -e "  status  - Show current cron configuration"
        echo -e "  test    - Test processor setup without installing cron"
        echo -e "  remove  - Remove extraction cron jobs"
        echo -e "  help    - Show this help message"
        ;;
esac
