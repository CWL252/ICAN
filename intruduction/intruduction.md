# ============================================================
# Git 命令行完整速查表
# ============================================================


# ============================================================
# 1. Git 基础配置
# ============================================================

# 查看 Git 版本
git --version

# 设置全局用户名
git config --global user.name "用户名"

# 设置全局邮箱
git config --global user.email "邮箱"

# 查看所有 Git 配置
git config --list

# 查看全局配置
git config --global --list

# 查看当前仓库配置
git config --local --list

# 查看用户名
git config user.name

# 查看邮箱
git config user.email

# 设置默认分支名为 main
git config --global init.defaultBranch main

# 设置默认编辑器
git config --global core.editor "编辑器"

# Windows 设置换行符
git config --global core.autocrlf true

# Linux / macOS 设置换行符
git config --global core.autocrlf input


# ============================================================
# 2. 创建 / 克隆仓库
# ============================================================

# 初始化 Git 仓库
git init

# 克隆仓库
git clone 仓库地址

# 克隆到指定目录
git clone 仓库地址 目录名

# 克隆指定分支
git clone -b 分支名 --single-branch 仓库地址

# 只克隆指定分支最新提交
git clone --depth 1 -b 分支名 --single-branch 仓库地址

# 浅克隆仓库
git clone --depth 1 仓库地址


# ============================================================
# 3. 查看仓库状态
# ============================================================

# 查看当前状态
git status

# 简洁查看状态
git status -s

# 查看当前所在分支
git branch --show-current

# 查看工作区修改
git diff

# 查看暂存区修改
git diff --cached

# 查看工作区和暂存区相对 HEAD 的所有修改
git diff HEAD

# 查看某个文件修改
git diff 文件名


# ============================================================
# 4. 添加文件到暂存区
# ============================================================

# 添加指定文件
git add 文件名

# 添加指定目录
git add 目录名

# 添加当前目录所有修改
git add .

# 添加所有修改，包括删除
git add -A

# 添加已跟踪文件的修改和删除
git add -u

# 交互式添加
git add -p


# ============================================================
# 5. 提交 Commit
# ============================================================

# 创建提交
git commit -m "提交说明"

# 打开编辑器填写提交说明
git commit

# 修改上一次提交说明
git commit --amend

# 修改上一次提交，同时不改提交信息
git commit --amend --no-edit

# 跳过 add，直接提交已跟踪文件
git commit -am "提交说明"


# ============================================================
# 6. 查看提交历史
# ============================================================

# 查看提交历史
git log

# 单行显示
git log --oneline

# 图形化显示分支历史
git log --oneline --graph --decorate --all

# 查看最近 N 条提交
git log -n N

# 查看指定文件历史
git log -- 文件名

# 查看每次提交的具体修改
git log -p

# 查看某次提交
git show 提交ID

# 查看某次提交的文件统计
git show --stat 提交ID

# 查看提交之间差异
git diff 提交ID1 提交ID2


# ============================================================
# 7. 分支管理
# ============================================================

# 查看本地分支
git branch

# 查看所有分支
git branch -a

# 查看远程分支
git branch -r

# 查看分支详细信息
git branch -vv

# 创建分支
git branch 分支名

# 切换分支
git switch 分支名

# 创建并切换分支
git switch -c 分支名

# 从指定分支创建新分支
git switch -c 新分支名 原分支名

# 老式切换分支命令
git checkout 分支名

# 老式创建并切换
git checkout -b 分支名

# 重命名当前分支
git branch -m 新分支名

# 重命名指定分支
git branch -m 原分支名 新分支名

# 删除已经合并的本地分支
git branch -d 分支名

# 强制删除本地分支
git branch -D 分支名


# ============================================================
# 8. 远程仓库 Remote
# ============================================================

# 查看远程仓库
git remote

# 查看远程仓库详细地址
git remote -v

# 查看指定远程详细信息
git remote show origin

# 添加远程仓库
git remote add origin 仓库地址

# 修改远程仓库地址
git remote set-url origin 仓库地址

# 删除远程仓库
git remote remove origin

# 重命名远程仓库
git remote rename 原名称 新名称


# ============================================================
# 9. 推送 Push
# ============================================================

# 推送当前分支
git push

# 推送指定分支
git push origin 分支名

# 第一次推送并建立追踪关系
git push -u origin 分支名

# 推送所有本地分支
git push origin --all

# 推送所有标签
git push origin --tags

# 删除远程分支
git push origin --delete 分支名

# 安全强制推送
git push --force-with-lease

# 强制推送
# 高风险，多人协作慎用
git push --force


# ============================================================
# 10. 获取远程更新 Fetch
# ============================================================

# 获取远程更新，但不合并
git fetch

# 获取 origin 更新
git fetch origin

# 获取所有远程仓库
git fetch --all

