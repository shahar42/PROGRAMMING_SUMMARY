# 🚀 Automated C++ STL Extraction System

## 📋 System Overview
- **Book**: C++ Standard LibraryContainers.pdf  
- **Pages**: 37-407 (370 pages total)
- **Batch Size**: 20 concepts per session
- **Interval**: Every 20 minutes
- **Estimated Total Time**: ~6 hours (18 batches × 20 minutes)

## 🎯 Quick Start

### Start Automated Extraction
```bash
# Option 1: Interactive (recommended for first run)
python3 stl_control.py start

# Option 2: Background process
./start_stl_background.sh
```

### Monitor Progress
```bash
# Check current status
python3 stl_control.py status

# View recent logs
python3 stl_control.py logs

# Show all commands
python3 stl_control.py help
```

### Stop Extraction
```bash
# If running interactively: Ctrl+C
# If running in background: 
kill $(cat cpp_stl_extraction.pid)
```

## 📁 Output Files

### Generated Concepts
- **Location**: `outputs/cpp_stl_containers/`
- **Format**: `concept_XXX_YY.json` 
- **Content**: STL-focused C++ concepts with code examples

### Tracking Files
- **Progress**: `cpp_stl_progress.json` - Current extraction state
- **Logs**: `cpp_stl_extraction.log` - Detailed extraction logs
- **PID**: `cpp_stl_extraction.pid` - Background process ID

## 🔧 Control Commands

| Command | Description |
|---------|-------------|
| `python3 stl_control.py status` | Show extraction progress |
| `python3 stl_control.py start` | Start interactive extraction |
| `python3 stl_control.py logs` | View recent log entries |
| `python3 stl_control.py reset` | Reset to page 37 (⚠️ destructive) |
| `./start_stl_background.sh` | Start background extraction |

## 📊 Expected Output Quality

### Concept Examples
- **std::vector push_back Operation**
- **Range-based for loops with containers**
- **std::sort with custom comparators**
- **Smart pointer RAII patterns**
- **Iterator arithmetic and types**

### Quality Standards
- ✅ **Modern C++**: Uses std:: prefix, auto, range-based loops
- ✅ **Complete Code**: Compilable examples with proper headers
- ✅ **STL-Focused**: Avoids basic C++ syntax, focuses on containers/algorithms
- ✅ **Practical**: Realistic use cases, not contrived examples
- ✅ **Documented**: Clear explanations of what/why/how

## 🛡️ Safety Features

### Error Handling
- **API Rate Limiting**: 2-second delays between calls
- **Retry Logic**: Automatic retry on failures
- **Graceful Shutdown**: Ctrl+C saves progress
- **Resumable**: Continues from last page on restart

### Progress Tracking
- **Page-by-page**: Tracks exactly which pages are processed
- **Deduplication**: Avoids creating duplicate concepts
- **Timestamped**: All extractions have metadata
- **Validated**: Ensures STL focus and code quality

## 🔍 Monitoring

### Real-time Status
```bash
# Quick status check
python3 stl_control.py status

# Expected output:
# 📊 C++ STL EXTRACTION STATUS
# 📄 Pages: 45/407 (2.2% complete)
# 🎯 Concepts extracted: 40
# 📦 Current batch: 3
# ⏰ Estimated time remaining: ~300 minutes
```

### Log Monitoring
```bash
# View recent activity
python3 stl_control.py logs

# Or watch live (if running interactively)
tail -f cpp_stl_extraction.log
```

## 🎉 Completion

When finished, you'll have:
- **~370 STL concepts** extracted from the book
- **High-quality JSON files** ready for MCP server integration
- **Complete extraction logs** for review
- **Progress file** showing 100% completion

The system will automatically stop when reaching page 407.

## 🚨 Troubleshooting

### Common Issues
1. **API Key Error**: Check `config/config.env` has valid `GEMINI_API_KEY`
2. **PDF Not Found**: Ensure `C++ Standard LibraryContainers.pdf` is in root directory
3. **Permission Error**: Run `chmod +x *.py *.sh` to make scripts executable
4. **Import Error**: Run from project root directory

### Recovery
```bash
# If extraction stops unexpectedly, just restart:
python3 stl_control.py start

# The system will resume from the last saved page
```