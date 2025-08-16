#!/bin/bash
set -e

# Persistent test infrastructure management script
# Provides optional persistent service mode for multiple test runs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service management functions
print_header() {
    echo -e "${BLUE}🔧 Persistent Test Infrastructure Manager${NC}"
    echo -e "${BLUE}==============================================${NC}"
}

check_dependencies() {
    echo -e "${BLUE}🔍 Checking dependencies...${NC}"
    
    # Check if virtual environment exists
    if [ ! -d "$SCRIPT_DIR/test_venv" ]; then
        echo -e "${RED}❌ Test virtual environment not found at $SCRIPT_DIR/test_venv${NC}"
        echo -e "${YELLOW}💡 Please run setup first or check your environment setup${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependencies check complete${NC}"
}

activate_venv() {
    echo -e "${BLUE}🐍 Activating Python virtual environment...${NC}"
    source "$SCRIPT_DIR/test_venv/bin/activate"
}

start_infrastructure() {
    print_header
    echo -e "${GREEN}🚀 Starting persistent test infrastructure...${NC}"
    echo
    
    check_dependencies
    activate_venv
    
    echo -e "${BLUE}Starting persistent infrastructure using proven working setup...${NC}"
    python "$SCRIPT_DIR/persist_infrastructure.py"
    
    return $?
}

stop_infrastructure() {
    print_header
    echo -e "${YELLOW}🔌 Stopping persistent test infrastructure...${NC}"
    echo
    
    echo -e "${BLUE}Stopping persistent infrastructure...${NC}"
    echo -e "${YELLOW}💡 Infrastructure will stop when you press Enter or Ctrl+C in the running terminal${NC}"
    echo -e "${YELLOW}💡 If no infrastructure is running, there's nothing to stop${NC}"
    echo
    echo -e "${GREEN}✅ Stop command completed${NC}"
}

check_status() {
    print_header
    echo -e "${BLUE}📊 Checking persistent infrastructure status...${NC}"
    echo
    
    echo -e "${BLUE}Checking for running infrastructure...${NC}"
    
    # Check for emulator
    if adb devices 2>/dev/null | grep -q "emulator.*device"; then
        echo -e "${GREEN}✅ Emulator: Running${NC}"
        EMULATOR_RUNNING=1
    else
        echo -e "${RED}❌ Emulator: Not running${NC}"
        EMULATOR_RUNNING=0
    fi
    
    # Check for Appium
    if curl -s http://localhost:4723/wd/hub/status 2>/dev/null | grep -q "ready"; then
        echo -e "${GREEN}✅ Appium: Running${NC}"
        APPIUM_RUNNING=1
    else
        echo -e "${RED}❌ Appium: Not running${NC}"
        APPIUM_RUNNING=0
    fi
    
    echo
    if [ "${EMULATOR_RUNNING}" -eq 1 ] && [ "${APPIUM_RUNNING}" -eq 1 ]; then
        echo -e "${GREEN}✅ Infrastructure is healthy and ready for testing${NC}"
        echo -e "${YELLOW}💡 Run './test.sh' to execute tests against this infrastructure${NC}"
    else
        echo -e "${YELLOW}⚠️  Infrastructure is not fully running${NC}"
        echo -e "${YELLOW}💡 Run './persist_tests.sh start' to start persistent infrastructure${NC}"
    fi
}

restart_infrastructure() {
    print_header
    echo -e "${BLUE}🔄 Restarting persistent test infrastructure...${NC}"
    echo
    
    echo -e "${BLUE}Restarting infrastructure...${NC}"
    echo -e "${YELLOW}💡 To restart infrastructure:${NC}"
    echo -e "${YELLOW}   1. Press Enter or Ctrl+C in the running infrastructure terminal${NC}"
    echo -e "${YELLOW}   2. Run './persist_tests.sh start' to start fresh infrastructure${NC}"
    echo
    echo -e "${GREEN}✅ Restart instructions provided${NC}"
}

health_check() {
    echo -e "${BLUE}🏥 Performing health check on services...${NC}"
    
    # Delegate to status check since it does the same thing
    check_status
}

show_usage() {
    print_header
    echo
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "   ${GREEN}./persist_tests.sh start${NC}     # Start persistent infrastructure (emulator + Appium)"
    echo -e "   ${GREEN}./persist_tests.sh stop${NC}      # Show instructions to stop persistent infrastructure"
    echo -e "   ${GREEN}./persist_tests.sh status${NC}    # Check infrastructure status"
    echo -e "   ${GREEN}./persist_tests.sh restart${NC}   # Show instructions to restart infrastructure"
    echo -e "   ${GREEN}./persist_tests.sh health${NC}    # Perform health check"
    echo -e "   ${GREEN}./persist_tests.sh cleanup${NC}   # Show instructions to stop infrastructure"
    echo
    echo -e "${YELLOW}Description:${NC}"
    echo -e "   This script manages persistent test infrastructure for faster test iterations."
    echo -e "   Uses the proven working setup code from './test.sh' for maximum reliability."
    echo -e "   Infrastructure runs in an interactive terminal that stays open until stopped."
    echo
    echo -e "${YELLOW}Benefits:${NC}"
    echo -e "   • Faster test execution (no emulator startup time)"
    echo -e "   • Consistent test environment"
    echo -e "   • Uses same working setup as './test.sh'"
    echo -e "   • Simple interactive control"
    echo
    echo -e "${YELLOW}Workflow:${NC}"
    echo -e "   1. ${GREEN}./persist_tests.sh start${NC}    # Start persistent services (keeps terminal open)"
    echo -e "   2. ${GREEN}./test.sh${NC}                   # Run tests in other terminals (faster execution)"
    echo -e "   3. ${GREEN}./test.sh${NC}                   # Run tests again (even faster, services running)"
    echo -e "   4. Press ${GREEN}Enter${NC} or ${GREEN}Ctrl+C${NC} in infrastructure terminal to stop"
    echo
}

# Main command processing
case "${1:-}" in
    start)
        start_infrastructure
        ;;
    stop)
        stop_infrastructure
        ;;
    status)
        check_status
        ;;
    restart)
        restart_infrastructure
        ;;
    health)
        health_check
        ;;
    cleanup)
        stop_infrastructure
        ;;
    help|--help|-h)
        show_usage
        ;;
    "")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo
        show_usage
        exit 1
        ;;
esac