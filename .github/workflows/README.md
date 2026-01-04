# RikkaHub ARM V7 GitHub Actions Workflows

此目录包含用于自动编译和发布 RikkaHub 的 GitHub Actions 工作流。

## 📋 工作流列表

| Workflow | 文件 | 目的 | 触发方式 |
|----------|------|------|--------|
| **Build ARM V7** | `build-armv7.yml` | 编译 32 位 ARM V7a 版本 | 手动/代码变更 |
| **Build Universal** | `build-universal.yml` | 编译 64 位通用版本 | 手动/代码变更 |
| **Build All Variants** | `build-all.yml` | 并行编译所有版本 | 手动触发 |

## 🚀 快速开始

### 1. 准备 Secrets

使用自动化脚本配置：

```bash
chmod +x scripts/setup-workflow.sh
./scripts/setup-workflow.sh
```

或手动配置：

1. 生成 keystore Base64：
   ```bash
   cat rikkahub.jks | base64 -w 0
   ```

2. 在 GitHub 仓库中添加三个 Secrets：
   - `KEY_BASE64`: Keystore 文件 Base64
   - `SIGNING_CONFIG`: 签名配置（4 行）
   - `GOOGLE_SERVICES_JSON`: Firebase JSON 文件

详见 `WORKFLOW_GUIDE.md`

### 2. 手动触发编译

1. 进入 GitHub **Actions** 标签
2. 选择 workflow（Build ARM V7/Build Universal/Build All Variants）
3. 点击 **Run workflow**
4. 选择发布类型：
   - `draft`: 草稿版本（测试）
   - `prerelease`: 预发布版本
   - `release`: 正式版本
5. 点击 **Run workflow**

### 3. 获取编译结果

**自动触发编译：**
- 编译成功后，进入 **Actions** 查看 Artifacts
- Artifacts 保留 30 天

**手动触发编译：**
- 编译成功后，自动创建 GitHub Release
- 进入 **Releases** 下载 APK

## 📖 详细文档

- **[WORKFLOW_GUIDE.md](../WORKFLOW_GUIDE.md)** - 完整工作流配置指南
- **[QUICK_START_ARMV7.md](../QUICK_START_ARMV7.md)** - 5 分钟快速开始
- **[docs/ARM_V7_BUILD_GUIDE.md](../docs/ARM_V7_BUILD_GUIDE.md)** - 详细编译指南

## 🔧 本地编译

如不想依赖 GitHub Actions，可本地编译：

```bash
# 检查配置
make check-config

# 编译 ARM V7
make build-armv7

# 编译 Universal
make build-universal

# 编译所有版本
make build-all
```

详见 `QUICK_START_ARMV7.md`

## 📊 工作流对比

| 功能 | ARM V7 | Universal | All |
|-----|--------|-----------|-----|
| 32 位编译 | ✅ | ❌ | ✅ |
| 64 位编译 | ❌ | ✅ | ✅ |
| 并行构建 | ❌ | ❌ | ✅ |
| 自动触发 | ✅ | ✅ | ❌ |
| 统一 Release | ❌ | ❌ | ✅ |

## ⚙️ 最小侵入性设计

- ✅ 不修改原项目文件
- ✅ 利用现有 flavor 配置
- ✅ 敏感信息通过 Secrets 隔离
- ✅ 编译后自动清理临时文件
- ✅ 完全兼容原项目

## 🔐 安全性

所有敏感信息（密钥、密码、配置）都通过 GitHub Secrets 安全存储。编译过程中：
- 从 Secrets 读取凭证
- 临时创建本地文件
- 编译完成后自动删除临时文件
- 敏感文件从不提交到仓库

## 🐛 故障排除

### 编译失败

1. 查看 Actions 日志中的错误信息
2. 确认 Secrets 配置正确
3. 在本地测试编译
4. 查看 `WORKFLOW_GUIDE.md` 的常见问题部分

### Secrets 问题

```bash
# 验证配置文件
make check-config

# 本地测试签名
./gradlew assembleArmv7Release --stacktrace
```

## 📱 支持的设备

### ARM V7a (32-bit)
- 设备：旧款和预算型设备
- CPU：ARM v7a
- Android：8.0+（API 26+）
- RAM：2GB+

### Universal (64-bit)
- 设备：现代设备
- CPU：ARM v8a 或 x86_64
- Android：8.0+（API 26+）
- RAM：3GB+

## 📈 性能指标

| 操作 | 耗时 |
|-----|------|
| ARM V7 编译 | 5-10 分钟 |
| Universal 编译 | 5-10 分钟 |
| 并行编译两个版本 | 6-10 分钟 |
| 缓存命中率 | +30-50% 速度提升 |

## 🔄 工作流触发条件

### Build ARM V7 / Build Universal

**手动触发：**
- GitHub Actions 页面 > Run workflow

**自动触发（push to master）：**
- `app/src/**` 变更
- `ai/src/**` 变更
- `common/src/**` 变更
- `highlight/src/**` 变更
- `search/src/**` 变更
- `tts/src/**` 变更
- `document/src/**` 变更
- `app/build.gradle.kts` 变更
- `build.gradle.kts` 变更
- `.github/workflows/build-*.yml` 变更

### Build All Variants

**仅手动触发**（避免重复编译）

## 📚 相关文件

```
.github/workflows/
├── build-armv7.yml        # ARM V7 编译工作流
├── build-universal.yml    # Universal 编译工作流
└── build-all.yml         # 所有版本编译工作流

scripts/
├── build-armv7.sh        # 本地编译脚本
└── setup-workflow.sh     # Workflow 配置助手

docs/
├── ARM_V7_BUILD_GUIDE.md         # 详细编译指南
└── GITHUB_ACTIONS_SETUP.md       # GA 设置指南

根目录:
├── WORKFLOW_GUIDE.md             # 工作流完整指南
├── QUICK_START_ARMV7.md          # 快速开始指南
├── Makefile                      # 本地构建命令
└── .gitignore                    # 敏感文件排除
```

## 💡 Tips

1. **首次使用**：建议先用 `draft` 发布类型测试
2. **性能优化**：Gradle 缓存会显著加快后续编译
3. **并行构建**：`Build All Variants` 会同时编译两个版本
4. **本地测试**：修改代码后先在本地测试编译

## ❓ 常见问题

**Q: 为什么有三个不同的 workflow？**
A: 满足不同使用场景 - 32 位编译、64 位编译、或两个都编译。

**Q: 编译失败怎么办？**
A: 查看 Actions 日志，确认 Secrets 配置，在本地测试。

**Q: 能否自定义编译参数？**
A: 可以，编辑对应的 workflow YAML 文件修改 gradle 参数。

**Q: APK 签名有效期？**
A: 取决于 keystore 中设置的有效期（通常 10 年）。

更多问题见 `WORKFLOW_GUIDE.md`

## 📝 License

遵循项目主 LICENSE

---

**最后更新：** 2025-01-04
