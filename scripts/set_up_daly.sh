#!/bin/bash
# Daily C Concept Extraction Automation Setup

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏛️  Setting up Daily C Concept Extraction Automation${NC}"
echo ""

# Get the current directory (project root)
PROJECT_DIR="$(pwd)"
VENV_PATH="$PROJECT_DIR/venv"
SCRIPT_PATH="$PROJECT_DIR/extract_c_concepts.py"
LOG_DIR="$PROJECT_DIR/logs"

# Verify project structure
echo -e "${YELLOW}🔍 Verifying project structure...${NC}"

if [[ ! -f "$SCRIPT_PATH" ]]; then
    echo -e "${RED}❌ extract_c_concepts.py not found in $PROJECT_DIR${NC}"
    exit 1
fi

if [[ ! -d "$VENV_PATH" ]]; then
    echo -e "${RED}❌ Virtual environment not found at $VENV_PATH${NC}"
    exit 1
fi

if [[ ! -f "$PROJECT_DIR/config.env" ]]; then
    echo -e "${RED}❌ config.env not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Project structure verified${NC}"

# Create logs directory
mkdir -p "$LOG_DIR"
echo -e "${GREEN}✅ Logs directory created: $LOG_DIR${NC}"

# Create the daily execution script
DAILY_SCRIPT="$PROJECT_DIR/run_daily_extraction.sh"

cat > "$DAILY_SCRIPT" << EOF
#!/bin/bash
# Daily C Concept Extraction Runner
# Generated on $(date)

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Run extraction with logging
echo "\$(date): Starting daily C concept extraction..." >> "$LOG_DIR/extraction.log"

python "$SCRIPT_PATH" >> "$LOG_DIR/daily_\$(date +%Y-%m-%d).log" 2>&1

# Check if extraction was successful
if [ \$? -eq 0 ]; then
    echo "\$(date): Daily extraction completed successfully" >> "$LOG_DIR/extraction.log"
else
    echo "\$(date): Daily extraction failed!" >> "$LOG_DIR/extraction.log"
fi

# Optional: Send notification (uncomment if you want email notifications)
# echo "Daily C extraction completed at \$(date)" | mail -s "C Concept Extraction" your-email@example.com
EOF

# Make the daily script executable
chmod +x "$DAILY_SCRIPT"
echo -e "${GREEN}✅ Daily execution script created: $DAILY_SCRIPT${NC}"

# Suggest cron job time
echo ""
echo -e "${BLUE}📅 Setting up daily automation...${NC}"
echo ""
echo "Choose your preferred daily extraction time:"
echo "1) 9:00 AM  (good for morning processing)"
echo "2) 6:00 PM  (good for after work)"
echo "3) 11:00 PM (good for overnight processing)"
echo "4) Custom time"
echo ""

read -p "Enter your choice (1-4): " time_choice

case $time_choice in
    1) CRON_TIME="0 9 * * *" ; TIME_DESC="9:00 AM daily" ;;
    2) CRON_TIME="0 18 * * *" ; TIME_DESC="6:00 PM daily" ;;
    3) CRON_TIME="0 23 * * *" ; TIME_DESC="11:00 PM daily" ;;
    4) 
        echo "Enter custom time in cron format (minute hour * * *):"
        echo "Examples: '30 14 * * *' for 2:30 PM, '0 8 * * *' for 8:00 AM"
        read -p "Cron time: " CRON_TIME
        TIME_DESC="custom time: $CRON_TIME"
        ;;
    *) 
        echo -e "${YELLOW}Invalid choice, defaulting to 9:00 AM${NC}"
        CRON_TIME="0 9 * * *"
        TIME_DESC="9:00 AM daily"
        ;;
esac

# Create cron job entry
CRON_ENTRY="$CRON_TIME $DAILY_SCRIPT"

echo ""
echo -e "${YELLOW}📋 Cron job configuration:${NC}"
echo "Schedule: $TIME_DESC"
echo "Command: $CRON_ENTRY"
echo ""

read -p "Do you want to install this cron job now? (y/n): " install_cron

if [[ $install_cron =~ ^[Yy]$ ]]; then
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo -e "${GREEN}✅ Cron job installed successfully!${NC}"
    echo ""
    echo -e "${BLUE}🔍 Verification:${NC}"
    echo "Current crontab entries:"
    crontab -l | grep -E "(extract_concepts|run_daily_extraction)" || echo "No extraction entries found"
else
    echo ""
    echo -e "${YELLOW}⚠️  Cron job not installed automatically.${NC}"
    echo "To install manually, run:"
    echo "crontab -e"
    echo "Then add this line:"
    echo "$CRON_ENTRY"
fi

echo ""
echo -e "${GREEN}🎉 Daily automation setup complete!${NC}"
echo ""
echo -e "${BLUE}📁 File locations:${NC}"
echo "- Extraction script: $SCRIPT_PATH"
echo "- Daily runner: $DAILY_SCRIPT"
echo "- Logs directory: $LOG_DIR"
echo "- Output directory: $PROJECT_DIR/summeries"
echo ""
echo -e "${BLUE}📊 Monitoring:${NC}"
echo "- Daily logs: $LOG_DIR/daily_YYYY-MM-DD.log"
echo "- General log: $LOG_DIR/extraction.log"
echo "- Daily summaries: $PROJECT_DIR/summeries/daily_summary_YYYY-MM-DD.md"
echo ""
echo -e "${BLUE}🔧 Management commands:${NC}"
echo "- View current cron jobs: crontab -l"
echo "- Edit cron jobs: crontab -e"
echo "- Remove cron job: crontab -e (then delete the line)"
echo "- Manual run: $DAILY_SCRIPT"
echo "- View logs: tail -f $LOG_DIR/extraction.log"
echo ""
echo -e "${GREEN}Your C programming knowledge will now be automatically extracted daily! 🚀${NC}"
