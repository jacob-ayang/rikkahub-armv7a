# Fork 自动同步计划

## 📋 目标
自动定期将 upstream (rikkahub/rikkahub) 的变更同步到 fork (jacob-ayang/rikkahub-armv7a)，保持代码与上游一致。

---

## 🔍 当前状态

| 项目 | 状态 |
|------|------|
| Fork 仓库 | ✅ jacob-ayang/rikkahub-armv7a |
| Upstream | ✅ rikkahub/rikkahub |
| 远程配置 | ✅ 已配置 upstream remote |
| 同步状态 | ✅ 当前已同步（无落后提交） |

---

## 📊 可行方案对比

### 方案 A：GitHub Actions 定期同步（⭐ 推荐）

**原理：** 创建 GitHub Actions 工作流，定期运行 sync 任务

**优点：**
- ✅ 完全自动化，无需手动干预
- ✅ 灵活的时间表配置（每天/每周等）
- ✅ 可创建自动 PR，支持人工审查
- ✅ 失败时会发送通知
- ✅ 保持完整的 Git 历史
- ✅ 可与当前 ARM V7 工作流兼容

**缺点：**
- ⚠️ 如果有冲突需要手动解决
- ⚠️ 需要额外的 GitHub Actions 分钟数

**实现方式：**
```yaml
# 定期运行（例：每天午夜）
schedule:
  - cron: '0 0 * * *'

步骤：
1. git fetch upstream
2. git merge upstream/master
3. git push origin master
```

**冲突处理：**
- 自动冲突：发邮件通知，创建 Draft PR
- 手动解决：在本地解决冲突后推送

---

### 方案 B：GitHub 的 "Sync Fork" 按钮（简化）

**原理：** 使用 GitHub 内置的 fork sync 功能

**优点：**
- ✅ 最简单，点一下按钮即可
- ✅ GitHub 官方支持
- ✅ 无额外配置

**缺点：**
- ⚠️ 需要手动点击，无法自动化
- ⚠️ 只能做快进合并 (fast-forward)
- ⚠️ 无法处理复杂冲突

**何时使用：**
- 简单场景，偶尔同步一次
- 没有本地定制化代码的 fork

---

### 方案 C：GitHub App（Dependabot/Renovate）

**原理：** 使用自动化机器人定期检查和更新

**优点：**
- ✅ 功能强大
- ✅ 自动创建 PR

**缺点：**
- ⚠️ 主要用于依赖更新，非最优
- ⚠️ 配置复杂

---

### 方案 D：本地脚本 + Cron 定时任务（手动服务器）

**原理：** 在本地或服务器定期运行 sync 脚本

**优点：**
- ✅ 完全控制

**缺点：**
- ⚠️ 需要 24/7 运行的服务器
- ⚠️ 维护成本高

---

## 🎯 推荐方案

**采用 方案 A（GitHub Actions 定期同步）**，理由：
1. ✅ 完全自动化，无需手动操作
2. ✅ 与现有 ARM V7 工作流兼容
3. ✅ GitHub 免费额度足够用
4. ✅ 支持自动 PR，保持审查机制
5. ✅ 失败时有通知，可及时处理
6. ✅ 便于追踪 upstream 变更

---

## 📝 实现细节

### 工作流配置

**文件位置：** `.github/workflows/sync-fork.yml`

**主要功能：**
1. 定期检查 upstream 更新（每天午夜）
2. 自动 fetch upstream
3. 自动 merge 或创建 PR
4. 失败时发邮件通知

**配置示例：**
```yaml
name: Sync Fork

on:
  schedule:
    - cron: '0 0 * * *'  # 每天午夜 UTC 时间
  workflow_dispatch:      # 支持手动触发

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Sync fork
        run: |
          git config user.name "github-actions"
          git config user.email "github-actions@github.com"
          
          git fetch upstream
          git merge upstream/master || {
            # 冲突处理
            git merge --abort
            # 创建 PR 通知
          }
```

### 同步时间表选项

**选项 1：每天同步（推荐）**
```
0 0 * * *
```
- 优点：及时获得 upstream 更新
- 缺点：可能频繁触发
- 适用：活跃的 upstream 仓库

