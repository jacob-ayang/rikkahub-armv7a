#!/bin/bash

# 版本号管理脚本
# 用途：更新版本号并准备 Release

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_GRADLE="$PROJECT_ROOT/app/build.gradle.kts"

# 获取当前版本号
get_current_version() {
    grep -oP 'versionName = "\K[^"]+' "$BUILD_GRADLE" | head -1
}

get_current_code() {
    grep -oP 'versionCode = \K[0-9]+' "$BUILD_GRADLE" | head -1
}

# 显示帮助信息
show_help() {
    cat << 'EOF'
版本号管理脚本 - RikkaHub ARM V7

用法:
  ./scripts/bump-version.sh [选项] [版本号]

选项:
  major              升级主版本号 (1.0.0 -> 2.0.0)
  minor              升级次版本号 (1.0.0 -> 1.1.0)
  patch              升级补丁版本号 (1.0.0 -> 1.0.1)
  <版本号>           直接指定版本号 (如: 1.8.0)
  current            显示当前版本号
  -h, --help         显示帮助信息

示例:
  ./scripts/bump-version.sh major           # 升级主版本号
  ./scripts/bump-version.sh 1.8.0          # 设置为 1.8.0
  ./scripts/bump-version.sh current        # 查看当前版本

EOF
}

# 版本号比较函数
increment_version() {
    local version=$1
    local type=$2
    
    # 分解版本号
    local major=$(echo $version | cut -d'.' -f1)
    local minor=$(echo $version | cut -d'.' -f2)
    local patch=$(echo $version | cut -d'.' -f3)
    
    case $type in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            echo -e "${RED}❌ 未知的升级类型: $type${NC}"
            return 1
            ;;
    esac
    
    echo "${major}.${minor}.${patch}"
}

# 验证版本号格式
validate_version() {
    local version=$1
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo -e "${RED}❌ 版本号格式无效: $version (应为 X.Y.Z 格式)${NC}"
        return 1
    fi
    return 0
}

# 更新版本号
update_version() {
    local new_version=$1
    local new_code=$2
    local old_version=$3
    local old_code=$4
    
    echo -e "${BLUE}更新版本信息:${NC}"
    echo "  versionCode: $old_code → $new_code"
    echo "  versionName: $old_version → $new_version"
    
    # 更新 versionCode
    sed -i "s/versionCode = $old_code/versionCode = $new_code/" "$BUILD_GRADLE"
    
    # 更新 versionName
    sed -i "s/versionName = \"$old_version\"/versionName = \"$new_version\"/" "$BUILD_GRADLE"
    
    echo -e "${GREEN}✓ 版本号已更新${NC}"
}

# 创建 Git 提交和 Tag
create_release() {
    local version=$1
    
    echo ""
    echo -e "${YELLOW}准备 Release...${NC}"
    
    # 检查是否有未提交的更改
    if ! git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}检测到有未提交的更改，正在暂存...${NC}"
        git add app/build.gradle.kts
    fi
    
    # 创建提交
    if git diff-index --cached --quiet HEAD --; then
        echo -e "${YELLOW}已暂存版本更新${NC}"
    else
        git commit -m "chore: bump version to $version"
        echo -e "${GREEN}✓ 创建版本提交${NC}"
    fi
    
    # 创建 Git Tag
    git tag -a "v$version" -m "Release version $version" || true
    echo -e "${GREEN}✓ 创建 Git Tag: v$version${NC}"
    
    echo ""
    echo -e "${BLUE}下一步:${NC}"
    echo "1. 审查变更："
    echo "   git log -1"
    echo ""
    echo "2. 推送到 GitHub："
    echo "   git push origin master"
    echo "   git push origin v$version"
    echo ""
    echo "3. 触发 Release 工作流："
    echo "   - 进入 GitHub Actions"
    echo "   - 手动触发 'Release' 工作流"
    echo "   - 或自动创建 Release"
}

# 主程序
main() {
    local current_version=$(get_current_version)
    local current_code=$(get_current_code)
    
    if [ -z "$1" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    if [ "$1" = "current" ]; then
        echo -e "${BLUE}当前版本:${NC}"
        echo "  versionCode: $current_code"
        echo "  versionName: $current_version"
        exit 0
    fi
    
    local new_version
    
    case "$1" in
        major|minor|patch)
            new_version=$(increment_version "$current_version" "$1")
            ;;
        *)
            new_version="$1"
            ;;
    esac
    
    # 验证版本号
    if ! validate_version "$new_version"; then
        exit 1
    fi
    
    # 检查版本号是否相同
    if [ "$new_version" = "$current_version" ]; then
        echo -e "${YELLOW}⚠️  新版本号与当前版本相同: $new_version${NC}"
        read -p "是否继续? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
    
    # 计算新的版本代码
    local new_code=$((current_code + 1))
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}版本升级确认${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "当前版本: $current_version (code: $current_code)"
    echo "新版本:   $new_version (code: $new_code)"
    echo ""
    
    # 确认
    read -p "确认升级? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 0
    fi
    
    # 执行更新
    update_version "$new_version" "$new_code" "$current_version" "$current_code"
    
    # 创建 Release
    create_release "$new_version"
}

main "$@"
