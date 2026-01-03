# GitHub Actions 秘密和部署配置指南

## 概述

本指南说明如何为 RikkaHub 项目配置 GitHub Actions CI/CD，使其能够自动编译和发布 ARM V7 版本。

## 📋 所需信息

在配置 GitHub Secrets 之前，你需要准备以下信息：

1. **Android 签名密钥** (.jks 文件)
2. **签名密钥配置** (密码、别名等)
3. **Google Services JSON** (来自 Firebase)

## 🔑 步骤 1: 生成或获取签名密钥

### 如果已有签名密钥

跳到第 2 步

### 如果需要创建新的签名密钥

使用 Android Studio 或命令行生成：

```bash
# 使用 Android Studio (推荐)
# 在 Android Studio 中:
# 1. Build > Generate Signed Bundle/APK
# 2. 选择 "APK"
# 3. 点击 "Create new" 生成新密钥

# 或使用命令行
keytool -genkey -v \
  -keystore rikkahub.jks \
  -keyalgorithm RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias rikkahub_key \
  -keypass your_key_password \
  -storepass your_store_password

# 验证密钥
keytool -list -v -keystore rikkahub.jks -storepass your_store_password
```

**保存以下信息**：
- Keystore 文件路径: `rikkahub.jks`
- Store Password: `your_store_password`
- Key Alias: `rikkahub_key`
- Key Password: `your_key_password`

## 🔑 步骤 2: 准备 Secrets

### Secret 1: KEY_BASE64

将签名密钥文件编码为 Base64：

```bash
# Linux/Mac
cat rikkahub.jks | base64 -w 0 > keystore.b64
cat keystore.b64

# Windows (PowerShell)
[Convert]::ToBase64String([io.File]::ReadAllBytes("rikkahub.jks"))

# 或在线工具: https://www.base64encode.org/
```

输出示例（非常长的字符串）：
```
/u3+7QAAAALMAAAAAQAAAAEADHJpa2thLW....（很多字符）....iKX0=
```

### Secret 2: SIGNING_CONFIG

创建包含签名配置的文本，内容为：

```properties
storeFile=app/app.key
storePassword=your_store_password
keyAlias=rikkahub_key
keyPassword=your_key_password
```

**替换值**：
- `your_store_password`: 你的 keystore 密码
- `rikkahub_key`: 你的 key 别名
- `your_key_password`: 你的 key 密码

### Secret 3: GOOGLE_SERVICES_JSON

从 Firebase 控制台获取 `google-services.json`：

