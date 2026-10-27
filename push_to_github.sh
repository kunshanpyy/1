#!/usr/bin/env bash
# ============================================================
#  一键推送脚本  (push_to_github.sh)
#  适用范围: Windows 上的 Git Bash（右键项目文件夹 -> Git Bash Here）
#  用法:       bash push_to_github.sh
#
#  说明:
#   1. 本脚本把本地已提交的完整代码推送到 GitHub 仓库
#      https://github.com/kunshanpyy/1
#   2. 远程仓库此前网页上传过零散文件，因此推送时会用
#      --force 覆盖它们（你自己的仓库，安全）。
#   3. 若提示 main 分支禁止 force push，请到 GitHub 仓库
#      Settings -> Branches 关闭分支保护，或删库重建空仓库。
#   4. 认证: 推送时用户名填 GitHub 账号；
#      密码/令牌处粘贴 Personal Access Token（不是账号密码）。
#      生成地址: https://github.com/settings/tokens （勾选 repo 权限）
# ============================================================

set -e

# 切换到脚本所在目录（即项目根目录 D:\作业\分割\code）
cd "$(dirname "$0")"

echo "==> 当前目录: $(pwd)"

# ---- 分支 ----
BRANCH=$(git branch --show-current 2>/dev/null || true)
if [ "$BRANCH" != "main" ]; then
  echo "==> 将分支重命名为 main"
  git branch -m main 2>/dev/null || true
fi
echo "==> 当前分支: $(git branch --show-current)"

# ---- 远程 ----
TARGET_REMOTE="https://github.com/kunshanpyy/1.git"
REMOTE=$(git remote get-url origin 2>/dev/null || true)
if [ -z "$REMOTE" ]; then
  echo "==> 未检测到 origin，已添加: $TARGET_REMOTE"
  git remote add origin "$TARGET_REMOTE"
elif [ "$REMOTE" != "$TARGET_REMOTE" ]; then
  echo "==> 远程 origin 与预期不符，已修正为: $TARGET_REMOTE"
  git remote set-url origin "$TARGET_REMOTE"
else
  echo "==> 已配置远程 origin: $REMOTE"
fi

# ---- 工作区检查 ----
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️  工作区有未提交改动，先为你暂存并提交:"
  git add -A
  git commit -m "chore: auto-commit before push" || true
fi

# ---- 待推送内容预览 ----
echo "==> 本地待推送的最近提交:"
git log --oneline -5
echo "==> 将推送的文件数: $(git ls-files | wc -l)"

# ---- 推送 ----
echo ""
echo "==> 开始推送... (用户名=GitHub账号, 密码处粘贴 Token)"
echo ""
if git push -u origin main; then
  echo "✅ 普通推送成功"
else
  echo "⚠️  普通推送失败，尝试强制推送（覆盖远程历史）..."
  git push -u origin main --force
  echo "✅ 强制推送成功"
fi

echo ""
echo "🎉 完成！仓库地址: https://github.com/kunshanpyy/1"
