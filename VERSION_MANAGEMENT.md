# 版本管理和 Release 发布指南

## 📋 概述

本项目提供了完整的版本管理工具链，用于：
- 管理版本号 (versionCode + versionName)
- 自动更新 Gradle 配置
- 创建 GitHub Release
- 发布编译后的 APK 文件

---

## 🚀 快速开始

### 方式 1：使用本地脚本（推荐）

```bash
# 查看当前版本
./scripts/bump-version.sh current

# 升级版本（自动选择）
./scripts/bump-version.sh major   # 1.7.7 → 2.0.0
./scripts/bump-version.sh minor   # 1.7.7 → 1.8.0
./scripts/bump-version.sh patch   # 1.7.7 → 1.7.8

# 指定具体版本
./scripts/bump-version.sh 1.8.0
```

**脚本会自动：**
1. ✅ 更新 `app/build.gradle.kts` 中的版本号
2. ✅ 递增 versionCode
3. ✅ 创建 Git 提交
4. ✅ 创建 Git Tag
5. ✅ 提示后续步骤

### 方式 2：使用 GitHub Actions（手动）

1. 进入 GitHub 仓库 → **Actions**
2. 选择 **Create Release** 工作流
3. 点击 **Run workflow**
4. 填入：
   - **version**: 版本号 (如 1.8.0)
   - **release_type**: 发布类型 (release/prerelease/draft)
5. 点击 **Run workflow**

**工作流会自动：**
1. ✅ 验证版本号格式
2. ✅ 编译 ARM V7 和 Universal 版本
3. ✅ 创建 GitHub Release
4. ✅ 上传 APK 文件到 Release

---

## 📝 详细步骤

### 本地发布 Release

#### Step 1: 更新版本号

```bash
# 进入项目目录
cd /path/to/rikkahub-armv7a

# 升级版本（选择一种）
./scripts/bump-version.sh minor

# 脚本输出示例：
# 当前版本: 1.7.7 (code: 124)
# 新版本:   1.8.0 (code: 125)
# 确认升级? (y/N) y
# ✓ 版本号已更新
```

#### Step 2: 推送到 GitHub

```bash
# 推送代码
git push origin master

# 推送 Tag
git push origin v1.8.0
```

#### Step 3: 触发 Release 工作流

**选项 A：自动触发（推荐）**

仓库中已添加 Git Tag 后，可以手动触发工作流创建 Release：

1. GitHub → **Actions**
2. **Create Release** 工作流
3. **Run workflow** → 输入版本号和类型
4. 工作流自动编译和发布

**选项 B：手动创建 Release**

1. GitHub → **Releases** → **Draft a new release**
2. Choose a tag: 选择 `v1.8.0`
3. Release title: `Release v1.8.0`
4. Write description (可选)
5. **Publish release**

---

## 📊 版本号说明

### versionCode 和 versionName

| 属性 | 说明 | 示例 |
|------|------|------|
| `versionCode` | 内部版本代码（递增整数） | 124, 125, 126 |
| `versionName` | 用户可见版本号 | 1.7.7, 1.8.0, 2.0.0 |

### 升级规则

遵循 **语义化版本控制 (Semantic Versioning)**：

```
版本格式: MAJOR.MINOR.PATCH
例子:    1.8.0

MAJOR (主版本) - 重大功能变化 (1.0.0 → 2.0.0)
MINOR (次版本) - 新增功能，向后兼容 (1.7.0 → 1.8.0)
PATCH (补丁)   - 修复 Bug，向后兼容 (1.7.7 → 1.7.8)
```

**何时升级：**
- `MAJOR` - 重大重构、API 改变、不兼容的功能变更
- `MINOR` - 新增功能、特性改进（向后兼容）
- `PATCH` - Bug 修复、小的改进（向后兼容）

---

## 🔧 脚本详解

### bump-version.sh

```bash
# 位置
./scripts/bump-version.sh

# 用法
./scripts/bump-version.sh [选项]

# 选项
major              升级主版本号
minor              升级次版本号
patch              升级补丁版本号
<版本号>           指定版本号 (如 1.8.0)
current            显示当前版本
--help             显示帮助
```

### 工作流的调用

脚本执行后会输出下一步操作：

```
下一步:
1. 审查变更：
   git log -1

2. 推送到 GitHub：
   git push origin master
   git push origin v1.8.0

3. 触发 Release 工作流：
   - 进入 GitHub Actions
   - 手动触发 'Release' 工作流
   - 或自动创建 Release
```

---

## 🌐 GitHub Actions 工作流

### create-release.yml

**触发方式：** 手动（workflow_dispatch）

**输入参数：**
- `version` - Release 版本号 (必填，格式 X.Y.Z)
- `release_type` - Release 类型 (release/prerelease/draft)

**工作流步骤：**
1. 验证版本号格式
2. 准备编译环境
3. 编译 ARM V7 Release APK
4. 编译 Universal Release APK
5. 创建 GitHub Release
6. 上传 APK 文件到 Release
7. 清理敏感文件

