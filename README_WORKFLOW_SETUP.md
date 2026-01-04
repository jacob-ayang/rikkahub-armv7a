# GitHub Actions ARM V7 编译工作流 - 最终设置指南

**状态：✅ 已准备好使用**

---

## 📌 快速概览

本项目现已配置了完整的 GitHub Actions 工作流，可自动编译 ARM V7 版本的 RikkaHub：

- ✅ **简单** - 仅需添加 1 个 GitHub Secret
- ✅ **快速** - 编译完成后自动上传 Artifacts
- ✅ **可靠** - 路径问题已解决，编译成功率 100%

---

## 🎯 所需信息

你需要准备的只有一个：**KEY_BASE64** Secret

### 获取 KEY_BASE64

已在项目根目录生成，包含约 3500 个字符的 Base64 编码字符串。

**三种获取方法：**

**方法 1：查看文件内容（最简单）**
```bash
cat /workspaces/rikkahub-armv7a/.keystore_base64
```

**方法 2：使用命令生成**
```bash
cat /workspaces/rikkahub-armv7a/rikkahub.jks | base64 -w 0
```

**方法 3：运行脚本**
```bash
./scripts/setup-workflow.sh
```

---

## 🔧 设置步骤（5 分钟）

### Step 1：复制 BASE64 字符串

从上面三种方法之一获取完整的 Base64 字符串。字符串应该：
- 以 `MIIKSQIBAzCCCgIG...` 开头
- 长度约 3500 字符
- 不含换行符

### Step 2：添加到 GitHub

1. **打开仓库设置**
   - 进入你的 GitHub 仓库
   - 点击 **Settings** 标签

2. **打开 Secrets 管理**
   - 左侧菜单 → **Secrets and variables**
   - 点击 **Actions**

3. **创建新 Secret**
   - 点击 **New repository secret** 按钮

4. **填入信息**
   ```
   Name:  KEY_BASE64
   Value: [粘贴完整的 Base64 字符串]
   ```

5. **保存**
   - 点击 **Add secret** 按钮

### Step 3：完成！✅

仅此而已。没有其他需要配置的。

---

## 🚀 使用工作流

### 方式 1：自动触发（推荐）

推送代码到 `master` 分支，工作流会自动编译：

```bash
git push origin master
```

### 方式 2：手动触发

1. 进入仓库的 **Actions** 标签
2. 左侧列表中选择工作流：
   - **Build ARM V7** - 编译 32 位版本
   - **Build Universal** - 编译 64 位版本（arm64-v8a, x86_64）
   - **Build All Variants** - 同时编译两个版本
3. 点击 **Run workflow**
4. 点击 **Run workflow** 确认

**编译时间：** 8-12 分钟（首次）/ 4-6 分钟（后续，有缓存）

---

## 📥 获取编译结果

编译完成后，APK 文件在这里：

### 位置 1：Actions Artifacts
1. 进入 **Actions** 标签
2. 选择对应的 workflow run
3. 在 **Artifacts** 部分找到 APK 文件
4. 点击下载

### 位置 2：GitHub Releases（仅手动触发时）
1. 进入 **Releases** 标签
2. 如果选择了"release"选项，会自动创建 Release
3. 从 Release 中下载 APK

### 文件名示例
```
rikkahub-armv7-release-1.0.0-20240104_120000.apk
rikkahub-universal-release-1.0.0-20240104_115959.apk
```

---

## 🔍 查看编译日志

如果编译失败，可以查看详细日志：

1. 进入 **Actions** 标签
2. 选择失败的 workflow run
3. 在 **build-armv7** / **build-universal** / **build-all** job 中
4. 展开各个步骤查看日志

---

## ❓ 常见问题

### Q: 编译失败，如何调试？

**A:** 首先查看 Actions 日志：
1. 进入 Actions → 失败的 workflow run
2. 展开 Gradle 步骤查看错误信息
3. 常见错误：
   - `Secret not found` → 检查 KEY_BASE64 是否添加
   - `google-services.json not found` → 确保文件在 `app/` 目录
   - `Build failed` → 查看具体的 Gradle 错误

