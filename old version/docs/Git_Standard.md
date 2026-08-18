# 智慧外科平台 Git 使用规范

## 1. 适用范围

本规范适用于智慧外科平台项目的所有成员，包括：

- 算法研发：Python 算法开发、训练、推理服务封装
- 前端开发：Vue 3 + Vite + TypeScript
- 后端开发：FastAPI 服务、数据库、算法服务集成
- 项目负责人、产品、医学顾问参与的文档与需求协作

目标是保证团队在多人并行开发时做到：

- 主分支稳定可运行
- 每个人可以独立开发、减少互相等待
- 接口改动可追踪
- 联调、测试、演示版本清晰

## 2. 仓库协作原则

### 2.1 基本原则

- 所有人统一通过 Git 和远程仓库协作，不通过聊天软件互相传项目代码
- 禁止直接在 `main` 分支上开发
- 每个功能、修复、重构都应在独立分支完成
- 小步提交，及时推送，避免长时间本地堆积未提交代码
- 提交前保证本地至少完成最基本的运行检查
- 改动接口、数据结构、模型输入输出格式前，必须先同步相关同学

### 2.2 主张的小步快跑方式

- 一个分支只做一件相对明确的事情
- 一个提交只表达一个明确意图
- 一个 PR 只解决一个主题问题
- 每周至少形成一个可演示、可联调的集成版本

## 3. 分支模型

项目统一使用以下分支：

### 3.1 `main`

- 用途：正式主分支
- 要求：始终保持可运行、可部署、可演示
- 规则：禁止直接提交，必须通过 PR 合并

### 3.2 `develop`

- 用途：日常集成分支
- 要求：各模块开发完成后先合并到该分支进行联调
- 规则：功能分支统一从 `develop` 拉出，完成后合回 `develop`

### 3.3 `feature/*`

- 用途：新功能开发
- 来源：从 `develop` 创建
- 示例：
  - `feature/frontend-video-upload`
  - `feature/backend-case-management`
  - `feature/algorithm-workflow-recognition`
  - `feature/inference-api`

### 3.4 `fix/*`

- 用途：普通问题修复
- 来源：一般从 `develop` 创建
- 示例：
  - `fix/frontend-empty-state`
  - `fix/backend-auth-error`

### 3.5 `hotfix/*`

- 用途：主分支紧急修复
- 来源：从 `main` 创建
- 规则：修复后同时合并回 `main` 和 `develop`
- 示例：
  - `hotfix/demo-login-failure`

## 4. 分支命名规范

分支命名统一使用：

```text
类型/模块-简短描述
```

建议使用小写字母，单词之间用中划线 `-`。

推荐示例：

- `feature/frontend-login-page`
- `feature/backend-video-upload-api`
- `feature/algorithm-instrument-detection`
- `feature/qa-service`
- `fix/frontend-table-style`
- `fix/backend-file-parse`

不推荐示例：

- `test`
- `aaa`
- `zhangsan`
- `newbranch`
- `功能1`

## 5. 推荐目录边界

为了减少冲突，建议仓库从一开始按职责拆目录。示例：

```text
frontend/    Vue3 + Vite + TypeScript 前端项目
backend/     FastAPI 后端项目
algorithm/   Python 算法研发、推理、模型服务代码
docs/        接口文档、需求文档、协作规范
scripts/     部署、初始化、辅助脚本
```

协作原则：

- 前端开发优先修改 `frontend/`
- 后端开发优先修改 `backend/`
- 算法研发优先修改 `algorithm/`
- 公共协议、接口文档统一维护在 `docs/`

如果确需跨目录修改，提交说明和 PR 描述中要明确原因。

## 6. 日常开发流程

### 6.1 开发前同步最新代码

每天开始开发前先同步：

```bash
git checkout develop
git pull origin develop
```

### 6.2 从 `develop` 创建功能分支

```bash
git checkout -b feature/backend-video-upload-api
```

### 6.3 在自己的分支上开发

开发过程中：

- 不要直接切回 `develop` 写代码
- 不要多人共用同一个功能分支
- 每完成一个小功能或一个清晰修改点就提交一次