**工作流产物：**
- GitHub Release 页面
- 两个 APK 文件 (ARM V7 + Universal)
- Release 描述文档

---

## 📦 Release 内容

自动生成的 Release 包含：

### 描述内容
```markdown
## Release vX.Y.Z

### APK Files
- ARM V7a (32-bit) - 用于旧设备
  - 架构: armeabi-v7a
  
- Universal (64-bit) - 用于新设备
  - 架构: arm64-v8a, x86_64

### Installation
1. 下载对应的 APK 文件
2. 启用"未知来源"安装
3. 安装 APK

### Build Information
- 编译日期: [自动填充]
- Min SDK: 26, Target SDK: 36
```

### 文件清单
```
rikkahub-armv7-release-1.8.0.apk
rikkahub-universal-release-1.8.0.apk
```

---

## 💡 常见工作流

### 场景 1：修复 Bug，发布补丁版本

```bash
# 修改代码...
git add .
git commit -m "fix: 修复某个 Bug"

# 升级补丁版本
./scripts/bump-version.sh patch
# → 1.7.7 → 1.7.8

# 推送
git push origin master v1.7.8

# GitHub 自动创建 Release（或手动触发工作流）
```

### 场景 2：新增功能，发布次版本

```bash
# 开发新功能...
git add .
git commit -m "feat: 新增某功能"

# 升级次版本
./scripts/bump-version.sh minor
# → 1.7.7 → 1.8.0

# 推送
git push origin master v1.8.0

# 触发 Release 工作流
```

### 场景 3：重大更新，发布主版本

```bash
# 重大重构...
git add .
git commit -m "refactor: 大规模重构"

# 升级主版本
./scripts/bump-version.sh major
# → 1.7.7 → 2.0.0

# 推送
git push origin master v2.0.0

# 创建 Release（可选择 prerelease）
```

---

## ⚙️ 配置文件位置

**版本号定义位置：**
```
app/build.gradle.kts
└── android {
    └── defaultConfig {
        └── versionCode = 125           ← 更新这里
        └── versionName = "1.8.0"       ← 更新这里
```

**脚本会自动更新这些值。**

---

## 🔐 安全性

### Secret 需求

Release 工作流需要 `KEY_BASE64` Secret 进行签名：

| Secret | 用途 |
|--------|------|
| `KEY_BASE64` | Keystore 文件的 Base64 编码 |

**⚠️ 不需要其他 Secrets！** 其他凭证已硬编码在工作流中。

---

## ❓ 常见问题

### Q: 如果提交了错误的版本号怎么办？

**A:** 可以重新运行脚本：

```bash
# 恢复到正确的版本
./scripts/bump-version.sh <correct_version>

# 删除错误的 Tag（如果已推送）
git tag -d v1.8.0
git push origin :refs/tags/v1.8.0

# 重新提交
git push origin master v1.8.0
```

### Q: 如何看到版本升级历史？

**A:** 查看 Git 日志：

```bash
# 查看所有版本标签
git tag -l "v*"

# 查看特定版本的提交
git show v1.8.0

# 查看两个版本间的更改
git log v1.7.7..v1.8.0
```

### Q: Release 发布失败，如何重试？

**A:** GitHub Actions 工作流可以重新运行：

1. 进入 **Actions** → 失败的工作流
2. 点击 **Re-run failed jobs** 或 **Re-run all jobs**
3. 工作流重新执行

### Q: 可以同时发布多个版本吗？

**A:** 可以，但不推荐。建议：

```bash
# 推送主分支到 GitHub
git push origin master

# 然后依次创建 Release
# - 每个 Release 对应一个版本标签
```

### Q: versionCode 如何重置？

**A:** versionCode 是递增的内部版本代码，不应该重置。如果需要：

```bash
# 编辑 build.gradle.kts
# 找到: versionCode = 125
# 改为: versionCode = <新值>

# 然后提交
git add app/build.gradle.kts
git commit -m "chore: reset versionCode to X"
```

---

## 📚 相关文档

- [WORKFLOW_GUIDE.md](../WORKFLOW_GUIDE.md) - 工作流详细说明
- [README_WORKFLOW_SETUP.md](../README_WORKFLOW_SETUP.md) - 工作流配置
- [app/build.gradle.kts](../app/build.gradle.kts) - Gradle 配置

---

## ✨ 总结

| 操作 | 命令 | 结果 |
|------|------|------|
| 查看当前版本 | `./scripts/bump-version.sh current` | 显示版本 |
| 升级补丁版本 | `./scripts/bump-version.sh patch` | 1.7.7 → 1.7.8 |
| 升级次版本 | `./scripts/bump-version.sh minor` | 1.7.7 → 1.8.0 |
| 升级主版本 | `./scripts/bump-version.sh major` | 1.7.7 → 2.0.0 |
| 指定版本 | `./scripts/bump-version.sh 1.8.0` | 设为 1.8.0 |
| 手动发布 Release | GitHub Actions → Create Release | 编译 + 发布 |

---

**祝你版本管理顺利！🚀**
