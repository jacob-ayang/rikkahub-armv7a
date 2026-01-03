# ARM V7 编译快速参考卡片

## 🚀 快速命令

### 本地编译

```bash
# ARM V7 编译
make build-armv7

# 通用编译
make build-universal

# 全部编译
make build-all

# Debug 编译
make build-debug
```

### 本地构建脚本

```bash
./scripts/build-armv7.sh
```

### 直接 Gradle 命令

```bash
# ARM V7 Release
./gradlew assembleArmv7Release

# ARM V7 Debug
./gradlew assembleArmv7Debug

# 通用 Release
./gradlew assembleUniversalRelease
```

---

## 🔧 配置检查

```bash
# 检查配置文件
make check-config

# 显示版本信息
grep versionName app/build.gradle.kts
grep versionCode app/build.gradle.kts
```

---

## 📋 GitHub Actions 设置

### 需要的 Secrets

| 名称 | 来源 |
|------|------|
| `KEY_BASE64` | 签名密钥的 Base64 编码 |
| `SIGNING_CONFIG` | local.properties 内容 |

> 注意：`google-services.json` 应直接提交到 `app/google-services.json`，不要使用 Secret。

### 准备 Secrets

```bash
# 编码签名密钥
cat rikkahub.jks | base64 -w 0 > keystore.b64
```

### 添加到 GitHub

```
Settings > Secrets and variables > Actions > New repository secret
```

---

## 📁 重要文件位置

```
项目根目录/
├── .github/workflows/build-armv7.yml     # CI/CD 工作流
├── app/build.gradle.kts                   # Gradle 配置 (含 flavor)
├── scripts/build-armv7.sh                 # 本地编译脚本
├── Makefile                               # 快捷命令
├── local.properties                       # (本地) 签名配置
├── app/google-services.json               # (本地) Firebase 配置
└── docs/
    ├── ARM_V7_BUILD_GUIDE.md             # 完整编译指南
    └── GITHUB_ACTIONS_SETUP.md           # CI/CD 设置指南
```

---

## 📱 编译输出位置

### 本地编译输出

```
app/build/outputs/apk/armv7/release/
app/build/outputs/apk/universal/release/
```

### 脚本自动输出

```
build-output/rikkahub_1.7.5_armv7a_*.apk
```

---

## 🔄 工作流触发方式

### 手动触发

```
GitHub > Actions > Build ARM V7 > Run workflow
```

### 自动触发 (代码推送)

推送到 `master` 且修改以下路径：
- `app/src/**`
- `ai/src/**`
- `common/src/**`
- `build.gradle.kts`
- `.github/workflows/build-armv7.yml`

---

## ✅ 编译前检查清单

- [ ] `local.properties` 存在并配置正确
- [ ] `app/google-services.json` 存在
- [ ] 签名密钥可访问
- [ ] JDK 17 已安装
- [ ] Android SDK 已安装

---

## 🐛 常见问题快速解决

| 问题 | 解决方案 |
|------|--------|
| `local.properties 不存在` | 创建并配置签名信息 |
| `google-services.json 不存在` | 从 Firebase 下载 |
| `Keystore was tampered` | 重新编码 KEY_BASE64 |
| `Out of memory` | 增加 JVM 堆: `-Xmx6144m` |
| 编译超时 | 重试 (缓存会更快) |

---

## 📊 版本号管理

```kotlin
// app/build.gradle.kts
versionCode = 122        // 每次发布递增 +1
versionName = "1.7.5"    // major.minor.patch
```

### 发布新版本

```bash
# 1. 更新版本号
vim app/build.gradle.kts

# 2. 提交并推送
git commit -m "chore: bump version to 1.7.6"
git push origin master

# 3. 等待自动编译和发布
```

---

## 🎯 Release 流程

```
代码推送
    ↓
GitHub Actions 自动触发
    ↓
编译 ARM V7 APK
    ↓
创建版本标签 (v1.7.5-armv7a-2024-01-01)
    ↓
创建 GitHub Release
    ↓
上传 APK 文件
    ↓
发布完成 ✓
```

---

## 📚 文档导航

| 文档 | 用途 | 阅读时间 |
|------|------|--------|
| `QUICK_START_ARMV7.md` | 快速开始 | 5 分钟 |
| `docs/ARM_V7_BUILD_GUIDE.md` | 完整指南 | 15 分钟 |
| `docs/GITHUB_ACTIONS_SETUP.md` | CI/CD 设置 | 20 分钟 |
| `ARMV7_IMPLEMENTATION_SUMMARY.md` | 实现总结 | 10 分钟 |

---

## 🔗 有用的链接

- [Android 文档](https://developer.android.com/)
- [Gradle 文档](https://gradle.org/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Firebase 控制台](https://console.firebase.google.com)
- [项目 GitHub](https://github.com/re-ovo/rikkahub)

---

## 💡 提示

1. **使用 Makefile**: 比记住长的 Gradle 命令更简单
   ```bash
   make help        # 显示所有可用命令
   ```

2. **检查缓存**: 第二次构建会快得多
   ```bash
   ./gradlew --build-cache
   ```

3. **并行构建**: 多个构建任务可以并行运行
   ```bash
   ./gradlew build -x test  # 跳过测试加快速度
   ```

4. **查看日志**: GitHub Actions 日志包含完整的构建信息

---

## 🆘 获取帮助

1. **查看 GitHub Actions 日志**
   - Actions > 最新运行 > 展开失败的步骤

2. **查看详细文档**
   - 运行 `make help` 查看可用命令
   - 阅读 `docs/` 目录下的文档

3. **提交问题**
   - GitHub Issues
   - 包括错误日志和环境信息

---

**保持这个文档在手边，以便快速查阅！**
