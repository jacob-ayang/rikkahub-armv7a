.PHONY: help build-armv7 build-universal build-all test lint clean setup-android check-config

SHELL := /bin/bash
PROJECT_ROOT := $(shell pwd)
GRADLE := ./gradlew

# 颜色输出
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)===================================$(NC)"
	@echo "$(BLUE)RikkaHub ARM V7 Build Makefile$(NC)"
	@echo "$(BLUE)===================================$(NC)"
	@echo ""
	@echo "$(YELLOW)构建命令:$(NC)"
	@echo "  $(GREEN)make build-armv7$(NC)       - 编译 ARM V7 Release APK"
	@echo "  $(GREEN)make build-universal$(NC)   - 编译通用 Release APK"
	@echo "  $(GREEN)make build-all$(NC)         - 编译所有版本"
	@echo "  $(GREEN)make build-debug$(NC)       - 编译 Debug 版本"
	@echo ""
	@echo "$(YELLOW)开发命令:$(NC)"
	@echo "  $(GREEN)make test$(NC)              - 运行单元测试"
	@echo "  $(GREEN)make lint$(NC)              - 运行代码检查"
	@echo "  $(GREEN)make clean$(NC)             - 清理构建输出"
	@echo ""
	@echo "$(YELLOW)设置命令:$(NC)"
	@echo "  $(GREEN)make setup-android$(NC)     - 设置 Android SDK"
	@echo "  $(GREEN)make check-config$(NC)      - 检查构建配置"
	@echo ""
	@echo "$(YELLOW)其他命令:$(NC)"
	@echo "  $(GREEN)make sync-gradle$(NC)       - 同步 Gradle 缓存"
	@echo "  $(GREEN)make show-variants$(NC)     - 显示所有可用构建变体"

setup-android:
	@echo "$(BLUE)设置 Android SDK...$(NC)"
	@echo "Please ensure Android SDK is installed and ANDROID_HOME is set"

check-config:
	@echo "$(BLUE)检查构建配置...$(NC)"
	@if [ -f "local.properties" ]; then \
		echo "$(GREEN)✓ local.properties 存在$(NC)"; \
	else \
		echo "$(RED)✗ local.properties 不存在$(NC)"; \
		echo "  请创建 local.properties 文件并配置签名信息"; \
	fi
	@if [ -f "app/google-services.json" ]; then \
		echo "$(GREEN)✓ google-services.json 存在$(NC)"; \
	else \
		echo "$(RED)✗ google-services.json 不存在$(NC)"; \
		echo "  请从 Firebase Console 下载 google-services.json"; \
	fi
	@echo ""
	@echo "$(YELLOW)版本信息:$(NC)"
	@grep -oP 'versionName = "\K[^"]+' app/build.gradle.kts | head -1 | xargs echo "  Version:"
	@grep -oP 'versionCode = \K[0-9]+' app/build.gradle.kts | head -1 | xargs echo "  Code:"

build-armv7: check-config
	@echo "$(BLUE)编译 ARM V7 Release APK...$(NC)"
	@$(GRADLE) clean assembleArmv7Release
	@echo "$(GREEN)✓ ARM V7 编译完成$(NC)"
	@echo "  输出: $(PROJECT_ROOT)/app/build/outputs/apk/armv7/release/"

build-universal: check-config
	@echo "$(BLUE)编译通用 Release APK...$(NC)"
	@$(GRADLE) clean assembleUniversalRelease
	@echo "$(GREEN)✓ 通用版编译完成$(NC)"
	@echo "  输出: $(PROJECT_ROOT)/app/build/outputs/apk/universal/release/"

build-all: check-config
	@echo "$(BLUE)编译所有变体...$(NC)"
	@$(GRADLE) clean buildAll
	@echo "$(GREEN)✓ 所有变体编译完成$(NC)"

build-debug: check-config
	@echo "$(BLUE)编译 Debug 版本...$(NC)"
	@$(GRADLE) assembleDebug
	@echo "$(GREEN)✓ Debug 编译完成$(NC)"

test:
	@echo "$(BLUE)运行单元测试...$(NC)"
	@$(GRADLE) test

