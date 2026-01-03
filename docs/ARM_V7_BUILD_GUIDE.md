# ARM V7 Build CI/CD 指南

本项目已配置完整的 GitHub Actions CI/CD 流程，可以自动编译和发布 ARM V7 架构的 RikkaHub APK。

## 📋 项目结构概览

- **app/**: Android 应用主模块
- **ai/**: AI SDK 和提供者集成（OpenAI, Google, Anthropic 等）
- **common/**, **highlight/**, **search/**, **tts/**, **document/**: 功能和工具库
- **.github/workflows/**: GitHub Actions 工作流定义

## 🏗️ ARM V7 架构编译配置

### 编译 Flavor 配置

项目已配置两个编译 flavor：

| Flavor | 架构 | 用途 |
|--------|------|------|
| `universal` | arm64-v8a, x86_64 | 通用构建（支持现代设备） |
| `armv7` | armeabi-v7a | ARM V7 构建（支持 32 位设备） |

### 支持的 Android 版本

- **最低 SDK**: API Level 26 (Android 8.0)
- **目标 SDK**: API Level 36 (Android 15)

## 🔧 本地构建

### 前置要求

1. **Java 17+** 环境
2. **Android SDK** (API Level 36)
3. **签名密钥** (`local.properties` 和签名文件)
4. **Google Services 配置** (`app/google-services.json`)

### 配置本地构建环境

#### 1. 创建 local.properties

```properties
storeFile=/path/to/your/keystore.jks
storePassword=your_keystore_password
keyAlias=your_key_alias
keyPassword=your_key_password
```

#### 2. 下载 Google Services JSON

从 Firebase Console 下载 `google-services.json` 并放在 `app/` 目录下。

### 构建命令

#### 使用自动化脚本（推荐）

```bash
chmod +x scripts/build-armv7.sh
./scripts/build-armv7.sh
```

此脚本将：
- ✓ 验证必需的配置文件
- ✓ 编译 ARM V7 APK
- ✓ 自动重命名输出文件
- ✓ 生成构建报告

#### 直接使用 Gradle

```bash
# 编译 ARM V7 Release APK
./gradlew assembleArmv7Release

# 编译 ARM V7 Debug APK
./gradlew assembleArmv7Debug

# 编译通用 Release APK
./gradlew assembleUniversalRelease
```

### 输出文件

构建完成后，APK 文件位置：

```
app/build/outputs/apk/armv7/release/rikkahub_[version]_armv7Release.apk
app/build/outputs/apk/universal/release/rikkahub_[version]_universalRelease.apk
```

脚本会自动复制到 `build-output/` 目录并重命名：

```
build-output/rikkahub_1.7.5_armv7a_20240101_120000.apk
```

## 🚀 GitHub Actions 自动编译

### 工作流文件

- 位置: `.github/workflows/build-armv7.yml`
- 触发条件:
  - 手动触发（workflow_dispatch）
  - 推送到 master 分支的代码和配置文件变更

### GitHub Secrets 配置

在 GitHub 仓库设置中，添加以下 Secrets：

| Secret 名称 | 描述 | 内容 |
|------------|------|------|
| `KEY_BASE64` | Base64 编码的签名密钥 | keystore.jks 的 Base64 编码 |
| `SIGNING_CONFIG` | 签名配置 | local.properties 的内容 |

> 注意：`google-services.json` 应直接提交到仓库 `app/google-services.json`（不要使用 Secret）。

#### 准备 Secrets

**1. 编码签名密钥:**

```bash
# Linux/Mac
base64 -i keystore.jks | tr -d '\n' | pbcopy

# 或直接查看
cat keystore.jks | base64 -w 0 > keystore.b64
```

**2. local.properties 内容:**

```properties
storeFile=app/app.key
storePassword=your_password
keyAlias=your_alias
keyPassword=your_password
```

**3. google-services.json 内容:**

直接复制 JSON 文件的全部内容

### 手动触发编译

1. 进入 GitHub 仓库
2. 点击 **Actions** 标签
3. 选择 **Build ARM V7** 工作流
4. 点击 **Run workflow** 按钮
5. 选择 Release 类型：
   - `draft`: 草稿版本
   - `prerelease`: 预发布版本
   - `release`: 正式版本
6. 点击 **Run workflow**

### 自动编译

配置了自动触发：

```yaml
push:
  branches:
    - master
  paths:
    - 'app/src/**'
    - 'ai/src/**'
    - '...其他模块...'
    - 'app/build.gradle.kts'
    - '.github/workflows/build-armv7.yml'
```

当以上路径有更新时，会自动触发编译流程。

## 📊 CI/CD 工作流详解

### 工作流步骤

```
1. 检出代码
   └─ 使用深度克隆以获取完整历史

2. 设置 JDK 17
   └─ 使用 Temurin 发行版

3. 设置 Android SDK
   └─ 初始化 Android 构建工具

4. 准备构建文件
   └─ 解码签名密钥
   └─ 配置签名参数
   └─ 配置 Google Services

5. 编译 ARM V7 APK
   └─ 执行 assembleArmv7Release task
   └─ 优化 JVM 堆大小

6. 提取版本信息
   └─ 获取 versionName
   └─ 获取 versionCode
   └─ 记录构建日期

7. 重命名 APK
   └─ 格式: rikkahub_v1.7.5_armv7a_2024-01-01.apk

8. 上传构建产物
   └─ 保留 30 天

9. 创建 GitHub Release
   └─ 生成版本标签
   └─ 发布 APK 文件
   └─ 生成版本说明
```

### 构建产物

- **Artifacts**: GitHub Actions 构建产物
  - 保留期: 30 天
  - 可从 Actions 标签下载

- **GitHub Release**:
  - 包含 APK 文件
  - 版本说明和支持信息
  - 永久保存

## 📦 安装 APK

### 前置要求

- Android 8.0 或更高版本
- 至少 100 MB 可用存储空间
- 支持 ARM V7a (32 位) 处理器的设备

### 安装步骤

1. 从 GitHub Release 或 Actions 下载 APK
2. 将 APK 传输到 Android 设备
3. 在 Settings > Security 中启用 "Unknown Sources"
4. 打开文件管理器，点击 APK 文件
5. 点击 "Install"
6. 安装完成后点击 "Open"

### 常见问题

**Q: 在哪些设备上可以使用 ARM V7 版本？**

A: ARM V7a (32 位) 处理器的设备，包括：
   - 较旧的 Android 手机（2014-2018 年）
   - 某些预算设备
   - 一些平板电脑

**Q: 为什么需要 ARM V7 版本？**

A: 某些旧设备或特定的硬件架构只支持 32 位应用。ARM V7 版本可以在这些设备上运行。

**Q: 如何验证设备是否支持 ARM V7？**

A: 
- 下载 "CPU-Z" 应用
- 检查 "CPU Architecture" 是否为 "ARMv7"

**Q: 构建失败了怎么办？**

A: 检查以下内容：
   1. Secrets 是否正确配置
   2. `google-services.json` 内容是否有效
   3. 签名密钥是否正确编码
   4. 查看 GitHub Actions 日志获取详细错误信息

## 🔐 安全建议

1. **不要提交**：
   - `local.properties`
   - `app/google-services.json`
   - `.jks` 签名文件

2. **使用 GitHub Secrets**:
   - 存储所有敏感信息
   - 定期轮换密钥

3. **限制访问**:
   - 仅授权人员可以触发发布
   - 启用分支保护规则

## 📚 相关文件

```
.github/
├── workflows/
│   └── build-armv7.yml          # ARM V7 编译 CI/CD 工作流
└── FUNDING.yml

scripts/
└── build-armv7.sh               # 本地编译脚本

app/
├── build.gradle.kts             # 包含 flavor 配置
└── google-services.json         # (不追踪)

armv7.properties                 # ARM V7 配置属性
local.properties                 # (不追踪) 本地签名配置
```

## 🔄 版本管理

版本号遵循语义化版本控制：

```
versionName = "1.7.5"  # major.minor.patch
versionCode = 122      # 递增整数
```

Release 标签格式：
```
v1.7.5-armv7a-2024-01-01
```

## 📞 故障排除

### 常见问题

1. **签名错误**
   ```
   错误: Keystore was tampered with, or password was incorrect
   ```
   → 检查 `SIGNING_CONFIG` secret 的准确性

2. **Google Services 错误**
   ```
   错误: google-services.json not found
   ```
   → 验证 `app/google-services.json` 内容为有效的 JSON 并已提交到仓库

3. **内存不足**
   ```
   错误: Out of memory
   ```
   → 工作流已设置 `-Xmx4096m`，如需更多可修改工作流

4. **超时错误**
   ```
   错误: The operation timed out
   ```
   → 检查网络连接，重试编译

### 查看详细日志

1. 进入 GitHub Actions
2. 点击失败的工作流运行
3. 展开 "Gradle Build" 步骤
4. 查看完整的错误信息

## 📈 监控和优化

### 构建时间

- 首次构建: ~5-10 分钟
- 增量编译: ~3-5 分钟

### 减少构建时间的方法

1. 启用 Gradle 缓存（已启用）
2. 平行构建（已配置）
3. 避免不必要的重建

## 🎯 最佳实践

1. **测试后再提交**:
   ```bash
   ./gradlew test
   ./gradlew lint
   ```

2. **使用 Conventional Commits**:
   ```
   feat: Add new feature
   fix: Fix bug
   chore: Update dependencies
   ```

3. **定期检查依赖**:
   ```bash
   ./gradlew dependencyUpdates
   ```

4. **保持分支整洁**:
   - 删除已合并的分支
   - 定期 rebase

## 📖 更多信息

- [Android 官方文档](https://developer.android.com/)
- [Gradle 文档](https://gradle.org/docs/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- 项目 README: [README.md](../README.md)

---

**最后更新**: 2024 年 1 月
