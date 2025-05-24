#!/bin/bash

# Quick Debug Script for Firebase Functions
# This script provides quick access to common debugging commands

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}🛠️  Firebase Functions Quick Debug${NC}"
    echo -e "${BLUE}================================================${NC}"
}

check_firebase_auth() {
    echo -e "${YELLOW}🔍 Checking Firebase authentication...${NC}"
    if firebase projects:list >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Firebase authenticated${NC}"
        current_project=$(firebase use --show 2>/dev/null || echo "none")
        echo -e "Current project: ${GREEN}$current_project${NC}"
    else
        echo -e "${RED}❌ Not authenticated with Firebase${NC}"
        echo -e "Run: ${YELLOW}firebase login${NC}"
        exit 1
    fi
}

show_functions() {
    echo -e "${YELLOW}📋 Listing deployed functions...${NC}"
    firebase functions:list
}

show_recent_logs() {
    local function_name=${1:-""}
    echo -e "${YELLOW}📜 Showing recent logs...${NC}"
    
    if [ -n "$function_name" ]; then
        echo -e "Filtering for function: ${GREEN}$function_name${NC}"
        firebase functions:log --only "$function_name" | tail -50
    else
        firebase functions:log | tail -50
    fi
}

follow_logs() {
    local function_name=${1:-""}
    echo -e "${YELLOW}👀 Monitoring logs (polling every 10 seconds)...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    
    while true; do
        clear
        echo -e "${BLUE}=== Latest Logs ($(date)) ===${NC}"
        
        if [ -n "$function_name" ]; then
            echo -e "Filtering for function: ${GREEN}$function_name${NC}"
            firebase functions:log --only "$function_name" -n 20
        else
            firebase functions:log -n 20
        fi
        
        echo -e "\n${YELLOW}Refreshing in 10 seconds... (Ctrl+C to stop)${NC}"
        sleep 10
    done
}

show_errors() {
    echo -e "${YELLOW}🔥 Showing recent errors...${NC}"
    firebase functions:log -n 100 | grep -i "error\|exception\|failed" | tail -20
}

open_logs_in_browser() {
    echo -e "${YELLOW}🌐 Opening logs in web browser...${NC}"
    firebase functions:log --open
}

deploy_function() {
    local function_name=${1:-""}
    
    if [ -n "$function_name" ]; then
        echo -e "${YELLOW}🚀 Deploying function: $function_name${NC}"
        firebase deploy --only "functions:$function_name"
    else
        echo -e "${YELLOW}🚀 Deploying all functions...${NC}"
        firebase deploy --only functions
    fi
}

test_locally() {
    echo -e "${YELLOW}🧪 Running local tests...${NC}"
    
    if [ ! -f "debug_functions.py" ]; then
        echo -e "${RED}❌ debug_functions.py not found${NC}"
        echo -e "Make sure you're in the functions directory"
        exit 1
    fi
    
    python debug_functions.py
}

start_emulator() {
    echo -e "${YELLOW}🏃 Starting Firebase emulator...${NC}"
    echo -e "${YELLOW}This will start all emulators. Press Ctrl+C to stop${NC}"
    firebase emulators:start
}

check_config() {
    echo -e "${YELLOW}⚙️ Checking Firebase Functions config...${NC}"
    firebase functions:config:get
}

show_menu() {
    echo -e "\n${BLUE}Select an option:${NC}"
    echo "1. Check Firebase auth & project"
    echo "2. List deployed functions"
    echo "3. Show recent logs"
    echo "4. Monitor logs (auto-refresh)"
    echo "5. Show recent errors"
    echo "6. Open logs in browser"
    echo "7. Deploy functions"
    echo "8. Test functions locally"
    echo "9. Start emulator"
    echo "10. Check function config"
    echo "11. Custom log filter"
    echo "0. Exit"
}

