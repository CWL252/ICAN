# Contributing to CholecInsight

欢迎参与 `CholecInsight` 的开发。

这份文档面向项目协作者，目标是帮助团队成员在进入仓库后，快速理解开发方式、分支规则、提交流程和联调注意事项。

## 1. 开始之前

在开始提交代码前，请先完成这几件事：

1. 阅读 [README.md](/D:/Codex/SrugAI/CholecInsight/README.md)
2. 阅读 [docs/Git_Standard.md](/D:/Codex/SrugAI/CholecInsight/docs/Git_Standard.md)
3. 阅读 [docs/PULL_REQUEST_TEMPLATE.md](/D:/Codex/SrugAI/CholecInsight/docs/PULL_REQUEST_TEMPLATE.md)
4. 如果涉及接口、字段、模型输出变更，再阅读 [docs/API_norm.md](/D:/Codex/SrugAI/CholecInsight/docs/API_norm.md)

## 2. 开发环境

当前项目采用前后端分离结构：

- `frontend/`：Vue 3 + Vite
- `backend/`：FastAPI + PyTorch

建议本地环境：

- Node.js 18+
- npm 9+
- Python 3.8+

### 权重文件

预训练权重**不存放在 GitHub 仓库中**，需要从项目维护者提供的百度网盘单独下载，并放到：

```text
backend/pretrained_weights/
```

当前需要的文件：

- `cnn_checkpoint_best_acc.pth.tar`
- `head_checkpoint_best_acc.pth.tar`

## 3. 分支规则

请统一使用以下分支模型：

- `main`：稳定分支，用于可演示、可交付版本
- `develop`：日常集成分支
- `feature/*`：新功能开发
- `fix/*`：常规问题修复
- `hotfix/*`：紧急修复

### 基本要求

- 不要直接在 `main` 上开发
- 日常开发从 `develop` 拉取并创建个人分支
- 一人一分支，不共用功能分支
- 一个分支尽量只解决一个主题

### 推荐命名

```text
feature/frontend-project-list
feature/backend-phase-job-api
fix/frontend-upload-state
fix/backend-empty-response
```

## 4. 推荐工作流

### 4.1 同步最新代码

```bash
git checkout develop
git pull origin develop
```

### 4.2 创建个人开发分支

```bash
git checkout -b feature/your-feature-name
```

### 4.3 本地开发与自测

提交前至少确认：

- 前端可以正常启动
- 后端可以正常启动
- 你改动的核心流程可以走通
- 没有把本地缓存、运行时文件、权重文件误提交

### 4.4 推送个人分支

```bash
git push -u origin feature/your-feature-name
```

### 4.5 发起 Pull Request

默认目标分支为 `develop`。

只有在阶段发布、对外交付或经过团队确认时，才从 `develop` 合并到 `main`。

## 5. Commit 规范

统一使用：

```text
type(scope): summary
```

常用类型：

- `feat`：新功能
- `fix`：缺陷修复
- `docs`：文档更新
- `refactor`：重构
- `test`：测试相关
- `chore`：工程配置、依赖或脚本调整

示例：

```bash
git commit -m "feat(frontend): add project creation flow"
git commit -m "feat(backend): add phase job polling endpoint"
git commit -m "fix(frontend): handle missing project video"
git commit -m "docs(contributing): add team workflow guide"
```

不建议使用这类提交信息：

```text
update
fix bug
修改一下
final
```

## 6. Pull Request 要求

每个 PR 应尽量小而清晰，并至少说明：

- 这次改动解决了什么问题
- 改动范围涉及哪些模块
- 是否影响前端、后端、算法接口
- 是否需要联调
- 是否补充了必要文档

建议直接参考：

- [docs/PULL_REQUEST_TEMPLATE.md](/D:/Codex/SrugAI/CholecInsight/docs/PULL_REQUEST_TEMPLATE.md)

### PR 合并前检查

- 本地已完成基本自测
- 已同步最新 `develop`
- 没有明显冲突
- 没有误提交 `node_modules`、`dist`、运行时目录、权重文件
- 如涉及接口变更，已通知相关成员

## 7. 接口与数据变更协作

以下改动不要直接“先写了再说”，而是要先同步团队：

- 接口路径变化
- 请求参数变化
- 返回字段变化
- 模型输入输出字段变化
- 标签命名变化
- 影响前后端联调的结构变化

原则是：

1. 先约定
2. 再开发
3. 再联调

如果涉及这些内容，请同步更新相关文档，优先维护在 `docs/` 目录下。

## 8. 目录协作建议

为了减少冲突，建议优先在自己负责的目录内改动：

- 前端相关：`frontend/`
- 后端相关：`backend/`
- 规范文档：`docs/`

如果必须跨目录改动，请在 commit 和 PR 描述里说明原因。

## 9. 不要提交这些内容

以下内容默认不应提交到仓库：

- `frontend/node_modules/`
- `frontend/dist/`
- `backend/runtime/`
- `__pycache__/`
- 本地虚拟环境
- 日志文件
- 临时导出文件
- 预训练权重文件
- 未脱敏数据

仓库当前已经通过 `.gitignore` 排除了大部分本地文件，但提交前仍建议自己再检查一次 `git status`。

## 10. 适合当前阶段的最小协作规则

如果团队刚开始多人并行开发，至少先执行这几条：

1. 不直接修改 `main`
2. 所有开发从 `develop` 拉分支
3. 一人一分支
4. 一个 PR 只做一件事
5. 接口变更必须提前同步
6. 合并前至少有一次 review

## 11. 有问题时怎么沟通

如果你发现以下情况，建议尽快在团队里同步，而不是自己硬改：

- 不确定接口字段该怎么定
- 模型输出和前端展示对不上
- 分支冲突较大
- 发现现有实现与 README 或 docs 描述不一致
- 本地能跑但联调不通

越早同步，后面的返工越少。
