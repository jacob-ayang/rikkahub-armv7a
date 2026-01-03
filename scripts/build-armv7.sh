#!/bin/bash

# ARM V7 Build Script for RikkaHub
# This script configures and builds the app for ARM V7 architecture

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RikkaHub ARM V7 Build Script${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if local.properties exists
if [ ! -f "$PROJECT_ROOT/local.properties" ]; then
    echo -e "${RED}Error: local.properties not found!${NC}"
    echo "Please create local.properties with signing configuration:"
    echo "  storeFile=path/to/keystore.jks"
    echo "  storePassword=password"
    echo "  keyAlias=alias"
    echo "  keyPassword=password"
    exit 1
fi

# Check if google-services.json exists
if [ ! -f "$PROJECT_ROOT/app/google-services.json" ]; then
    echo -e "${RED}Error: app/google-services.json not found!${NC}"
    echo "Please download it from Firebase Console"
    exit 1
fi

echo -e "${GREEN}✓ Configuration files found${NC}"

# Create temporary build config
echo -e "${YELLOW}Configuring ARM V7 build...${NC}"

# Build for ARM V7
echo -e "${BLUE}Building APK for ARM V7...${NC}"
cd "$PROJECT_ROOT"
chmod +x gradlew

# Build with ARM V7 configuration
./gradlew clean assembleArmv7Release \
    -Pandroid.injected.build.model=full \
    --build-cache \
    -Xmx4096m

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
    
    # Find and rename APK
    APK_DIR="$PROJECT_ROOT/app/build/outputs/apk/release"
    if [ -d "$APK_DIR" ]; then
        # Get version info
        VERSION_NAME=$(grep -oP 'versionName = "\K[^"]+' "$PROJECT_ROOT/app/build.gradle.kts" | head -1)
        BUILD_DATE=$(date +'%Y%m%d_%H%M%S')
        
        # Create output directory
        OUTPUT_DIR="$PROJECT_ROOT/build-output"
        mkdir -p "$OUTPUT_DIR"
        
        # Copy and rename APK
        for apk in "$APK_DIR"/*.apk; do
            if [ -f "$apk" ]; then
                NEW_NAME="rikkahub_${VERSION_NAME}_armv7a_${BUILD_DATE}.apk"
                cp "$apk" "$OUTPUT_DIR/$NEW_NAME"
                
                # Get file size
                SIZE=$(du -h "$OUTPUT_DIR/$NEW_NAME" | cut -f1)
                
                echo -e "${GREEN}✓ APK generated: $NEW_NAME ($SIZE)${NC}"
                echo -e "${YELLOW}  Location: $OUTPUT_DIR/$NEW_NAME${NC}"
            fi
        done
    fi
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Build complete!${NC}"
echo -e "${BLUE}========================================${NC}"