# 删除已经不存在的远程分支引用
git fetch --prune

# 获取并清理
git fetch --all --prune


# ============================================================
# 11. 拉取 Pull
# ============================================================

# 拉取当前分支
git pull

# 拉取指定远程分支
git pull origin 分支名

# 拉取并使用 rebase
git pull --rebase

# 拉取指定分支并 rebase
git pull --rebase origin 分支名

# 只允许快进更新
git pull --ff-only


# ============================================================
# 12. Merge 合并分支
# ============================================================

# 将指定分支合并到当前分支
git merge 分支名

# 禁止 fast-forward，保留合并节点
git merge --no-ff 分支名

# 只允许 fast-forward
git merge --ff-only 分支名

# 中止正在进行的合并
git merge --abort


# ============================================================
# 13. Rebase 变基
# ============================================================

# 将当前分支变基到指定分支
git rebase 分支名

# 交互式整理最近 N 个提交
git rebase -i HEAD~N

# 冲突解决后继续 rebase
git rebase --continue

# 跳过当前提交
git rebase --skip

# 中止 rebase
git rebase --abort


# ============================================================
# 14. 多人协作标准流程
# ============================================================

# 获取远程最新状态
git fetch origin

# 切换到主分支
git switch main

# 更新主分支
git pull --ff-only origin main

# 创建自己的功能分支
git switch -c 功能分支名

# 修改代码后查看状态
git status

# 添加修改
git add .

# 提交
git commit -m "提交说明"

# 再次同步远程 main
git fetch origin

# 将自己的分支基于最新 main 变基
git rebase origin/main

# 第一次推送功能分支
git push -u origin 功能分支名

# 后续继续推送
git push


# ============================================================
# 15. 多人协作：更新自己的功能分支
# ============================================================

# 获取远程最新代码
git fetch origin

# 当前功能分支变基到最新 main
git rebase origin/main

# 如果该分支之前已经推送过，rebase 后通常需要
git push --force-with-lease


# ============================================================
# 16. 多人协作：使用 Merge 同步 main
# ============================================================

git fetch origin

git switch 功能分支名

git merge origin/main

git push


# ============================================================
# 17. 多人协作：更新本地主分支
# ============================================================

git switch main

git fetch origin

git pull --ff-only origin main


# ============================================================
# 18. 多人协作：远程新增了分支
# ============================================================

# 获取远程分支
git fetch origin

# 查看远程分支
git branch -r

# 创建对应本地分支
git switch -c 分支名 --track origin/分支名


# ============================================================
# 19. 多人协作：删除已合并功能分支
# ============================================================

# 切换到 main
git switch main

# 更新 main
git pull

# 删除本地功能分支
git branch -d 功能分支名

# 删除远程功能分支
git push origin --delete 功能分支名

# 清理本地远程引用
git fetch --prune


# ============================================================
# 20. 冲突处理
# ============================================================

# 查看冲突文件
git status

# 手动修改冲突文件后添加
git add 冲突文件

# Merge 冲突解决后提交
git commit

# Rebase 冲突解决后继续
git rebase --continue

# 放弃 merge
git merge --abort

# 放弃 rebase
git rebase --abort


# ============================================================
# 21. Stash 临时保存修改
# ============================================================

# 临时保存当前修改
git stash

# 保存并填写说明
git stash push -m "说明"

# 包括未跟踪文件
git stash -u

# 查看 stash
git stash list

# 恢复最近一次 stash，并保留 stash
git stash apply

# 恢复指定 stash
git stash apply stash@{N}

# 恢复最近 stash 并删除 stash
git stash pop

# 删除指定 stash
git stash drop stash@{N}

# 删除所有 stash
git stash clear


# ============================================================
# 22. 撤销工作区修改
# ============================================================

# 撤销指定文件未提交修改
git restore 文件名

# 撤销所有未提交修改
git restore .

# 用指定提交版本恢复文件
git restore --source=提交ID 文件名


# ============================================================
# 23. 撤销 git add
# ============================================================

# 将指定文件移出暂存区
git restore --staged 文件名

# 清空整个暂存区
git restore --staged .


# ============================================================
# 24. Reset 回退
# ============================================================

# 回退提交，但保留修改在暂存区
git reset --soft HEAD~1

# 回退提交，修改保留在工作区
git reset HEAD~1

# 等价于 mixed
git reset --mixed HEAD~1

# 回退提交，并彻底丢弃修改
# 高风险
git reset --hard HEAD~1

# 回退到指定提交
git reset --hard 提交ID

# 将本地完全恢复成远程 main
# 高风险，会丢弃本地未提交修改
git fetch origin
git reset --hard origin/main


# ============================================================
# 25. Revert 安全撤销提交
# ============================================================

# 创建一个新提交，用于撤销某次提交
git revert 提交ID

