# 🔐 添加 GitHub Secrets - 快速步骤

## 现在的状态

✅ google-services.json 已添加到 app/ 目录  
✅ 代码已推送到 origin/master  
⏳ **需要**：添加 2 个 Secrets 以启用构建

---

## 需要的 2 个 Secrets

### 1️⃣ KEY_BASE64（签名密钥的 Base64 编码）

**获取方法**：

如果你有 keystore 文件（例如 `rikkahub.keystore`），运行：

```bash
# Linux/Mac
cat rikkahub.keystore | base64 -w 0

# 或 Python
python3 -c "import base64; print(base64.b64encode(open('rikkahub.keystore', 'rb').read()).decode())"

# Windows PowerShell
[Convert]::ToBase64String([io.File]::ReadAllBytes("rikkahub.keystore"))
```

**结果**: 一个很长的字符串（3500+ 字符），例如：
```
/u3+7QAAAAKgAAAAAQAFcmlra2F1aAAAAAQf5W...（很长）
```

### 2️⃣ SIGNING_CONFIG（签名配置）

**内容**（根据你的密钥调整）：

```properties
storeFile=rikkahub.keystore
storePassword=rikkahub@123
keyAlias=rikkahub
keyPassword=rikkahub@123
```

或使用你自己的密组合密码。

---

## 添加到 GitHub 的步骤

1. **访问 Settings**
   ```
   https://github.com/jacob-ayang/rikkahub-armv7a/settings/secrets/actions
   ```

2. **点击 "New repository secret"**

3. **添加 Secret #1**：
   - **Name**: `KEY_BASE64`
   - **Value**: 粘贴 Base64 编码的 keystore
   - **保存**

4. **添加 Secret #2**：
   - **Name**: `SIGNING_CONFIG`
   - **Value**: 粘贴签名配置内容
   - **保存**

---

## 验证 Secrets 已添加

运行以下命令（需要 GitHub CLI）：

```bash
gh secret list
```

应该看到：
```
KEY_BASE64              Updated 2024-XX-XX
SIGNING_CONFIG         Updated 2024-XX-XX
```

---

## 手动触发构建（测试）

Secrets 添加后，进行：

1. 访问 https://github.com/jacob-ayang/rikkahub-armv7a/actions
2. 左侧选择 **"Build ARM V7a"**
3. 点击 **"Run workflow"** 按钮
4. 保持默认设置，点击 **"Run workflow"**
5. 等待构建完成（通常 5-15 分钟）

---

## 如果没有 keystore？

如果你没有现成的 keystore，生成一个新的：

```bash
keytool -genkey -v \
  -keystore rikkahub.keystore \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias rikkahub
  
# 系统会要求输入：
# 密钥库密码 (keystore password): rikkahub@123
# 密钥密码 (key password): rikkahub@123
# 其他信息（名字、组织等）: 按需填写或直接回车
```

生成后，按上面的方法获取 Base64。

---

✨ 完成后，工作流会自动编译 ARM V7a APK！
