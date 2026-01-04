#!/bin/bash

# Workflow Configuration Assistant
# 此脚本帮助快速准备 GitHub Actions Secret

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}RikkaHub Workflow Configuration Assistant${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Function to prompt user
prompt_input() {
    local prompt_text=$1
    local response
    read -p "$(echo -e ${YELLOW}${prompt_text}${NC})" response
    echo "$response"
}

echo -e "${BLUE}Note: Only ONE secret is needed: KEY_BASE64${NC}"
echo -e "${BLUE}      Other configurations are automated!${NC}"
echo ""

# Check if keystore exists
echo -e "${YELLOW}Step 1: Generate KEY_BASE64 Secret${NC}"
echo ""

KEYSTORE_FILE=$(prompt_input "Enter keystore file path (default: rikkahub.jks): ")

# Use default if empty
if [ -z "$KEYSTORE_FILE" ]; then
    KEYSTORE_FILE="rikkahub.jks"
fi

if [ -f "$KEYSTORE_FILE" ]; then
    echo -e "${GREEN}✓ Keystore found: $KEYSTORE_FILE${NC}"
    
    # Generate Base64
    echo ""
    echo -e "${YELLOW}Generating Base64 encoding...${NC}"
    
    BASE64_ENCODED=$(cat "$KEYSTORE_FILE" | base64 -w 0)
    
    echo ""
    echo -e "${GREEN}✓ Base64 generated (${#BASE64_ENCODED} characters)${NC}"
    echo ""
    echo -e "${BLUE}=== KEY_BASE64 ===${NC}"
    echo "$BASE64_ENCODED"
    echo -e "${BLUE}===================${NC}"
    echo ""
    echo -e "${YELLOW}Save this value as GitHub Secret: KEY_BASE64${NC}"
    
    # Save to file
    echo "$BASE64_ENCODED" > .keystore_base64
    echo -e "${GREEN}✓ Also saved to: .keystore_base64${NC}"
else
    echo -e "${RED}✗ Keystore file not found or skipped${NC}"
    echo ""
    echo "To generate a keystore:"
    echo ""
    echo "  keytool -genkey -v -keystore rikkahub.jks \\"
    echo "    -keyalg RSA -keysize 2048 -validity 10000 \\"
    echo "    -alias rikkahub"
    echo ""
    exit 1
fi

# Summary and instructions
echo ""
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Configuration Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Go to your GitHub repository"
echo "2. Navigate to: Settings > Secrets and variables > Actions"
echo "3. Click 'New repository secret' and add this secret:"
echo ""
echo -e "   ${YELLOW}Secret Name: KEY_BASE64${NC}"
echo "   Value: [content from .keystore_base64]"
echo ""
echo "4. Trigger a workflow:"
echo "   - Go to Actions tab"
echo "   - Select 'Build ARM V7' / 'Build Universal' / 'Build All Variants'"
echo "   - Click 'Run workflow'"
echo "   - Select release type (draft/prerelease/release)"
echo "   - Click 'Run workflow'"
echo ""
echo -e "${BLUE}Important Notes:${NC}"
echo ""
echo "✓ google-services.json is automatically read from app/ directory"
echo "✓ Only need 2 Secrets instead of 3!"
echo ""
echo "⚠  The following temporary files were created for convenience:"
echo "   - .keystore_base64"
echo "   - .signing_config"
echo ""
echo "   These files contain sensitive information. Do NOT commit them!"
echo ""
echo "✓ The .gitignore should exclude these files."
echo "✓ After adding secrets to GitHub, you can delete these files:"
echo ""
echo "   rm -f .keystore_base64 .signing_config"
echo ""
echo -e "${BLUE}Workflow Documentation:${NC}"
echo ""
echo "For detailed information, see:"
echo "  - WORKFLOW_GUIDE.md (完整指南)"
echo "  - QUICK_START_ARMV7.md (快速开始)"
echo "  - docs/ARM_V7_BUILD_GUIDE.md (编译指南)"
echo ""
