# 🚀 Release 快速参考

## 发布新版本只需 3 步

### 1️⃣ 升级版本号（本地）

```bash
# 查看当前版本
./scripts/bump-version.sh current

# 选择一种方式升级：
./scripts/bump-version.sh major   # 1.7.7 → 2.0.0
./scripts/bump-version.sh minor   # 1.7.7 → 1.8.0
./scripts/bump-version.sh patch   # 1.7.7 → 1.7.8

# 或指定具体版本
./scripts/bump-version.sh 1.8.0
```

脚本会自动：
- ✅ 更新 `app/build.gradle.kts`
- ✅ 递增 versionCode
- ✅ 创建 Git 提交和 Tag
- ✅ 提示下一步操作

### 2️⃣ 推送到 GitHub

```bash
# 推送代码和 Tag
git push origin master
git push origin v1.8.0
```

### 3️⃣ 创建 Release

**方式 A：使用 GitHub Actions（推荐）**
1. GitHub → **Actions**
2. **Create Release** 工作流
3. **Run workflow** → 输入版本号
4. ✅ 自动编译 + 发布

**方式 B：手动创建**
1. GitHub → **Releases** → **Draft a new release**
2. 选择 Tag: `v1.8.0`
3. **Publish release**

---

## 📊 版本号规则

```
版本格式: MAJOR.MINOR.PATCH

升级场景：
- MAJOR → 重大功能变更 (1.0.0 → 2.0.0)
- MINOR → 新增功能 (1.7.0 → 1.8.0)
- PATCH → Bug 修复 (1.7.7 → 1.7.8)
```

---

## 📦 Release 包含内容

- ✅ ARM V7a APK (32-bit，适合老设备)
- ✅ Universal APK (64-bit，适合新设备)
- ✅ 自动生成的 Release 说明
- ✅ 安装和使用指南

---

## 🎯 常见命令速查

| 目的 | 命令 |
|------|------|
| 查看版本 | `./scripts/bump-version.sh current` |
| 修复版本 | `./scripts/bump-version.sh patch` |
| 新增功能 | `./scripts/bump-version.sh minor` |
| 大更新 | `./scripts/bump-version.sh major` |
| 指定版本 | `./scripts/bump-version.sh 1.8.0` |

---

## ❓ 出现问题？

查看完整指南：[VERSION_MANAGEMENT.md](../VERSION_MANAGEMENT.md)

**祝你发布顺利！🎉**