# 撤销最近一次提交
git revert HEAD

# 撤销 merge commit
git revert -m 1 合并提交ID


# ============================================================
# 26. Reset 和 Revert 使用原则
# ============================================================

# 未推送的个人提交：
# 可以使用 reset

# 已经推送到多人共享分支的提交：
# 推荐使用 revert


# ============================================================
# 27. Cherry-pick 选择某个提交
# ============================================================

# 将指定提交应用到当前分支
git cherry-pick 提交ID

# 应用多个提交
git cherry-pick 提交ID1 提交ID2

# 冲突解决后继续
git cherry-pick --continue

# 中止 cherry-pick
git cherry-pick --abort


# ============================================================
# 28. 删除文件
# ============================================================

# 删除文件并加入暂存区
git rm 文件名

# 删除目录
git rm -r 目录名

# 只取消 Git 跟踪，但保留本地文件
git rm --cached 文件名

# 取消跟踪目录
git rm -r --cached 目录名


# ============================================================
# 29. 移动 / 重命名文件
# ============================================================

git mv 原文件名 新文件名

git mv 原目录 新目录


# ============================================================
# 30. .gitignore
# ============================================================

# 查看被忽略文件
git status --ignored

# 检查文件为什么被忽略
git check-ignore -v 文件名

# 如果文件已经被 Git 跟踪，需要先取消跟踪
git rm --cached 文件名

# 目录
git rm -r --cached 目录名


# ============================================================
# 31. 标签 Tag
# ============================================================

# 查看标签
git tag

# 创建轻量标签
git tag 标签名

# 创建带说明的标签
git tag -a 标签名 -m "标签说明"

# 给指定提交创建标签
git tag 标签名 提交ID

# 查看标签信息
git show 标签名

# 推送指定标签
git push origin 标签名

# 推送所有标签
git push origin --tags

# 删除本地标签
git tag -d 标签名

# 删除远程标签
git push origin --delete 标签名


# ============================================================
# 32. 查看文件历史
# ============================================================

# 查看文件提交历史
git log -- 文件名

# 跟踪文件重命名前后的历史
git log --follow -- 文件名

# 查看每一行是谁修改的
git blame 文件名


# ============================================================
# 33. 查找提交
# ============================================================

# 按提交信息搜索
git log --grep="关键词"

# 按作者搜索
git log --author="作者"

# 查找添加或删除指定字符串的提交
git log -S "关键词"

# 查看某时间之后的提交
git log --since="日期"

# 查看某时间之前的提交
git log --until="日期"


# ============================================================
# 34. Reflog 恢复误操作
# ============================================================

# 查看 HEAD 历史移动记录
git reflog

# 恢复到某个历史状态
git reset --hard HEAD@{N}

# 或
git reset --hard 提交ID


# ============================================================
# 35. Clean 清理未跟踪文件
# ============================================================

# 预览将删除哪些文件
git clean -n

# 删除未跟踪文件
git clean -f

# 删除未跟踪目录
git clean -fd

# 包括被 .gitignore 忽略的文件
# 高风险
git clean -fdx


# ============================================================
# 36. 查看哪些分支已经合并
# ============================================================

# 已合并到当前分支
git branch --merged

# 尚未合并
git branch --no-merged


# ============================================================
# 37. 比较分支
# ============================================================

# 比较两个分支内容
git diff 分支A 分支B

# 查看分支A有而分支B没有的提交
git log 分支B..分支A --oneline

# 查看两个分支分叉情况
git log --left-right --graph 分支A...分支B


# ============================================================
# 38. 设置上游分支
# ============================================================

# 当前分支关联远程分支
git branch --set-upstream-to=origin/分支名

# 推送同时建立关联
git push -u origin 分支名

# 查看追踪关系
git branch -vv


# ============================================================
# 39. Fork 多人协作常用 Remote
# ============================================================

# 查看 remote
git remote -v

# 添加上游原仓库
git remote add upstream 上游仓库地址

# 获取上游仓库更新
git fetch upstream

# 更新本地 main
git switch main
git merge upstream/main

# 或使用 rebase
git switch main
git rebase upstream/main

# 将更新推送到自己的 fork
git push origin main


# ============================================================
# 40. Fork 功能分支开发
# ============================================================

git fetch upstream

git switch main

git rebase upstream/main

git push origin main

git switch -c 功能分支名

git add .

git commit -m "提交说明"

git push -u origin 功能分支名


# ============================================================
# 41. 查看远程仓库状态
# ============================================================

# 查看远程详细信息
git remote show origin

# 获取远程引用
git ls-remote origin

# 查看远程所有分支
git branch -r


# ============================================================
# 42. 修改提交作者信息
# ============================================================

# 修改最近一次提交作者
git commit --amend --author="用户名 <邮箱>"

# 修改 Git 用户名
git config user.name "用户名"

