# ARM V7a CI/CD 配置指南

本指南说明如何为 ARM V7a 构建配置 GitHub Actions CI/CD 工作流所需的密钥和文件。

## 📋 需要的 Secrets

GitHub Actions 工作流需要以下 Secrets 才能成功构建 ARM V7a APK：

| Secret 名称 | 说明 | 类型 | 必需 |
|-----------|------|------|------|
| `KEY_BASE64` | 签名密钥(keystore)的Base64编码 | 二进制 | ✅ |
| `SIGNING_CONFIG` | 签名配置信息 | 文本 | ✅ |
| `GOOGLE_SERVICES_JSON` | Firebase google-services.json 内容 | JSON | ❌* |

*可选：如果仓库中已包含 `app/google-services.json`，则无需此 Secret

---

## 🔑 1. 生成或获取签名密钥 (Keystore)

### 选项 A: 使用已有的 keystore

如果你已经有一个 keystore 文件（例如 `rikkahub.jks` 或 `.keystore`），跳到 **步骤 2**。

### 选项 B: 生成新的 keystore

如果没有 keystore，使用 `keytool` 生成：

```bash
# 生成 keystore（有效期 10000 天）
keytool -genkey -v \
  -keystore rikkahub.keystore \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias rikkahub

# 系统会提示输入：
# 密钥库密码 (keystore password): 设置一个安全密码，例如 rikkahub@123
# 密钥密码 (key password): 可以与密钥库密码相同
# 其他信息 (名字、组织等): 按需填写

# 查看生成的 keystore 信息
keytool -list -v -keystore rikkahub.keystore
```

**重要**: 妥善保管 keystore 文件和密码，丢失会无法更新应用！

---

## 🔐 2. 准备 KEY_BASE64

需要将 keystore 文件编码为 Base64 字符串。

### Linux / macOS

```bash
cat rikkahub.keystore | base64 -w 0
# 或
base64 < rikkahub.keystore
```

### Windows (PowerShell)

```powershell
[Convert]::ToBase64String([io.File]::ReadAllBytes("rikkahub.keystore"))
```

### 结果

输出应该是一个长字符串，看起来像：
```
/u3+7QAAAAKgAAAAAQAFcmlra2F1aAAAAAQf5W...（很长）
```

**复制整个输出字符串** —— 这将是 `KEY_BASE64` 的值。

---

## 📝 3. 准备 SIGNING_CONFIG

这定义了签名时使用的密钥库和密钥的详细信息。需要以下信息：

```properties
storeFile=rikkahub.keystore
storePassword=<你的密钥库密码>
keyAlias=rikkahub
keyPassword=<你的密钥密码>
```

**示例**:
```properties
storeFile=rikkahub.keystore
storePassword=rikkahub@123
keyAlias=rikkahub
keyPassword=rikkahub@123
```

将此内容保存为 `SIGNING_CONFIG` 的值（稍后添加到 GitHub Secrets）。

---

## 📱 4. 准备 GOOGLE_SERVICES_JSON (可选)

Firebase 配置文件内容。

### 获取方式：