custom_log_filter() {
    echo -e "${YELLOW}🔍 Custom log filtering${NC}"
    echo "Enter search term (or press Enter for all logs):"
    read -r search_term
    
    echo "Enter function name (or press Enter for all functions):"
    read -r function_name
    
    if [ -n "$function_name" ]; then
        if [ -n "$search_term" ]; then
            firebase functions:log --only "$function_name" | grep -i "$search_term" | tail -30
        else
            firebase functions:log --only "$function_name" | tail -30
        fi
    else
        if [ -n "$search_term" ]; then
            firebase functions:log | grep -i "$search_term" | tail -30
        else
            firebase functions:log | tail -30
        fi
    fi
}

# Main script
main() {
    print_header
    
    # Check if we're in the right directory
    if [ ! -f "requirements.txt" ] || [ ! -d "../src" ]; then
        echo -e "${RED}❌ Please run this script from the functions/ directory${NC}"
        exit 1
    fi
    
    # Handle command line arguments
    case "${1:-}" in
        "auth"|"check")
            check_firebase_auth
            ;;
        "list"|"functions")
            check_firebase_auth
            show_functions
            ;;
        "logs")
            check_firebase_auth
            show_recent_logs "$2"
            ;;
        "follow")
            check_firebase_auth
            follow_logs "$2"
            ;;
        "errors")
            check_firebase_auth
            show_errors
            ;;
        "deploy")
            check_firebase_auth
            deploy_function "$2"
            ;;
        "test"|"local")
            test_locally
            ;;
        "emulator"|"emu")
            start_emulator
            ;;
        "config")
            check_firebase_auth
            check_config
            ;;
        "help"|"-h"|"--help")
            echo -e "${GREEN}Firebase Functions Debug Script${NC}"
            echo ""
            echo "Usage: $0 [command] [function_name]"
            echo ""
            echo "Commands:"
            echo "  auth, check          - Check Firebase authentication"
            echo "  list, functions      - List deployed functions"
            echo "  logs [function]      - Show recent logs (optionally for specific function)"
            echo "  follow [function]    - Monitor logs with auto-refresh"
            echo "  errors              - Show recent errors"
            echo "  deploy [function]    - Deploy functions"
            echo "  test, local         - Test functions locally"
            echo "  emulator, emu       - Start Firebase emulator"
            echo "  config              - Show functions config"
            echo "  help                - Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 logs find_leads   - Show logs for find_leads function"
            echo "  $0 follow            - Follow all function logs"
            echo "  $0 deploy find_leads - Deploy only find_leads function"
            ;;
        "")
            # Interactive mode
            check_firebase_auth
            
            while true; do
                show_menu
                echo -n "Enter your choice: "
                read -r choice
                
                case $choice in
                    1)
                        check_firebase_auth
                        ;;
                    2)
                        show_functions
                        ;;
                    3)
                        echo "Enter function name (or press Enter for all):"
                        read -r func_name
                        show_recent_logs "$func_name"
                        ;;
                    4)
                        echo "Enter function name (or press Enter for all):"
                        read -r func_name
                        follow_logs "$func_name"
                        ;;
                    5)
                        show_errors
                        ;;
                    6)
                        open_logs_in_browser
                        ;;
                    7)
                        echo "Enter function name (or press Enter for all):"
                        read -r func_name
                        deploy_function "$func_name"
                        ;;
                    8)
                        test_locally
                        ;;
                    9)
                        start_emulator
                        ;;
                    10)
                        check_config
                        ;;
                    11)
                        custom_log_filter
                        ;;
                    0)
                        echo -e "${GREEN}👋 Goodbye!${NC}"
                        exit 0
                        ;;
                    *)
                        echo -e "${RED}❌ Invalid choice. Please try again.${NC}"
                        ;;
                esac
                
                echo -e "\n${YELLOW}Press Enter to continue...${NC}"
                read -r
            done
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $1${NC}"
            echo -e "Run ${YELLOW}$0 help${NC} for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 