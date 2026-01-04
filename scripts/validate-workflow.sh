#!/bin/bash

# Workflow Configuration Validator
# 验证 GitHub Actions 工作流配置是否完整

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Workflow Configuration Validator${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

VALIDATION_PASSED=true

# Check workflow files
echo -e "${YELLOW}Checking Workflow Files...${NC}"
echo ""

WORKFLOWS=(
    ".github/workflows/build-armv7.yml"
    ".github/workflows/build-universal.yml"
    ".github/workflows/build-all.yml"
)

for workflow in "${WORKFLOWS[@]}"; do
    if [ -f "$PROJECT_ROOT/$workflow" ]; then
        echo -e "${GREEN}✓${NC} $workflow"
    else
        echo -e "${RED}✗${NC} $workflow (MISSING)"
        VALIDATION_PASSED=false
    fi
done

echo ""

# Check documentation
echo -e "${YELLOW}Checking Documentation...${NC}"
echo ""

DOCS=(
    "WORKFLOW_GUIDE.md"
    "QUICK_START_ARMV7.md"
    "docs/ARM_V7_BUILD_GUIDE.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$PROJECT_ROOT/$doc" ]; then
        echo -e "${GREEN}✓${NC} $doc"
    else
        echo -e "${RED}✗${NC} $doc (MISSING)"
        VALIDATION_PASSED=false
    fi
done

echo ""

# Check build configuration
echo -e "${YELLOW}Checking Build Configuration...${NC}"
echo ""

# Check app/build.gradle.kts has flavors
if grep -q "productFlavors" "$PROJECT_ROOT/app/build.gradle.kts"; then
    if grep -q '"armv7"' "$PROJECT_ROOT/app/build.gradle.kts"; then
        echo -e "${GREEN}✓${NC} armv7 flavor configured"
    else
        echo -e "${RED}✗${NC} armv7 flavor not found"
        VALIDATION_PASSED=false
    fi
    
    if grep -q '"universal"' "$PROJECT_ROOT/app/build.gradle.kts"; then
        echo -e "${GREEN}✓${NC} universal flavor configured"
    else
        echo -e "${RED}✗${NC} universal flavor not found"
        VALIDATION_PASSED=false
    fi
else
    echo -e "${RED}✗${NC} productFlavors not configured"
    VALIDATION_PASSED=false
fi

echo ""

# Check scripts
echo -e "${YELLOW}Checking Scripts...${NC}"
echo ""

if [ -f "$PROJECT_ROOT/scripts/build-armv7.sh" ]; then
    echo -e "${GREEN}✓${NC} scripts/build-armv7.sh"
else
    echo -e "${RED}✗${NC} scripts/build-armv7.sh (MISSING)"
    VALIDATION_PASSED=false
fi

if [ -f "$PROJECT_ROOT/scripts/setup-workflow.sh" ]; then
    echo -e "${GREEN}✓${NC} scripts/setup-workflow.sh"
else
    echo -e "${RED}✗${NC} scripts/setup-workflow.sh (MISSING)"
    VALIDATION_PASSED=false
fi

echo ""

# Check Makefile
echo -e "${YELLOW}Checking Makefile...${NC}"
echo ""

if [ -f "$PROJECT_ROOT/Makefile" ]; then
    if grep -q "build-armv7" "$PROJECT_ROOT/Makefile"; then
        echo -e "${GREEN}✓${NC} Makefile has build-armv7 target"
    else
        echo -e "${YELLOW}⚠${NC} Makefile missing build-armv7 target"
    fi
    
    if grep -q "build-universal" "$PROJECT_ROOT/Makefile"; then
        echo -e "${GREEN}✓${NC} Makefile has build-universal target"
    else
        echo -e "${YELLOW}⚠${NC} Makefile missing build-universal target"
    fi
else
    echo -e "${RED}✗${NC} Makefile not found"
    VALIDATION_PASSED=false
fi

echo ""

# Check .gitignore
echo -e "${YELLOW}Checking .gitignore...${NC}"
echo ""

IGNORE_ENTRIES=(
    ".keystore_base64"
    ".signing_config"
    "*.jks"
    "app/app.key"
)

for entry in "${IGNORE_ENTRIES[@]}"; do
    if grep -q "$entry" "$PROJECT_ROOT/.gitignore"; then
        echo -e "${GREEN}✓${NC} $entry in .gitignore"
    else
        echo -e "${YELLOW}⚠${NC} $entry not in .gitignore"
    fi
done

echo ""

# Check google-services.json
echo -e "${YELLOW}Checking google-services.json...${NC}"
echo ""

if [ -f "$PROJECT_ROOT/app/google-services.json" ]; then
    echo -e "${GREEN}✓${NC} app/google-services.json found"
else
    echo -e "${RED}✗${NC} app/google-services.json not found (required)"
    VALIDATION_PASSED=false
fi

echo ""

# Local configuration check
echo -e "${YELLOW}Checking Local Configuration...${NC}"
echo ""

if [ -f "$PROJECT_ROOT/local.properties" ]; then
    echo -e "${YELLOW}⚠${NC} local.properties exists (should not be committed)"
else
    echo -e "${GREEN}✓${NC} local.properties not found (good, should be local only)"
fi

echo ""

# Gradle wrapper check
echo -e "${YELLOW}Checking Gradle Setup...${NC}"
echo ""

if [ -f "$PROJECT_ROOT/gradlew" ]; then
    echo -e "${GREEN}✓${NC} Gradle wrapper found"
else
    echo -e "${RED}✗${NC} Gradle wrapper not found"
    VALIDATION_PASSED=false
fi

if [ -f "$PROJECT_ROOT/build.gradle.kts" ]; then
    echo -e "${GREEN}✓${NC} build.gradle.kts found"
else
    echo -e "${RED}✗${NC} build.gradle.kts not found"
    VALIDATION_PASSED=false
fi

echo ""

# Summary
echo -e "${BLUE}========================================${NC}"

if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}✅ All validations passed!${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo ""
    echo "1. Configure GitHub Secrets (only 1 required!):"
    echo "   ./scripts/setup-workflow.sh"
    echo ""
    echo "2. Add this Secret to GitHub:"
    echo "   - KEY_BASE64"
    echo ""
    echo "3. Test with manual trigger:"
    echo "   - Go to GitHub Actions"
    echo "   - Select a workflow"
    echo "   - Click 'Run workflow'"
    echo ""
    echo "4. Monitor build progress in Actions tab"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "   - Quick Start: QUICK_START_ARMV7.md"
    echo "   - Full Guide: WORKFLOW_GUIDE.md"
    echo "   - Build Guide: docs/ARM_V7_BUILD_GUIDE.md"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Validation failed!${NC}"
    echo ""
    echo -e "${YELLOW}Please fix the issues above.${NC}"
    echo ""
    echo -e "${BLUE}For help, see:${NC}"
    echo "   WORKFLOW_GUIDE.md"
    echo "   QUICK_START_ARMV7.md"
    echo ""
    exit 1
fi
