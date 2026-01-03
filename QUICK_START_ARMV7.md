# ARM V7 编译快速开始

这是一个快速指南，帮助你快速上手 RikkaHub 的 ARM V7 编译和发布流程。

## 🚀 5 分钟快速开始

### 步骤 1: 本地编译准备 (1 分钟)

```bash
# 进入项目目录
cd /path/to/rikkahub-armv7a

# 查看帮助和可用命令
make help

# 检查配置
make check-config
```

### 步骤 2: 配置签名文件 (2 分钟)

#### 创建 `local.properties`:
```bash
cat > local.properties <<EOF
storeFile=/path/to/your/keystore.jks
storePassword=your_keystore_password
keyAlias=your_key_alias
keyPassword=your_key_password
EOF
```

#### 准备 Google Services:
从 Firebase Console 下载 `google-services.json` 放到 `app/` 目录

### 步骤 3: 本地编译 (2 分钟)

```bash
# 使用快捷命令编译 ARM V7
make build-armv7

# 或使用脚本
chmod +x scripts/build-armv7.sh
./scripts/build-armv7.sh

# 或直接使用 Gradle
./gradlew assembleArmv7Release
```

### 编译输出

APK 文件位置：
```
app/build/outputs/apk/armv7/release/rikkahub_1.7.5_armv7Release.apk
```

---

## 📱 配置自动编译 (GitHub Actions)

### 步骤 1: 准备 Secrets (5 分钟)

**1.1 将签名密钥转为 Base64:**

```bash
# Linux/Mac
cat rikkahub.jks | base64 -w 0

# Windows PowerShell
[Convert]::ToBase64String([io.File]::ReadAllBytes("rikkahub.jks"))
```

复制输出的长字符串。

**1.2 收集配置:**

创建以下内容：
- `KEY_BASE64`: 上面的 Base64 字符串
- `SIGNING_CONFIG`: 
  ```
  storeFile=app/app.key
  storePassword=your_password
  keyAlias=your_alias
  keyPassword=your_password
  ```
- `google-services.json`: 将 `google-services.json` 下载并提交到 `app/google-services.json`，不要使用 Secret。

### 步骤 2: 添加 GitHub Secrets (3 分钟)

1. 进入 GitHub 仓库 > **Settings**
2. 左侧 > **Secrets and variables** > **Actions**
3. 点击 **New repository secret**
4. 分别添加三个 Secret:
   - Name: `KEY_BASE64`, Value: [Base64 字符串]
   - Name: `SIGNING_CONFIG`, Value: [配置内容]
   - **不要** 添加 `GOOGLE_SERVICES_JSON` Secret；请将 `google-services.json` 下载并提交到仓库的 `app/google-services.json`。

### 步骤 3: 触发编译 (1 分钟)

#### 方式 A: 手动触发

```
GitHub > Actions > Build ARM V7 > Run workflow > 选择发布类型 > Run workflow
```

#### 方式 B: 自动触发

推送代码到 `master` 分支并修改以下路径之一：
- `app/src/**`
- `ai/src/**`
- `build.gradle.kts` 文件

### 步骤 4: 获取编译结果

成功完成后，可以从以下位置获取 APK：

1. **GitHub Actions Artifacts**: 
   - Actions > 最新的构建 > Artifacts

2. **GitHub Release**:
   - Releases > 最新版本 > Assets

---

## 📋 常见任务

### 查看所有构建变体

```bash
make show-variants
```

### 编译所有版本

```bash
make build-all
```

### 运行测试

```bash
make test
```

### 代码检查

```bash
make lint
```

### 清理旧构建

```bash
make clean
```

---

## 🔧 故障排除

### 问题: "local.properties 不存在"

**解决:**
```bash
# 使用提示的命令创建 local.properties
cp local.properties.example local.properties
# 然后编辑文件，填入你的签名配置
```

### 问题: "google-services.json 不存在"

**解决:**
1. 进入 [Firebase Console](https://console.firebase.google.com)
2. 选择项目 > 设置 > 下载 `google-services.json`
3. 放到 `app/` 目录

### 问题: 构建失败 "Keystore was tampered with"

**解决:**
1. 确认密码准确
2. 重新生成 Base64 编码
3. 更新 GitHub Secrets

### 问题: GitHub Actions 超时

**解决:**
1. 重试（通常会使用缓存更快）
2. 修改工作流增加超时时间：`.github/workflows/build-armv7.yml`

---

## 📚 详细文档

- **完整 CI/CD 指南**: [docs/GITHUB_ACTIONS_SETUP.md](docs/GITHUB_ACTIONS_SETUP.md)
- **ARM V7 编译指南**: [docs/ARM_V7_BUILD_GUIDE.md](docs/ARM_V7_BUILD_GUIDE.md)
- **项目 README**: [README.md](README.md)

---

## 🎯 典型工作流

### 本地开发和测试

```bash
# 1. 修改代码
vim app/src/main/java/...

# 2. 本地编译测试
make build-armv7

# 3. 如果编译成功，提交代码
git add .
git commit -m "feat: 新功能描述"
git push origin master

# 4. GitHub Actions 自动编译和发布
# 等待 GitHub Actions 完成
```

### 发布新版本

```bash
# 1. 更新版本号
vim app/build.gradle.kts
# 修改 versionName 和 versionCode

# 2. 提交版本更新
git add app/build.gradle.kts
git commit -m "chore: bump version to v1.7.6"
git push origin master

# 3. 等待自动编译
# Actions 会自动为新版本编译并创建 Release

# 4. 在 GitHub Release 页面编辑 Release Notes
```

---

## 💡 建议

1. **使用 Makefile**: 复杂的命令都封装在 Makefile 中，更容易记忆和使用
   ```bash
   make build-armv7        # 比 ./gradlew assembleArmv7Release 更简短
   ```

2. **测试后再推送**: 在推送到 master 之前，先在本地编译测试
   ```bash
   make test && make lint && make build-armv7
   ```

3. **使用分支开发**: 为新功能创建分支，然后通过 PR 合并到 master
   ```bash
   git checkout -b feature/new-feature
   # ... 开发代码 ...
   git push origin feature/new-feature
   # 在 GitHub 上创建 PR
   ```

4. **定期更新**: 保持依赖和工具链最新
   ```bash
   ./gradlew dependencyUpdates
   ```

---

## 📞 获取帮助

如有问题，可以：

1. 查看 GitHub Actions 日志获取详细错误信息
2. 查看相关文档
3. 提交 Issue 到 GitHub

---

**最后更新**: 2024 年 1 月