### 6.4 提交前同步集成分支

发起 PR 前先同步最新 `develop`：

```bash
git checkout develop
git pull origin develop
git checkout feature/backend-video-upload-api
git merge develop
```

如果项目要求线性历史，也可以使用 `rebase`，但团队未熟练前优先使用 `merge`，降低误操作风险。

### 6.5 自测通过后推送远程

```bash
git push -u origin feature/backend-video-upload-api
```

### 6.6 发起 PR 到 `develop`

要求：

- PR 标题清晰
- 描述本次改了什么
- 写明是否影响接口、数据库、模型服务
- 写明需要谁联调或 review

### 6.7 集成稳定后从 `develop` 合并到 `main`

适用场景：

- 周版本演示
- 里程碑验收
- 对外展示或部署

## 7. 提交信息规范

统一格式：

```text
type(scope): summary
```

如果不想写 `scope`，也允许简化为：

```text
type: summary
```

### 7.1 推荐的 `type`

- `feat`：新增功能
- `fix`：修复缺陷
- `refactor`：重构代码，不改变外部行为
- `docs`：文档更新
- `style`：样式或格式调整，不影响逻辑
- `test`：补充或修改测试
- `chore`：工程配置、依赖、脚本等杂项

### 7.2 推荐示例

```bash
git commit -m "feat(frontend): add surgical video upload page"
git commit -m "feat(backend): add case management API"
git commit -m "feat(algorithm): add workflow recognition inference script"
git commit -m "fix(backend): handle empty detection results"
git commit -m "docs(api): update inference response example"
git commit -m "refactor(frontend): split result panel components"
```

### 7.3 不推荐示例

```bash
git commit -m "修改"
git commit -m "update"
git commit -m "改了一下bug"
git commit -m "final"
```

## 8. 各角色提交要求

### 8.1 算法研发（Python）

提交前至少确认：

- 核心脚本能运行
- 模型推理输入输出格式已固定
- 依赖项变更已更新到依赖文件
- 若提供服务接口，已说明调用方式和返回字段

算法相关提交建议：

- 训练代码和实验脚本不要频繁污染平台主流程
- 临时 notebook、临时数据、超大模型文件不要直接提交到仓库
- 模型权重、大数据文件建议使用对象存储、制品库或单独管理方案
- 推理服务化代码与实验代码尽量分开

推荐目录思路：

- `algorithm/experiments/`：实验代码
- `algorithm/inference/`：推理脚本
- `algorithm/services/`：可供平台接入的服务代码
- `algorithm/configs/`：配置文件

### 8.2 前端开发（Vue3 + Vite + TypeScript）

提交前至少确认：

- 项目可以启动
- 页面无明显报错
- 类型检查通过或无新增明显类型问题
- 接口字段名与文档一致

前端相关提交建议：

- 页面、组件、接口请求、类型定义尽量分层提交
- 样式大改与业务逻辑大改尽量不要混在同一个提交
- 公共组件改动要在 PR 中标明影响范围

### 8.3 后端开发（FastAPI）

提交前至少确认：

- 服务可启动
- 新接口可访问
- 请求参数、响应结构、错误码说明明确
- 若改数据库结构，附带迁移说明

后端相关提交建议：

- 路由、服务层、数据层尽量分层组织
- 接口变更必须同步前端和算法接入同学
- 算法服务调用失败、超时、空结果的异常处理要明确

## 9. Pull Request 规范

### 9.1 PR 标题格式

统一建议：

```text
[模块] 变更内容
```

示例：

- `[前端] 新增视频上传页面`
- `[后端] 新增病例管理接口`
- `[算法] 接入手术流程识别推理服务`

### 9.2 PR 描述建议包含

- 变更目的
- 主要修改内容
- 是否影响接口
- 是否影响数据库
- 是否影响算法输入输出格式
- 自测情况
- 需要谁重点 review

### 9.3 PR 合并前检查项

- 能正常运行
- 没有明显冲突
- 文档已同步更新
- 接口改动已通知相关成员
- 不包含无关代码和调试文件

## 10. Code Review 规则

团队规模不大，建议采用轻量 review，但必须保留 review 动作。

