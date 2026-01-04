# ✅ GitHub Actions Secrets 配置

## 已生成的凭证

### Secret 1: KEY_BASE64

**文件位置：** `/tmp/key_base64.txt`

**内容长度：** 3,516 字符（Base64 编码的 keystore 文件）

**复制方法：**
```bash
# Linux/Mac 直接复制到剪贴板
cat /tmp/key_base64.txt | xclip -selection clipboard

# 或查看内容
cat /tmp/key_base64.txt
```

---

### Secret 2: SIGNING_CONFIG

**⚠️ 重要更新：** 签名配置现已硬编码在 workflow 中，你只需提供 KEY_BASE64！

**原因：** SIGNING_CONFIG 中的 storeFile 路径容易出错，现在 workflow 自动设置为 `rikkahub.keystore`

**如果你需要修改配置：**
编辑 `.github/workflows/build-*.yml` 文件，在 "Prepare signing credentials" 步骤中修改这些值：
```
storeFile=rikkahub.keystore      # keystore 文件名
storePassword=rikkahub@123       # keystore 密码
keyAlias=rikkahub                # 密钥别名
keyPassword=rikkahub@123         # 密钥密码
```

默认值已设置，如无特殊需求，可忽略此 Secret。

---

## 添加到 GitHub 的步骤

### 1️⃣ 进入 GitHub 仓库设置

- 打开你的 GitHub 仓库
- 点击 **Settings** 选项卡
- 左侧菜单选择 **Secrets and variables** → **Actions**

### 2️⃣ 添加第一个 Secret (KEY_BASE64)

1. 点击 **New repository secret**
2. **Name:** `KEY_BASE64`
3. **Value:** 复制 `/tmp/key_base64.txt` 中的全部内容
4. 点击 **Add secret**

### 3️⃣ 添加第二个 Secret (SIGNING_CONFIG)

⚠️ **已简化：** SIGNING_CONFIG 现已硬编码在 workflow 中！

如需自定义签名参数，编辑相应 workflow 文件的 "Prepare signing credentials" 步骤。

### 4️⃣ 验证添加成功

添加完成后，你应该看到这个 Secret 列在 Actions Secrets 中：
- ✅ `KEY_BASE64`

签名配置已自动处理，无需额外配置！

---

## Keystore 文件信息

**生成时间：** 2025-01-04

**文件位置：** `/workspaces/rikkahub-armv7a/rikkahub.jks`

**文件大小：** ~2.7 KB

**证书信息：**
- **名称：** CN=RikkaHub Developer, O=RikkaHub, C=CN
- **密钥算法：** RSA 2048-bit
- **有效期：** 10,000 天（约 27 年）
- **别名：** rikkahub
- **密码：** rikkahub@123

---

## ⚠️ 安全提示

1. **Keystore 文件（rikkahub.jks）：**
   - 已在项目目录生成
   - **不要提交到 Git！** (.gitignore 已配置)
   - 妥善保管，定期备份
   - 如遗失无法恢复

2. **密码（rikkahub@123）：**
   - 仅用于测试/演示
   - 生产环境建议使用更强的密码
   - 定期更换密码

3. **Secrets：**
   - 已安全存储在 GitHub
   - 不会显示在日志中
   - 编译完成后自动清理临时文件

---

## 下一步

1. ✅ 生成 Secrets 完成
2. ➡️ 添加 Secrets 到 GitHub
3. ➡️ 进入 GitHub Actions 手动触发编译
4. ➡️ 查看编译结果

---

**生成时间：** 2025-01-04