1. 访问 [Firebase Console](https://console.firebase.google.com)
2. 选择项目 "rikkahub-32bit" (或你的项目)
3. 项目设置 → 下载 `google-services.json`
4. 打开文件，复制全部内容

或者，从备份分支获取：

```bash
git show backup-master-20260216-015025:app/google-services.json
```

此参数是可选的，因为仓库中可能已包含此文件。

---

## 🛠️ 5. 在 GitHub 添加 Secrets

### 步骤：

1. **进入 GitHub 仓库**
   - 访问 `https://github.com/jacob-ayang/rikkahub-armv7a`

2. **打开 Settings 标签**
   - 右上角 → Settings

3. **找到 Secrets and variables**
   - 左侧菜单 → Security → Secrets and variables → Actions

4. **添加 Secrets**

#### Secret 1: KEY_BASE64

- 点击 **New repository secret**
- **Name:** `KEY_BASE64`
- **Value:** 粘贴 Base64 编码的 keystore（从步骤 2）
- 点击 **Add secret**

#### Secret 2: SIGNING_CONFIG

- 点击 **New repository secret**
- **Name:** `SIGNING_CONFIG`
- **Value:** 粘贴签名配置信息（从步骤 3）
- 点击 **Add secret**

#### Secret 3: GOOGLE_SERVICES_JSON (可选)

- 点击 **New repository secret**
- **Name:** `GOOGLE_SERVICES_JSON`
- **Value:** 粘贴 google-services.json 的完整内容（从步骤 4）
- 点击 **Add secret**

---

## ✅ 6. 验证配置

### 检查 Secrets 是否正确添加

```bash
# 在仓库本地执行（需要 GitHub CLI）
gh secret list
```

应该显示：
```
KEY_BASE64              Updated 2024-XX-XX X:XX:XX PM (UTC)
SIGNING_CONFIG         Updated 2024-XX-XX X:XX:XX PM (UTC)
GOOGLE_SERVICES_JSON   Updated 2024-XX-XX X:XX:XX PM (UTC)
```

---

## 🚀 7. 触发构建

### 方式 1: 自动构建（推荐）

只要代码推送到 `master` 分支并修改了特定文件，工作流会自动执行：

```bash
# 提交代码到 master
git add .
git commit -m "feat: 新功能"
git push origin master

# 工作流会自动在 GitHub Actions 中触发
```

### 方式 2: 手动触发

1. 进入 GitHub 仓库
2. **Actions** 标签
3. 左侧选择 **Build ARM V7a**
4. 右侧点击 **Run workflow**
5. 选择分支和选项：
   - **Branch:** master
   - **Release type:** draft / prerelease / release
6. 点击 **Run workflow**

---

## 📊 8. 监控构建

1. 进入 **Actions** 标签
2. 点击最新的 **Build ARM V7a** 工作流
3. 查看各步骤的执行情况
4. 如果构建成功，在 **Summary** 中可以看到构建统计

### 常见问题排查

| 问题 | 解决方案 |
|-----|--------|
| ❌ 密钥验证失败 | 确保 BASE64 和 SIGNING_CONFIG 的密码一致 |
| ❌ 构建超时 | 检查网络连接和 Gradle 缓存 |
| ❌ APK 不适配 ARM V7a | 检查 `app/build.gradle.kts` 中的 ABI 过滤配置 |
| ❌ Firebase 错误 | 确保 google-services.json 正确且项目 ID 匹配 |

---

## 📦 9. 获取构建产物

### 从 GitHub Actions 下载

1. 进入 Actions → 最新构建
2. **Summary** → **Artifacts** 部分
3. 下载 `rikkahub-armv7a-x.x.x` 文件

### 从 GitHub Release 下载

如果选择了 "release" 或 "prerelease" 模式，APK 会自动上传到 Release：

1. 进入 **Releases** 标签
2. 找到对应版本
3. 下载 `.apk` 文件

---

## 🔒 安全建议

1. **保护 Secrets**
   - 永远不要在代码或日志中暴露 Secrets
   - GitHub Actions 会自动隐藏 Secret 值（显示 `***`）
   - 定期检查 keystore 密码是否被泄露

2. **Keystore 备份**
   - 妥善备份 keystore 文件
   - 如果丢失，无法更新已发布的应用

3. **密钥轮换**
   - 定期更新密钥（例如每年一次）
   - 保持 Firebase 密钥的安全性

4. **访问控制**
   - 仅允许信任的人员访问仓库设置
   - 定期审计谁有权访问 Secrets

---

## 🔗 相关文档

- **构建指南**: [QUICK_START_ARMV7.md](../QUICK_START_ARMV7.md)
- **完整 CI/CD 文档**: [docs/GITHUB_ACTIONS_SETUP.md](../docs/GITHUB_ACTIONS_SETUP.md)
- **ARM V7 编译细节**: [docs/ARM_V7_BUILD_GUIDE.md](../docs/ARM_V7_BUILD_GUIDE.md)

---

**创建时间**: 2026-02-16