**选项 2：每周同步**
```
0 0 * * 0
```
- 优点：减少同步频率
- 缺点：可能漂离较多
- 适用：upstream 更新不频繁

**选项 3：每月同步**
```
0 0 1 * *
```
- 优点：最少的同步频率
- 缺点：累积较多变更
- 适用：仅获取重大更新

---

## 🔧 冲突处理策略

### 场景 1：无冲突（自动合并）
```
✅ 自动合并 upstream/master 到本地 master
✅ 自动推送到 origin master
✅ 无需人工干预
```

### 场景 2：有冲突（自动创建 PR）
```
❌ 检测到合并冲突
→ 中止自动合并
→ 创建 Draft PR "chore: sync upstream"
→ 发邮件通知
→ 人工审查和解决
→ PR 合并后自动关闭
```

**冲突解决建议：**
1. 接受 upstream 版本（如果是 core 代码）
2. 保留本地版本（如果是 ARM V7 特定代码）
3. 手动合并（如果都需要）

---

## 💾 存储冲突日志

实现方案记录冲突历史，便于追踪：
- 何时发生冲突
- 涉及哪些文件
- 解决方案

**日志文件：** `.github/sync-log.md`

---

## 🚀 实施步骤

### Phase 1：准备（5 分钟）
- [ ] 审阅本计划
- [ ] 确认推荐方案（方案 A）
- [ ] 获批进行

### Phase 2：实现（20 分钟）
- [ ] 创建 `sync-fork.yml` 工作流
- [ ] 配置 cron 时间表
- [ ] 测试工作流
- [ ] 推送到 GitHub

### Phase 3：验证（10 分钟）
- [ ] 手动触发工作流
- [ ] 检查 upstream 变更
- [ ] 验证合并结果

### Phase 4：持续维护（日常）
- [ ] 监控工作流运行
- [ ] 处理冲突 PR
- [ ] 定期审查日志

---

## 📊 成本分析

**GitHub Actions 用量：**
- 工作流频率：每天 1 次
- 预计时间：1-2 分钟/次
- 月度用量：30-60 分钟

**GitHub 免费额度：** 2000 分钟/月
- 💰 完全免费！

---

## ⚠️ 风险评估

| 风险 | 概率 | 影响 | 缓解方案 |
|------|------|------|---------|
| 自动冲突 | 低 | 创建 PR，手动解决 | 定期审查 upstream |
| 意外覆盖 | 极低 | 本地变更丢失 | 使用 merge 而非 rebase |
| 工作流失败 | 中 | 同步中断 | 邮件通知 + 手动触发 |
| 依赖过期 | 低 | 编译失败 | 单独的依赖更新工作流 |

---

## 📋 检查清单

在实施前，确认：
- [ ] 仓库权限：能修改工作流
- [ ] upstream 配置：已正确配置
- [ ] 本地分支：master 是主开发分支
- [ ] 远程权限：能推送到 origin
- [ ] GitHub Actions：已启用

---

## 💡 后续考虑

### 长期维护
- 定期审查同步日志
- 监控是否有频繁冲突
- 考虑定制化代码的隔离

### 扩展功能
- 同时同步其他分支（dev/feature 等）
- 自动更新依赖版本
- 集成 Slack 通知
- 生成同步报告

---

## 📞 最终决策

✅ **已批准并实施**

### 决策总结

1. **采用方案 A：GitHub Actions 定期同步** ✅
2. **同步频率：每天 UTC 00:00** ✅
3. **冲突处理：自动合并（无冲突时）** ✅
4. **高级功能：智能版本发布** ✅

---

## 🚀 最终实现方案

### 核心逻辑

```
每天自动运行 sync-fork.yml 工作流：

1️⃣ 检查 upstream 是否有新提交
   ├─ 有新提交 → 自动 merge
   │  └─ 升级版本号（patch）
   │     └─ 发布 prerelease 版本
   └─ 无新提交 → 跳过

2️⃣ 检查 upstream 是否有新 release 标签
   ├─ 有新 release → 同步该版本
   │  ├─ 创建本地 tag
   │  └─ 发布正式 release 版本
   └─ 无新 release → 跳过
```

