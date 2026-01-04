# Fork 自动同步 - 使用指南

## 🎯 工作原理

自动每天检查 upstream 是否有新的提交和 release，并智能发布版本：

```
每天 UTC 00:00 自动运行：

upstream 有代码更新？
  ├─ 是 → 自动升级 patch 版本 → 发布 prerelease
  └─ 否 → 下一步

upstream 有新 release？
  ├─ 是 → 同步版本 → 发布 release
  └─ 否 → 等待下次检查
```

---

## 📦 发布类型

### Prerelease（抢先版）
- **何时发布**：upstream 有新代码提交时
- **版本号**：自动升级 patch → `v1.7.8-prerelease`
- **稳定性**：⚠️ 不稳定，测试用
- **用户**：希望尝试最新功能的用户

### Release（正式版）
- **何时发布**：upstream 有新 release 时
- **版本号**：与 upstream 完全同步 → `v1.8.0`
- **稳定性**：✅ 稳定，正式版
- **用户**：所有用户

---

## 🚀 使用场景

### 场景 1：upstream 活跃更新

```
upstream 提交 5 个新的 commit（2025-01-05）
   ↓ [自动在 2025-01-06 00:00 UTC 触发]
检测到新代码 → 版本升级 1.7.7 → 1.7.8
   ↓
编译 ARM V7 + Universal APK
   ↓
发布 prerelease: v1.7.8-prerelease

用户可以：
✅ 下载最新 prerelease 测试新功能
✅ 反馈 bug
✅ 等待正式版发布
```

### 场景 2：upstream 发布正式版本

```
upstream 发布新 release: v1.8.0
   ↓ [自动在检查时触发]
检测到新 release tag
   ↓
同步版本 tag 到本地
   ↓
编译 ARM V7 + Universal APK
   ↓
发布 release: v1.8.0

用户可以：
✅ 下载最新正式版本
✅ 安装到设备上
```

### 场景 3：无更新

```
upstream 无新提交，无新 release
   ↓
工作流运行 1-2 分钟，检查完毕
   ↓
无任何操作，等待下次检查
```

---

## 💡 主要特性

✅ **完全自动化**
- 无需手动干预
- 每天自动检查
- 自动编译和发布

✅ **智能版本管理**
- 自动升级 patch 版本
- 与 upstream 版本同步
- 完整的 Git 历史

✅ **双层发布机制**
- prerelease：测试新功能
- release：正式稳定版本

✅ **零成本**
- 月度用量 100-200 分钟
- GitHub 免费额度 2000 分钟
- 完全免费！

---

## 🔍 监控工作流

### 查看工作流运行

1. GitHub 仓库 → **Actions** 标签
2. **Sync Fork with Auto Release** 工作流
3. 查看运行历史和日志

### 查看发布版本

1. GitHub 仓库 → **Releases** 标签
2. 查看：
   - `v1.7.8-prerelease` - 自动生成的抢先版
   - `v1.8.0` - 同步的正式版
   - `v1.8.1-prerelease` - 后续的抢先版

---

## 🎛️ 手动触发

### 强制发布 prerelease

```
GitHub → Actions → Sync Fork with Auto Release
         ↓
         Run workflow
         ↓
         ☑️ Force create prerelease even without upstream changes
         ↓
         Run workflow
```

即使没有 upstream 更新，也可以强制发布 prerelease。

---

## 📊 示例时间轴

```
2025-01-04 12:00 UTC
  upstream 提交新 commit
  
2025-01-05 00:00 UTC
  ✅ 自动检查触发
  ✅ 检测到新 commit
  ✅ 版本升级 1.7.7 → 1.7.8
  ✅ 编译 APK
  ✅ 发布 v1.7.8-prerelease
  
2025-01-05 12:00 UTC
  upstream 发布 release v1.8.0
  
2025-01-06 00:00 UTC
  ✅ 自动检查触发
  ✅ 检测到新 release tag
  ✅ 同步版本 tag
  ✅ 编译 APK
  ✅ 发布 v1.8.0（release）
  
2025-01-07 00:00 UTC
  ❌ 无新更新
  ✅ 工作流运行 1-2 分钟
  ⏭️  无任何操作
```

---

## ⚠️ 注意事项

1. **prerelease 不稳定**
   - 可能包含 bug
   - 仅用于测试
   - 不建议日常使用

2. **release 才是正式版**
   - 与 upstream 同步
   - 经过充分测试
   - 用户可放心使用

3. **版本号同步**
   - prerelease：自动升级 patch
   - release：与 upstream 完全一致

4. **编译失败处理**
   - 工作流失败时，会在 Actions 显示
   - 邮件通知（GitHub 默认）
   - 可手动重试

---

## 🔧 配置参数

### Cron 时间表

当前配置：`0 0 * * *`（每天 UTC 00:00）

**支持其他配置：**
- `0 0 * * 0` - 每周 1 次（周日）
- `0 0 1 * *` - 每月 1 次
- `0 */6 * * *` - 每 6 小时 1 次

修改方式：编辑 `.github/workflows/sync-fork.yml` 的 `cron` 值

---

## 📈 预期效果

**每月预期发布：**
- prerelease：5-10 个（根据 upstream 更新频率）
- release：1-2 个（根据 upstream 发布频率）

**用户获得：**
- ✅ 最新代码的快速访问
- ✅ 测试新功能的机会
- ✅ 正式稳定版本的及时同步
- ✅ 多架构 APK（ARM V7 + Universal）

---

## ❓ 常见问题

### Q: prerelease 和 release 的区别是什么？

A: 
- **prerelease**：upstream 有新代码时自动发布，包含最新功能，但可能不稳定
- **release**：upstream 有新 release 时发布，与 upstream 完全同步，稳定可靠

### Q: 如何禁用自动同步？

A: 在 GitHub 仓库设置中禁用 Actions：
- Settings → Actions → Disable for this repository

### Q: 可以修改检查频率吗？

A: 可以，编辑 `.github/workflows/sync-fork.yml` 修改 cron 表达式

### Q: 如果编译失败怎么办？

A: 
1. 查看 Actions 日志了解失败原因
2. 手动重试工作流
3. 修复代码后再同步

### Q: 版本号会冲突吗？

A: 不会，系统会自动检测并避免重复

---

## 📞 获取帮助

- **工作流日志**：GitHub Actions → 具体工作流 → 查看日志
- **发布页面**：GitHub Releases → 查看发布历史
- **配置文件**：`.github/workflows/sync-fork.yml`
- **计划文档**：`FORK_SYNC_PLAN.md`

---

**自动同步已启动！🚀**

现在你的 fork 会自动保持与 upstream 同步，并智能发布版本。
