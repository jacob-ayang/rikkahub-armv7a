# 🚀 ARM V7a CI/CD 快速参考卡

## 📋 需要做什么？

### 准备阶段 (10 分钟)

```bash
# 第 1 步：准备 keystore 或生成新的
keytool -genkey -v -keystore rikkahub.keystore -keyalg RSA -keysize 2048 -alias rikkahub

# 第 2 步：生成 Base64 编码
cat rikkahub.keystore | base64 -w 0  # 复制输出

# 第 3 步：准备签名配置
cat > signing.txt << EOF
storeFile=rikkahub.keystore
storePassword=<你的密钥库密码>
keyAlias=rikkahub
keyPassword=<你的密钥密码>
EOF
```

### GitHub 配置 (2 分钟)

1. **访问**: https://github.com/jacob-ayang/rikkahub-armv7a/settings/secrets/actions

2. **添加 3 个 Secrets**：

| Secret 名称 | 值来源 |
|-----------|--------|
| `KEY_BASE64` | 第 2 步的 Base64 字符串 |
| `SIGNING_CONFIG` | signing.txt 的内容 |
| `GOOGLE_SERVICES_JSON` | app/google-services.json*（可选） |

*如果仓库中已有此文件，可跳过

### 测试构建 (5 分钟)

```bash
# 方法 1：自动触发
git push origin master

# 方法 2：手动触发
# https://github.com/jacob-ayang/rikkahub-armv7a/actions
# 选择 "Build ARM V7a" → Run workflow
```

---

## 📂 新增文件

```
.github/workflows/
├── build-armv7.yml                    # ⭐ CI/CD 工作流

ARMV7A_CI_CD_SETUP.md                  # 📖 详细配置指南
ARMV7A_CI_CD_CHECKLIST.md              # ✅ 检查清单
ARMV7A_CI_CD_SUMMARY.md                # 📊 完成总结
google-services-backup.json            # 💾 备份参考
```

---

## 🔑 密钥生成速查

### 生成 keystore

```bash
keytool -genkey -v \
  -keystore rikkahub.keystore \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias rikkahub
```

提示会问：
- 密钥库密码: `rikkahub@123` (例)
- 名字: `RikkaHub`
- 确认: `是`

### 生成 Base64

```bash
# Linux/Mac
cat rikkahub.keystore | base64 -w 0

# Windows PowerShell
[Convert]::ToBase64String([io.File]::ReadAllBytes("rikkahub.keystore"))

# 将输出保存为 KEY_BASE64
```

### 签名配置

```properties
storeFile=rikkahub.keystore
storePassword=<密钥库密码>
keyAlias=rikkahub
keyPassword=<密钥密码>
```

---

## 🎯 工作流功能一览

| 功能 | 说明 |
|------|------|
| 自动触发 | master 分支推送时 |
| 手动触发 | workflow_dispatch（可选发布类型） |
| 构建产物 | ARM V7a Release APK |
| 版本管理 | 自动提取版本号和时间戳 |
| 发布 | 自动创建 GitHub Release（手动触发时） |
| 验证 | SHA256 校验和计算 |
| 清理 | 自动删除敏感文件 |

---

## ⏱️ 预期耗时

| 步骤 | 耗时 |
|------|------|
| 准备 keystore | 2-5 分钟 |
| Base64 编码 | < 1 分钟 |
| GitHub 配置 | 2-3 分钟 |
| 首次构建 | 10-15 分钟* |
| 后续构建 | 5-8 分钟** |

*包含依赖下载
**使用缓存

---

## 📱 成功标志

✅ GitHub Actions 工作流显示 **All jobs completed successfully**
✅ **Artifacts** 中可下载 `.apk` 文件
✅ **Summary** 中显示 APK 大小和 SHA256
✅ 可选：自动创建 Release（手动触发时）

---

## 🐛 快速诊断

| 问题 | 检查项 |
|-----|--------|
| 密钥验证失败 | BASE64 和 SIGNING_CONFIG 的密码是否匹配 |
| google-services.json 错误 | 文件是否存在，或 GOOGLE_SERVICES_JSON Secret 是否正确 |
| 构建超时 | 首次构建较慢，重试或增加超时时间 |
| APK 找不到 | 查看完整日志中的错误信息 |

---

## 📚 完整文档

- 🔐 **详细配置**: [ARMV7A_CI_CD_SETUP.md](./ARMV7A_CI_CD_SETUP.md)
- ✅ **完整清单**: [ARMV7A_CI_CD_CHECKLIST.md](./ARMV7A_CI_CD_CHECKLIST.md)
- 📊 **配置总结**: [ARMV7A_CI_CD_SUMMARY.md](./ARMV7A_CI_CD_SUMMARY.md)
- 🚀 **快速开始**: [QUICK_START_ARMV7.md](./QUICK_START_ARMV7.md)

---

## 🔗 快速链接

- 🔑 **添加 Secrets**: https://github.com/jacob-ayang/rikkahub-armv7a/settings/secrets/actions
- ▶️ **运行工作流**: https://github.com/jacob-ayang/rikkahub-armv7a/actions
- 📦 **下载产物**: https://github.com/jacob-ayang/rikkahub-armv7a/actions (最新任务)
- 🏷️ **发布页面**: https://github.com/jacob-ayang/rikkahub-armv7a/releases

---

## 💡 关键提示

1. **安全第一** - keystore 和密码妥善保管，丢失会无法更新 Play Store
2. **Base64 仔细** - 粘贴时确保完整，不包含换行符（使用 `-w 0` 参数）
3. **密码一致** - SIGNING_CONFIG 中的密码必须与 keystore 匹配
4. **第一次较慢** - 首次构建需要下载 Android SDK 和依赖，10+ 分钟正常
5. **有问题查日志** - GitHub Actions 会显示详细的构建日志，找错误在日志中

---

**快速参考版本**: 1.0
**最后更新**: 2026-02-16