### 三个工作流 Job

**Job 1：sync-fork（核心）**
- 检查 upstream 更新
- 检查 upstream release 标签
- 自动 merge upstream/master
- 自动升级版本号
- 输出给后续 job

**Job 2：create-prerelease（条件触发）**
- 条件：有 upstream 代码更新
- 自动编译 ARM V7 + Universal APK
- 发布 prerelease 版本
- 标签：`v{version}-prerelease`

**Job 3：sync-release（条件触发）**
- 条件：upstream 有新 release
- 同步 upstream 版本标签
- 自动编译 ARM V7 + Universal APK
- 发布正式 release 版本
- 标签：`v{upstream-version}`

---

## 📋 行为示例

### 场景 1：upstream 有代码更新（无新 release）

```
时间：每天 UTC 00:00
检测：upstream/master 有 5 个新提交

操作：
1. ✅ 自动 fetch upstream
2. ✅ 自动 merge upstream/master
3. ✅ 升级版本：1.7.7 → 1.7.8
4. ✅ 自动编译 ARM V7 + Universal APK
5. ✅ 发布 prerelease：v1.7.8-prerelease

标签说明：
- prerelease = 不稳定版本
- 自动创建，用户自愿测试
- 包含 upstream 最新代码
```

### 场景 2：upstream 发布新 release

```
时间：每天 UTC 00:00（或任何时间）
检测：upstream 有新 release tag（如：v1.8.0）

操作：
1. ✅ 同步 upstream release tag（v1.8.0）
2. ✅ 创建本地 tag（v1.8.0）
3. ✅ 自动编译 ARM V7 + Universal APK
4. ✅ 发布正式 release：v1.8.0

标签说明：
- release = 正式稳定版本
- 与 upstream 版本号同步
- 用户可直接安装
```

### 场景 3：upstream 无更新

```
时间：每天 UTC 00:00
检测：upstream 无新提交，无新 release

操作：
- 跳过，什么都不做
- 等待下次检查

成本：1-2 分钟执行时间
```

---

## 📊 版本号管理

### 版本号规则

```
上游 release: v1.8.0
   ↓
我们的 release: v1.8.0 (与上游完全一致)

同时：
   ↓ (如果有额外的代码更新)
我们的 prerelease: v1.8.1-prerelease (patch + 1)
```

### 自动升级逻辑

```
upstream 有代码更新时：
- 当前版本：1.7.7
- 新版本：1.7.8 (patch + 1)
- 类型：prerelease

upstream 发布 release 时：
- 当前版本：1.7.7
- 新版本：同 upstream (如 1.8.0)
- 类型：release
```

---

## ⚙️ 手动触发选项

### 手动同步

```bash
GitHub Actions → Sync Fork with Auto Release → Run workflow

选项：
☑️  Force prerelease even without upstream changes
    可选：强制发布 prerelease（即使无 upstream 更新）
```

---

## 🔐 权限和密钥

**必需密钥：**
- ✅ `KEY_BASE64` - Keystore Base64 编码

**权限：**
- ✅ `contents: write` - 创建 release 和 tag
- ✅ `pull-requests: write` - 如需创建 PR（当前未用）

---

## 📊 成本分析

**GitHub Actions 用量：**
- 工作流频率：每天 1 次
- 无更新时：1-2 分钟
- 有更新时：8-12 分钟（含编译）
- 月度用量：约 100-200 分钟

**GitHub 免费额度：** 2000 分钟/月
- 💰 完全免费！

---

## ✅ 实施检查清单

- [x] 创建 sync-fork.yml 工作流
- [x] 配置每日检查（cron: 0 0 * * *）
- [x] 实现自动版本升级
- [x] 实现 prerelease 发布
- [x] 实现 release 同步
- [x] 配置签名凭证
- [x] 测试工作流逻辑
- [ ] 首次推送和手动测试
- [ ] 监控工作流运行

---

## 📚 参考资源

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Syncing a fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork)
- [Scheduled workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)
- [Creating releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)

---

**实现完成！🚀**

工作流已创建并准备就绪。推送后即可自动运行。