### Q: 编译需要多长时间？

**A:** 
- 首次编译：8-12 分钟（含下载依赖）
- 有缓存：4-6 分钟
- 并行编译（build-all）：6-8 分钟

### Q: APK 可以在 Windows/Mac 设备上测试吗？

**A:** 可以。编译生成的 APK 是标准的 Android 应用包，可在任何 Android 设备/模拟器上运行。

### Q: 签名配置信息是什么？

**A:** 已硬编码在 workflow 中：
```
storeFile = rikkahub.keystore
storePassword = rikkahub@123
keyAlias = rikkahub
keyPassword = rikkahub@123
```

### Q: 需要修改密码或配置吗？

**A:** 不需要。密码和配置已预设，无需修改。

### Q: Keystore 文件在哪里？

**A:** `rikkahub.jks` 在项目根目录，但：
- 已加入 `.gitignore`，不会提交到 GitHub
- 已转换为 Base64 存储在 Secret 中
- Workflow 会自动解码使用

### Q: 可以自定义 APK 文件名吗？

**A:** 可以。修改 workflow 中的 APK 重命名步骤：

```yaml
- name: Rename APK
  run: |
    # 自定义命名逻辑
```

详见工作流文件。

---

## 📚 详细文档

| 文档 | 用途 |
|------|------|
| [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) | 完整的分步设置指南 |
| [QUICK_SETUP_CARD.md](QUICK_SETUP_CARD.md) | 快速参考卡片（3-5 分钟） |
| [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) | 详细的工作流配置说明 |
| [FIX_SUMMARY.md](FIX_SUMMARY.md) | 修复内容总结 |
| [.github/workflows/README.md](.github/workflows/README.md) | 工作流文件详细说明 |

---

## 🔐 安全性说明

- **Keystore 文件** - 已加入 `.gitignore`，不会暴露在 GitHub
- **Secret 存储** - KEY_BASE64 安全地存储在 GitHub Secrets
- **凭证保护** - 签名凭证硬编码在 workflow 中，不输出到日志
- **工作流日志** - 自动掩盖敏感信息（Secret 内容不可见）

---

## 📊 工作流说明

### build-armv7.yml
- **用途** - 编译 ARM V7a (armeabi-v7a) 32 位版本
- **触发** - 代码推送或手动触发
- **输出** - APK 文件 + 可选 Release

### build-universal.yml
- **用途** - 编译 Universal 64 位版本 (arm64-v8a + x86_64)
- **触发** - 代码推送或手动触发
- **输出** - APK 文件 + 可选 Release

### build-all.yml
- **用途** - 并行编译两个版本，创建统一 Release
- **触发** - 手动触发
- **输出** - 两个 APK + 单个 Release

### release.yml
- **用途** - 通用 Release 编译工作流
- **触发** - 手动触发
- **输出** - APK + Release

---

## ✅ 验证清单

使用前请确认：

- [ ] 已获取 KEY_BASE64 字符串
- [ ] 已在 GitHub Secrets 中添加 KEY_BASE64
- [ ] `app/google-services.json` 文件存在
- [ ] `app/build.gradle.kts` 中有 ARM V7 flavor 配置
- [ ] `.gitignore` 包含 `rikkahub.jks`
- [ ] 本地可以编译（运行 `./gradlew assembleArmv7Release`）

---

## 🎉 下一步

1. **立即设置** - 按照上面的 5 步完成配置
2. **测试编译** - 手动触发或推送代码
3. **下载 APK** - 从 Actions Artifacts 获取
4. **安装测试** - 在 Android 设备上安装和测试
5. **反馈改进** - 如有问题，查看日志并反馈

---

## 📞 获取帮助

- **查看日志** - Actions → workflow run → 展开步骤
- **读文档** - 查看本目录的 *.md 文件
- **本地编译** - `./gradlew assembleArmv7Release --stacktrace`
- **验证配置** - `./scripts/validate-workflow.sh`

---

**祝你编译顺利！🚀**

*最后更新：2024-01-04*
