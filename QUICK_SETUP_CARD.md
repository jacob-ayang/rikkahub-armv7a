# ⚡ 快速设置卡片

## 🎯 目标
添加 GitHub Secret，使 GitHub Actions 能编译 ARM v7 版本的 RikkaHub

## ⏱️ 预计时间
3-5 分钟

---

## 📋 需要的信息

### KEY_BASE64 Secret 值

**完整的 Base64 字符串（3,516 字符）：**

```
MIIKSQIBAzCCCgIGCSqGSIb3DQEHAaCCCfMEggnvMIIJ6zCCBbIGCSqGSIb3DQEHAaCCBaMEggWfMIIFmzCCBZcGCyqGSIb3DQEM
```

**获取完整值：**

```bash
# 选项 1：在项目目录运行此命令
cat /workspaces/rikkahub-armv7a/.keystore_base64

# 选项 2：使用脚本生成
./scripts/setup-workflow.sh
```

---

## ✅ 设置步骤

### 1️⃣ 复制 BASE64 字符串

从上面获取完整的 `KEY_BASE64` 值（全部内容，约 3500 字符）。

### 2️⃣ 添加到 GitHub

**路径：** Settings → Secrets and variables → Actions

**点击：** New repository secret

**填入：**
- **Name:** `KEY_BASE64`
- **Value:** [粘贴完整的 BASE64 字符串]

**点击：** Add secret

### 3️⃣ 完成！

仅此而已。不需要其他配置。

---

## 🚀 立即测试

### 自动编译
推送任何代码更改到 `master` 分支会自动触发编译。

### 手动编译

1. 进入 GitHub 仓库 → **Actions**
2. 选择工作流（pick one）：
   - **build-armv7** - 编译 32 位版本
   - **build-universal** - 编译 64 位版本
   - **build-all** - 同时编译两个版本
3. 点击 **Run workflow**

**编译时间：** 约 8-10 分钟

---

## 📦 获取 APK

编译完成后，进入 **Actions** → workflow run → **Artifacts** 下载 APK 文件。

---

## ❓ 有问题？

查看详细指南：
- [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) - 完整设置指南
- [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - 详细配置说明
- [Actions 日志](https://github.com/jacob-ayang/rikkahub-armv7a/actions) - 编译日志

---

## 📝 关键信息

| 项目 | 内容 |
|------|------|
| 所需 Secret 数量 | **仅 1 个** |
| Secret 名称 | `KEY_BASE64` |
| Secret 长度 | 约 3,516 字符 |
| Keystore 文件 | `rikkahub.jks` |
| Store 密码 | `rikkahub@123` |
| Key 别名 | `rikkahub` |
| 有效期 | 10,000 天 |

---

**祝你编译顺利！🎉**