1. 访问 [Firebase Console](https://console.firebase.google.com)
2. 选择你的项目
3. 点击设置图标 > 项目设置
4. 下载 `google-services.json`
5. 复制完整的 JSON 内容

示例：
```json
{
  "type": "service_account",
  "project_id": "rikkahub-xxx",
  ...（完整内容）
}
```

## 🔐 步骤 3: 在 GitHub 中添加 Secrets

### 访问 Secrets 设置

1. 进入 GitHub 仓库主页
2. 点击 **Settings** (设置)
3. 左侧菜单 > **Secrets and variables** > **Actions**
4. 点击 **New repository secret**

### 添加 SECRET 1: KEY_BASE64

1. **Name**: `KEY_BASE64`
2. **Value**: 粘贴之前编码的 Base64 字符串
3. 点击 **Add secret**

### 添加 SECRET 2: SIGNING_CONFIG

1. **Name**: `SIGNING_CONFIG`
2. **Value**: 粘贴 local.properties 的内容
   ```
   storeFile=app/app.key
   storePassword=your_store_password
   keyAlias=rikkahub_key
   keyPassword=your_key_password
   ```
3. 点击 **Add secret**

### 添加 SECRET 3: GOOGLE_SERVICES_JSON

1. **Name**: `GOOGLE_SERVICES_JSON`
2. **Value**: 粘贴完整的 google-services.json 内容
3. 点击 **Add secret**

## ✅ 验证配置

在 GitHub Actions 中验证秘密是否正确设置：

```bash
# 在本地测试签名（可选）
# 使用之前编码的 keystore 进行测试构建
```

## 🚀 步骤 4: 触发第一次构建

### 手动触发

1. 进入仓库 **Actions** 标签
2. 左侧选择 **Build ARM V7** 工作流
3. 点击 **Run workflow**
4. 选择发布类型：
   - `draft`: 保存为草稿版本
   - `prerelease`: 标记为预发布
   - `release`: 正式版本
5. 点击 **Run workflow**

### 自动触发

推送代码到 `master` 分支，修改以下路径之一：
- `app/src/**`
- `ai/src/**`
- `app/build.gradle.kts`
- `.github/workflows/build-armv7.yml`

## 📊 监控构建

### 实时监控

1. 进入 **Actions** 标签
2. 点击最新的 **Build ARM V7** 运行
3. 查看实时日志
4. 每个步骤的状态都会显示

### 常见状态

| 状态 | 含义 | 操作 |
|------|------|------|
| 🟡 In progress | 正在构建 | 等待完成 |
| ✅ Success | 构建成功 | 下载 APK |
| ❌ Failure | 构建失败 | 查看日志 |

### 构建时间预期

- 首次构建: 7-10 分钟
- 增量编译: 4-6 分钟

## 📥 获取构建产物

### 方式 1: 从 Actions 下载

1. 进入 **Actions** 标签
2. 选择已完成的 **Build ARM V7** 运行
3. 在 **Artifacts** 部分找到文件
4. 点击下载

### 方式 2: 从 GitHub Release 下载

1. 进入仓库 **Releases** 页面
2. 选择对应版本的 Release
3. 在 Assets 中下载 APK

## 🔧 故障排除

### 构建失败: "Keystore was tampered with"

**原因**: `KEY_BASE64` 或 `SIGNING_CONFIG` 不正确

**解决**:
1. 重新编码签名密钥
2. 验证 Base64 编码的完整性
3. 确保 `SIGNING_CONFIG` 中的密码准确

### 构建失败: "google-services.json not found"

**原因**: `GOOGLE_SERVICES_JSON` 内容无效

**解决**:
1. 重新从 Firebase 下载 json 文件
2. 确保完整复制 JSON 内容（包括大括号）
3. 验证 JSON 格式有效（使用 [JSON 验证器](https://jsonlint.com)）

### 构建失败: "Out of memory"

**原因**: Gradle JVM 堆不足

**解决**: 工作流已设置 `-Xmx4096m`，如需更多可修改 `.github/workflows/build-armv7.yml`：
```yaml
env:
  GRADLE_OPTS: "-Xmx6144m"  # 增加到 6GB
```

### 构建超时

**原因**: 网络问题或依赖下载缓慢

**解决**:
1. 重试构建（通常会命中缓存）
2. 检查网络连接
3. 检查 gradle.org 状态

## 🔄 更新和维护

### 定期检查

- **每月**: 检查依赖更新
- **每季度**: 更新 SDK 和工具链
- **每年**: 轮换签名密钥

### 更新依赖

```bash
# 查看可用更新
./gradlew dependencyUpdates

# 更新后测试
./gradlew clean build
```

## 📱 APK 分发和安装

### 通过 Google Play

1. 在 Google Play Console 创建应用
2. 上传已签名的 APK
3. 填写应用信息
4. 提交审核

### 通过直链

1. 上传 APK 到文件服务器
2. 生成下载链接
3. 分享给用户

### 用户安装

1. 下载 APK
2. 启用"未知源"安装
3. 运行 APK 文件
4. 按提示安装

## 🎯 最佳实践

1. **安全**:
   - 定期轮换密钥
   - 限制 Secrets 访问权限
   - 使用强密码

2. **质量**:
   - 本地测试后再推送
   - 使用 pre-commit hooks
   - 定期代码审查

3. **发布**:
   - 遵循语义化版本
   - 撰写详细的 Release Notes
   - 保留发布历史

## 📚 参考资源

- [GitHub Secrets 官方文档](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Android 官方签名指南](https://developer.android.com/studio/publish/app-signing)
- [Firebase 文档](https://firebase.google.com/docs)
- [GitHub Actions 文档](https://docs.github.com/en/actions)

## 💡 常见问题

**Q: 是否可以使用多个签名密钥?**

A: 可以，但每个 flavor/variant 只能有一个活跃的签名配置。

**Q: 如何备份签名密钥?**

A: 
1. 将 `.jks` 文件保存在安全位置
2. 备份密码到密码管理器
3. 定期验证备份的可用性

**Q: 能否同时发布到多个渠道?**

A: 可以扩展工作流以支持多个发布目标（Google Play, GitHub Release 等）。

**Q: 如何处理版本号更新?**

A: 修改 `app/build.gradle.kts` 中的 `versionCode` 和 `versionName`，然后推送触发新构建。

---

**最后更新**: 2024 年 1 月
