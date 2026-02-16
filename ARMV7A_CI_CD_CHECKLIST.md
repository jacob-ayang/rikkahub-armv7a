# ARM V7a CI/CD 快速检查清单

在配置 CI/CD 之前，请按照以下清单逐项检查。

## ✅ 前置准备

- [ ] 已准备好 keystore 文件（`rikkahub.keystore` 或类似）
- [ ] 了解 keystore 的密码（设置签名配置时需要）
- [ ] 有 Firebase 项目访问权限用于获取 `google-services.json`
- [ ] 已有 push 权限到 `https://github.com/jacob-ayang/rikkahub-armv7a`

## 🔑 密钥和配置

### KEY_BASE64 准备

- [ ] 已将 keystore 文件转换为 Base64 编码
  ```bash
  cat rikkahub.keystore | base64 -w 0
  ```
- [ ] 复制了完整的 Base64 字符串（应该是 3500+ 字符）
- [ ] 在记事本中临时保存了此值

### SIGNING_CONFIG 准备

根据以下模板准备签名配置：

```properties
storeFile=rikkahub.keystore
storePassword=<你的密钥库密码>
keyAlias=<你的密钥别名，通常是 rikkahub>
keyPassword=<你的密钥密码>
```

- [ ] 已定义 `storePassword`（keystore 密码）
- [ ] 已定义 `keyAlias`（通常是 `rikkahub`）
- [ ] 已定义 `keyPassword`（如果与 keystore 密码相同，值相同即可）
- [ ] 在记事本中临时保存了此配置

### GOOGLE_SERVICES_JSON 准备（可选）

- [ ] 检查了 `app/google-services.json` 是否已在仓库中
  - 如果已有：无需添加 Secret（可选）
  - 如果没有：从 Firebase Console 下载并准备内容
- [ ] 如需添加，已从备份分支获取或从 Firebase 控制台下载

## 🛠️ GitHub Secrets 配置

### 添加 Secrets

1. 访问 https://github.com/jacob-ayang/rikkahub-armv7a/settings/secrets/actions

2. 添加 Secret 1: `KEY_BASE64`
   - [ ] Name: `KEY_BASE64`
   - [ ] Value: Base64 编码的 keystore（从上面复制）
   - [ ] 点击 **Add secret**

3. 添加 Secret 2: `SIGNING_CONFIG`
   - [ ] Name: `SIGNING_CONFIG`
   - [ ] Value: 完整的签名配置（从上面复制）
   - [ ] 点击 **Add secret**

4. 添加 Secret 3: `GOOGLE_SERVICES_JSON`（可选）
   - [ ] Name: `GOOGLE_SERVICES_JSON`
   - [ ] Value: google-services.json 完整内容（如果需要）
   - [ ] 点击 **Add secret**

### 验证 Secrets

- [ ] 已访问 https://github.com/jacob-ayang/rikkahub-armv7a/settings/secrets/actions
- [ ] 可以看到所有已添加的 Secrets（名称可见，值隐藏）
- [ ] 确认至少有 `KEY_BASE64` 和 `SIGNING_CONFIG` 两个 Secret

## 📦 工作流文件验证

- [ ] 检查 `.github/workflows/build-armv7.yml` 是否存在
- [ ] 工作流文件包含以下关键步骤：
  - [ ] Checkout code
  - [ ] Set up JDK 17
  - [ ] Setup Android SDK
  - [ ] Validate configuration
  - [ ] Prepare signing credentials
  - [ ] Build ARM V7a Release APK
  - [ ] Verify build output
  - [ ] Upload artifacts

## 🚀 首次构建测试

### 选项 A: 自动触发

- [ ] 对任何受监视的文件进行本地更改
- [ ] 提交并推送到 master 分支
  ```bash
  git add .
  git commit -m "test: CI/CD 配置测试"
  git push origin master
  ```
- [ ] 进入 GitHub Actions 监控构建

### 选项 B: 手动触发

- [ ] 访问 https://github.com/jacob-ayang/rikkahub-armv7a/actions
- [ ] 左侧选择 **Build ARM V7a** 工作流
- [ ] 点击 **Run workflow** 按钮
- [ ] 选择 `master` 分支
- [ ] 选择 Release type: `draft`
- [ ] 点击 **Run workflow**

### 构建监控

- [ ] 工作流已开始执行（可在 Actions 标签中看到）
- [ ] 观察每个步骤的执行情况：
  - ✅ Checkout
  - ✅ JDK 设置
  - ✅ Android SDK 设置
  - ✅ 配置验证
  - ✅ 签名凭证准备
  - ✅ 构建 APK
  - ✅ 验证输出
  - ✅ 上传工件

### 构建成功验证

- [ ] 工作流显示 ✅ **All jobs completed successfully**
- [ ] 可以看到 **Summary** 中的构建统计：
  - 版本号
  - 构建日期
  - APK 大小
  - 文件名

- [ ] 可以下载 APK 工件：
  - [ ] 访问 https://github.com/jacob-ayang/rikkahub-armv7a/actions
  - [ ] 选择最新的 **Build ARM V7a** 任务
  - [ ] 在 **Artifacts** 部分找到 `rikkahub-armv7a-x.x.x`
  - [ ] 下载 APK 文件

## 📱 APK 验证（可选但推荐）

- [ ] 下载了生成的 APK
- [ ] 在 Android 设备或模拟器上安装了 APK
- [ ] 应用运行无错误
- [ ] 应用功能正常（登录、基本操作等）

## ⚠️ 故障排除

如果构建失败，按以下顺序检查：

1. **签名错误**
   - [ ] 检查 `SIGNING_CONFIG` 中的密码是否与 keystore 匹配
   - [ ] 验证 `keyAlias` 是否正确
   - [ ] 重新生成 Base64 编码

2. **缺失文件**
   - [ ] 检查 `app/google-services.json` 是否存在
   - [ ] 如果缺失且未配置 Secret，构建会失败
   - [ ] 从备份分支获取或从 Firebase 控制台下载

3. **构建错误**
   - [ ] 查看完整的构建日志
   - [ ] 搜索 **ERROR** 或 **FAILED** 关键字
   - [ ] 检查是否有编译错误或依赖问题

4. **超时或网络问题**
   - [ ] 重试构建
   - [ ] 检查网络连接

## 📚 下一步

一旦首次构建成功，你可以：

1. **启用自动发布**
   - 修改工作流以自动创建 Release
   - 配置版本号自动化

2. **添加更多工作流**
   - `build-universal.yml` - 构建通用 APK
   - `build-all.yml` - 构建所有变体
   - `create-release.yml` - 自动创建 Release

3. **配置监控和通知**
   - 添加失败通知（邮件、Slack 等）
   - 配置构建结果报告

4. **测试和发布**
   - 在真实设备上测试 APK
   - 发布到 Google Play Store
   - 创建 GitHub Release

## 📞 需要帮助？

- 查看工作流日志：访问 Actions → 最新任务 → 查看具体步骤
- 检查 Secret 是否正确：访问 Settings → Secrets and variables
- 查看相关文档：
  - [ARMV7A_CI_CD_SETUP.md](./ARMV7A_CI_CD_SETUP.md) - 详细配置指南
  - [QUICK_START_ARMV7.md](./QUICK_START_ARMV7.md) - 快速开始指南

---

**清单版本**: 1.0
**最后更新**: 2026-02-16