# 修改 Git 邮箱
git config user.email "邮箱"


# ============================================================
# 43. Git Bisect 定位 Bug
# ============================================================

# 开始二分查找
git bisect start

# 标记当前版本有问题
git bisect bad

# 标记某个历史版本正常
git bisect good 提交ID

# 当前测试正常
git bisect good

# 当前测试异常
git bisect bad

# 结束
git bisect reset


# ============================================================
# 44. Git Worktree 多分支同时工作
# ============================================================

# 查看 worktree
git worktree list

# 在另一个目录检出指定分支
git worktree add 路径 分支名

# 创建新分支并建立 worktree
git worktree add -b 新分支名 路径

# 删除 worktree
git worktree remove 路径

# 清理失效 worktree
git worktree prune


# ============================================================
# 45. Git Submodule 子模块
# ============================================================

# 添加子模块
git submodule add 仓库地址 路径

# 初始化子模块
git submodule init

# 更新子模块
git submodule update

# 克隆仓库时同时获取子模块
git clone --recurse-submodules 仓库地址

# 更新所有子模块
git submodule update --init --recursive

# 拉取子模块最新版本
git submodule update --remote


# ============================================================
# 46. Git LFS 大文件
# ============================================================

# 初始化 Git LFS
git lfs install

# 跟踪某种大文件
git lfs track "*.扩展名"

# 查看 LFS 跟踪规则
git lfs track

# 查看 LFS 文件
git lfs ls-files

# 拉取 LFS 文件
git lfs pull


# ============================================================
# 47. 保存补丁 Patch
# ============================================================

# 生成补丁
git format-patch HEAD~N

# 应用补丁
git am 补丁文件

# 生成普通 diff
git diff > 修改.patch

# 应用普通 diff
git apply 修改.patch


# ============================================================
# 48. 查看仓库大小和对象
# ============================================================

git count-objects -vH

git gc

git gc --prune=now


# ============================================================
# 49. 常见安全操作
# ============================================================

# 操作前先查看状态
git status

# 拉取前先获取远程信息
git fetch origin

# 查看远程和本地差异
git log HEAD..origin/main --oneline

# 查看本地尚未推送提交
git log origin/main..HEAD --oneline

# 推送前确认分支
git branch --show-current

# 推送前确认 remote
git remote -v


# ============================================================
# 50. 多人协作推荐工作流
# ============================================================

# ---- 开始工作 ----

git switch main

git fetch origin

git pull --ff-only origin main

git switch -c 功能分支名


# ---- 编写代码 ----

git status

git add .

git commit -m "提交说明"


# ---- 同步其他人的最新修改 ----

git fetch origin

git rebase origin/main


# ---- 如果发生冲突 ----

git status

# 手动解决冲突

git add 冲突文件

git rebase --continue


# ---- 推送自己的分支 ----

git push -u origin 功能分支名


# ---- 后续继续修改 ----

git add .

git commit -m "提交说明"

git push


# ---- 如果 rebase 后需要重新推送 ----

git push --force-with-lease


# ============================================================
# 51. 主分支多人协作推荐规则
# ============================================================

# 获取更新
git fetch origin

# 更新 main
git switch main
git pull --ff-only origin main

# 不推荐直接在 main 上开发
# 推荐从 main 创建功能分支
git switch -c 功能分支名

# 开发完成提交
git add .
git commit -m "提交说明"

# 同步最新 main
git fetch origin
git rebase origin/main

# 推送功能分支
git push -u origin 功能分支名


# ============================================================
# 52. Git 最重要的工作区关系
# ============================================================

# 工作区
#    ↓ git add
# 暂存区
#    ↓ git commit
# 本地仓库
#    ↓ git push
# 远程仓库

# 远程仓库
#    ↓ git fetch / git pull
# 本地仓库
#    ↓ checkout / switch / restore
# 工作区


# ============================================================
# 53. 最常用命令
# ============================================================

git status

git branch

git switch 分支名

git switch -c 新分支名

git fetch origin

git pull

git pull --rebase

git add .

git commit -m "提交说明"

git push

git push -u origin 分支名

git log --oneline --graph --decorate --all

git diff

git stash

git stash pop

git merge 分支名

git rebase 分支名

git restore 文件名

git restore --staged 文件名

git reflog


# ============================================================
# 54. 高风险命令 —— 执行前务必确认
# ============================================================

# 强制删除本地分支
git branch -D 分支名

# 丢弃所有本地修改
git reset --hard HEAD

# 回退到指定提交并丢弃之后的工作
git reset --hard 提交ID

# 强制覆盖远程
git push --force

# 相对安全的强制推送
git push --force-with-lease

# 删除所有未跟踪文件和目录
git clean -fd

# 连 .gitignore 忽略内容一起删除
git clean -fdx