lint:
	@echo "$(BLUE)运行代码检查...$(NC)"
	@$(GRADLE) lint

clean:
	@echo "$(BLUE)清理构建输出...$(NC)"
	@$(GRADLE) clean
	@rm -rf build-output/
	@echo "$(GREEN)✓ 清理完成$(NC)"

sync-gradle:
	@echo "$(BLUE)同步 Gradle 缓存...$(NC)"
	@$(GRADLE) --build-cache
	@echo "$(GREEN)✓ 同步完成$(NC)"

show-variants:
	@echo "$(BLUE)可用的构建变体:$(NC)"
	@echo ""
	@echo "$(YELLOW)ARM V7 (32-bit):$(NC)"
	@echo "  - assembleArmv7Release"
	@echo "  - assembleArmv7Debug"
	@echo "  - bundleArmv7Release"
	@echo ""
	@echo "$(YELLOW)通用 (arm64-v8a, x86_64):$(NC)"
	@echo "  - assembleUniversalRelease"
	@echo "  - assembleUniversalDebug"
	@echo "  - bundleUniversalRelease"
	@echo ""
	@echo "$(YELLOW)示例用法:$(NC)"
	@echo "  ./gradlew assembleArmv7Release"

# 为脚本添加可执行权限
chmod-scripts:
	@echo "$(BLUE)设置脚本权限...$(NC)"
	@chmod +x scripts/*.sh
	@echo "$(GREEN)✓ 完成$(NC)"

# 显示构建大小
show-build-sizes:
	@echo "$(BLUE)构建输出大小:$(NC)"
	@find app/build/outputs -name "*.apk" -exec ls -lh {} \; 2>/dev/null || echo "  没有找到 APK 文件"

# 生成 Release Notes 模板
generate-release-notes:
	@echo "$(BLUE)生成 Release Notes 模板...$(NC)"
	@VERSION=$$(grep -oP 'versionName = "\K[^"]+' app/build.gradle.kts | head -1); \
	DATE=$$(date +'%Y-%m-%d'); \
	echo "# RikkaHub v$$VERSION (ARM V7)" > release-notes-$$VERSION.md; \
	echo "" >> release-notes-$$VERSION.md; \
	echo "**发布日期**: $$DATE" >> release-notes-$$VERSION.md; \
	echo "**架构**: ARM v7a (32-bit)" >> release-notes-$$VERSION.md; \
	echo "" >> release-notes-$$VERSION.md; \
	echo "## 新功能" >> release-notes-$$VERSION.md; \
	echo "- " >> release-notes-$$VERSION.md; \
	echo "" >> release-notes-$$VERSION.md; \
	echo "## Bug 修复" >> release-notes-$$VERSION.md; \
	echo "- " >> release-notes-$$VERSION.md; \
	echo "" >> release-notes-$$VERSION.md; \
	echo "## 安装说明" >> release-notes-$$VERSION.md; \
	echo "1. 下载 APK 文件" >> release-notes-$$VERSION.md; \
	echo "2. 启用\"未知源\"安装" >> release-notes-$$VERSION.md; \
	echo "3. 运行 APK 文件安装" >> release-notes-$$VERSION.md; \
	echo "" >> release-notes-$$VERSION.md; \
	echo "## 支持的设备" >> release-notes-$$VERSION.md; \
	echo "- Android 8.0 及以上" >> release-notes-$$VERSION.md; \
	echo "- ARM v7a (32-bit) 处理器" >> release-notes-$$VERSION.md; \
	echo "" >> release-notes-$$VERSION.md; \
	echo "$(GREEN)✓ Release Notes 已生成: release-notes-$$VERSION.md$(NC)"

# 快速开发构建 (不签名)
dev-build:
	@echo "$(BLUE)构建开发版本...$(NC)"
	@$(GRADLE) assembleArmv7Debug
	@echo "$(GREEN)✓ 开发版本构建完成$(NC)"
	@find app/build/outputs/apk/armv7/debug -name "*.apk" | head -1 | xargs echo "  输出:"

.DEFAULT_GOAL := help