### 10.1 基本规则

- 所有合并到 `develop` 和 `main` 的代码都应经过至少 1 人 review
- 大改动必须指定相关模块负责人 review
- 接口变更必须让调用方看一眼

### 10.2 推荐 review 关注点

- 是否影响现有功能
- 命名是否清晰
- 是否引入重复逻辑
- 是否影响接口兼容性
- 是否遗漏异常处理
- 是否缺少必要文档

### 10.3 不建议的情况

- 不看内容直接合并
- 多个大功能混在一个 PR
- 明知有冲突或明显 bug 仍强行合并

## 11. 接口与数据变更协作规则

智慧外科平台属于算法、平台、医学知识强耦合项目，以下变更必须提前同步：

- 接口路径变化
- 请求参数变化
- 返回字段变化
- 数据库表结构变化
- 文件上传格式变化
- 算法输入输出字段变化
- 模型版本切换导致结果格式变化
- 医学标签命名变化

建议所有接口定义统一维护在 `docs/` 中，例如：

- `docs/api-design.md`
- `docs/data-schema.md`
- `docs/model-input-output.md`

原则是先约定，再开发，再联调。

## 12. 冲突处理规则

发生冲突时遵循以下原则：

- 先理解双方修改意图，再处理冲突
- 不要为了图快直接覆盖别人的代码
- 冲突集中在公共文件时，优先找相关开发者确认
- 解决冲突后重新自测受影响模块

高频冲突区域要重点注意：

- 前端公共类型定义
- 后端接口 schema
- 算法服务返回结构
- 全局配置文件
- 依赖文件

## 13. 禁止提交的内容

以下内容原则上禁止直接提交到仓库：

- 大体积原始数据集
- 模型权重文件
- 临时测试视频
- 本地缓存文件
- 日志文件
- IDE 临时配置
- 临时导出报告
- 含隐私或未脱敏医疗数据的文件

建议通过 `.gitignore` 统一忽略这些内容。

## 14. 演示与发布流程

建议采用以下节奏：

### 14.1 日常开发

- 成员在 `feature/*` 分支开发
- 完成后合并到 `develop`

### 14.2 每周联调

- 在 `develop` 上集中联调
- 修复阻塞问题
- 验证核心业务链路

### 14.3 阶段演示或发布

- 从 `develop` 合并到 `main`
- 给演示版本打标签，例如：

```bash
git tag v0.1.0
git tag v0.2.0
```

这样便于回溯每个阶段的稳定版本。

## 15. 推荐的最小团队执行规则

如果当前团队希望先快速落地，可以先强制执行以下 8 条：

1. 禁止直接改 `main`
2. 所有开发从 `develop` 拉分支
3. 一人一分支，不共用
4. 一个 PR 只做一件事
5. 提交信息必须使用 `feat/fix/docs/refactor/...`
6. 接口变更必须提前同步
7. 合并前至少有 1 人 review
8. 每周至少产出一个可演示版本

## 16. 推荐命令示例

### 16.1 新建功能分支

```bash
git checkout develop
git pull origin develop
git checkout -b feature/frontend-result-dashboard
```

### 16.2 日常提交

```bash
git add .
git commit -m "feat(frontend): add result dashboard page"
git push -u origin feature/frontend-result-dashboard
```

### 16.3 合并前同步 `develop`

```bash
git checkout develop
git pull origin develop
git checkout feature/frontend-result-dashboard
git merge develop
```

### 16.4 紧急修复主分支

```bash
git checkout main
git pull origin main
git checkout -b hotfix/demo-login-failure
```

修复完成后，分别合并回 `main` 和 `develop`。

## 17. 附：角色协作建议

为了减少等待，建议角色配合方式如下：

- 产品负责人先明确本周优先级、验收标准、接口优先级
- 医学顾问先参与标签定义、结果评估标准制定
- 算法同学优先交付可调用的推理接口或 mock 输出
- 后端同学先固定接口协议和错误返回结构
- 前端同学先基于接口文档或 mock 数据完成页面联调

项目中最重要的不是“谁先写完”，而是“前后端和算法能不能尽早按同一协议并行推进”。

