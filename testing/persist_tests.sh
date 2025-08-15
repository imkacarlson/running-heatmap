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
    
    echo -e "${BLUE}Setting up emulator and Appium services...${NC}"
    python "$SCRIPT_DIR/service_manager.py" --setup
    
    if [ $? -eq 0 ]; then
        echo
        echo -e "${GREEN}✅ Persistent infrastructure is now running!${NC}"
        echo
        echo -e "${YELLOW}📋 Usage:${NC}"
        echo -e "   ${GREEN}./test.sh${NC}                    # Run tests against persistent infrastructure"
        echo -e "   ${GREEN}./persist_tests.sh status${NC}    # Check infrastructure status"
        echo -e "   ${GREEN}./persist_tests.sh stop${NC}      # Stop persistent infrastructure"
        echo
        echo -e "${YELLOW}💡 The emulator and Appium server will remain running for faster subsequent test runs${NC}"
        echo -e "${YELLOW}   Use './persist_tests.sh stop' when you're done testing${NC}"
        return 0
    else
        echo
        echo -e "${RED}❌ Failed to start persistent infrastructure${NC}"
        echo -e "${YELLOW}💡 Check the error messages above and try again${NC}"
        return 1
    fi
}

stop_infrastructure() {
    print_header
    echo -e "${YELLOW}🔌 Stopping persistent test infrastructure...${NC}"
    echo
    
    check_dependencies
    activate_venv
    
    echo -e "${BLUE}Cleaning up emulator and Appium services...${NC}"
    python "$SCRIPT_DIR/service_manager.py" --cleanup
    
    echo
    echo -e "${GREEN}✅ Persistent infrastructure stopped${NC}"
    echo -e "${YELLOW}💡 Run './persist_tests.sh start' to restart persistent infrastructure${NC}"
}

check_status() {
    print_header
    echo -e "${BLUE}📊 Checking persistent infrastructure status...${NC}"
    echo
    
    check_dependencies
    activate_venv
    
    python "$SCRIPT_DIR/service_manager.py" --status
    
    if [ $? -eq 0 ]; then
        echo
        echo -e "${GREEN}✅ Infrastructure is healthy and ready for testing${NC}"
        echo -e "${YELLOW}💡 Run './test.sh' to execute tests against this infrastructure${NC}"
    else
        echo
        echo -e "${YELLOW}⚠️  Infrastructure needs attention${NC}"
        echo -e "${YELLOW}💡 Try './persist_tests.sh restart' to fix issues${NC}"
    fi
}

restart_infrastructure() {
    print_header
    echo -e "${BLUE}🔄 Restarting persistent test infrastructure...${NC}"
    echo
    
    check_dependencies
    activate_venv
    
    echo -e "${BLUE}Checking for unhealthy services...${NC}"
    python "$SCRIPT_DIR/service_manager.py" --restart
    
    if [ $? -eq 0 ]; then
        echo
        echo -e "${GREEN}✅ Infrastructure restart complete${NC}"
        echo -e "${YELLOW}💡 Services should now be healthy and ready for testing${NC}"
    else
        echo
        echo -e "${RED}❌ Failed to restart infrastructure${NC}"
        echo -e "${YELLOW}💡 Try './persist_tests.sh stop' and then './persist_tests.sh start'${NC}"
    fi
}

health_check() {
    check_dependencies
    activate_venv
    
    echo -e "${BLUE}🏥 Performing health check on services...${NC}"
    python "$SCRIPT_DIR/service_manager.py" --health-check
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ All services are healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  Some services have health issues${NC}"
    fi
}

show_usage() {
    print_header
    echo
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "   ${GREEN}./persist_tests.sh start${NC}     # Start persistent infrastructure (emulator + Appium)"
    echo -e "   ${GREEN}./persist_tests.sh stop${NC}      # Stop persistent infrastructure"
    echo -e "   ${GREEN}./persist_tests.sh status${NC}    # Check infrastructure status"
    echo -e "   ${GREEN}./persist_tests.sh restart${NC}   # Restart unhealthy services"
    echo -e "   ${GREEN}./persist_tests.sh health${NC}    # Perform health check"
    echo -e "   ${GREEN}./persist_tests.sh cleanup${NC}   # Force cleanup all services"
    echo
    echo -e "${YELLOW}Description:${NC}"
    echo -e "   This script manages persistent test infrastructure for faster test iterations."
    echo -e "   Unlike './test.sh' which sets up and tears down services for each run,"
    echo -e "   persistent mode keeps emulator and Appium running between test sessions."
    echo
    echo -e "${YELLOW}Benefits:${NC}"
    echo -e "   • Faster test execution (no emulator startup time)"
    echo -e "   • Consistent test environment"
    echo -e "   • Reduced CI/CD pipeline time"
    echo
    echo -e "${YELLOW}Workflow:${NC}"
    echo -e "   1. ${GREEN}./persist_tests.sh start${NC}    # Start persistent services"
    echo -e "   2. ${GREEN}./test.sh${NC}                   # Run tests (will use persistent services)"
    echo -e "   3. ${GREEN}./test.sh${NC}                   # Run tests again (faster, services already running)"
    echo -e "   4. ${GREEN}./persist_tests.sh stop${NC}     # Stop persistent services when done"
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