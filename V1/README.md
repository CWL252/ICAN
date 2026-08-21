# CholecInsight

面向腹腔镜胆囊切除术的视频分析、教学辅助与阶段识别原型项目。

当前项目采用前后端分离结构：

- `frontend/`：基于 Vue 3 + Vite 的交互界面
- `backend/`：基于 FastAPI 的关键步骤分析服务
- `docs/`：Git 协作、PR、接口变更等团队规范文档
- `assets/`：演示资源

## 1. 项目简介

CholecInsight 主要聚焦腹腔镜胆囊切除术（LC, Laparoscopic Cholecystectomy）场景，目标是为外科教学、病例复盘和流程分析提供一个可扩展的交互平台。

当前版本已经具备以下基础能力：

- 创建视频分析项目并录入病例/术者/术式等元信息
- 上传手术视频并在前端播放预览
- 在分析页进行时间点文字注释
- 提交“关键步骤分析”任务，并轮询后端获取结果
- 展示关键步骤时间线、置信度和阶段分布结果
- 将项目数据保存在浏览器本地，支持会话内继续分析

## 2. 当前实现状态

目前仓库更接近“可演示原型”而不是“完整生产系统”。

### 前端当前能力

- 首页支持创建、查看、删除和复制项目
- 项目元信息保存在 `localStorage`
- 当前激活项目保存在 `sessionStorage`
- 视频文件保存在浏览器 `IndexedDB`
- 分析页支持视频加载、关键步骤分析任务提交、结果展示和简单导出

### 后端当前能力

- 提供健康检查接口：`GET /health`
- 提供关键步骤分析任务创建接口：`POST /api/phase/jobs`
- 提供任务查询接口：`GET /api/phase/jobs/{job_id}`
- 使用后台线程执行分析任务
- 将上传视频和任务结果写入 `backend/runtime/`

### 当前边界与注意事项

- 当前没有数据库，项目数据主要保存在浏览器本地
- 当前没有用户系统、权限控制和多成员在线协作能力
- 模型推理依赖本地权重目录和运行环境，默认不是“开箱即用”
- 仓库内已有前端构建产物和依赖目录，后续建议逐步规范化清理

## 3. 技术栈

### Frontend

- Vue 3
- Vue Router
- Vite
- Tailwind CSS

### Backend

- FastAPI
- Uvicorn
- PyTorch
- OpenCV
- Albumentations

## 4. 目录结构

```text
CholecInsight/
├─ assets/                  演示资源
├─ backend/                 FastAPI 后端与阶段识别推理逻辑
│  ├─ app.py                服务入口
│  ├─ job_manager.py        后台任务管理
│  ├─ phase_service.py      视频阶段分析服务
│  ├─ phase_model.py        模型加载封装
│  └─ requirements.txt      Python 依赖
├─ docs/                    团队规范与文档
│  ├─ API_norm.md
│  ├─ Git_Standard.md
│  └─ PULL_REQUEST_TEMPLATE.md
├─ frontend/                Vue 前端工程
│  ├─ src/
│  │  ├─ views/             首页/分析页
│  │  ├─ api/               前端接口请求封装
│  │  ├─ projectStore.js    项目本地存储
│  │  ├─ phaseAnalysisStore.js
│  │  └─ videoStore.js
│  ├─ package.json
│  └─ vite.config.js
└─ README.md
```

## 5. 快速启动

### 5.1 启动前准备

建议本地准备以下环境：

- Node.js 18+
- npm 9+
- Python 3.8+
- 可选：CUDA 环境与 PyTorch GPU 版本

可参考仓库根目录的 `.env.example` 了解当前项目使用的环境变量。

### 5.2 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认开发地址通常为：

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

### 5.3 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8001 --reload
```

后端默认地址：

- [http://127.0.0.1:8001](http://127.0.0.1:8001)

健康检查：

```bash
curl http://127.0.0.1:8001/health
```

## 6. 环境变量与模型依赖

后端阶段识别服务会优先读取项目内的权重目录：

```text
backend/pretrained_weights/
```

如果项目内没有找到权重文件，后端才会回退读取环境变量 `SURGPHASE_ROOT` 对应目录下的：

```text
SURGPHASE_ROOT=D:\project\SurgPhase
```

### 权重文件说明

由于预训练权重体积较大，不适合直接存放在 GitHub 仓库中，因此本仓库**不提交权重文件本体**。团队成员需要从百度网盘链接单独下载权重，并手动放到下面的位置：

```text
backend/pretrained_weights/
```

当前需要的权重文件为：

- `cnn_checkpoint_best_acc.pth.tar`
- `head_checkpoint_best_acc.pth.tar`

权重文件地址：

- 百度网盘链接：`https://pan.baidu.com/s/1pnqnadYkODxdyco6zZZcfw?pwd=auhm`
- 提取码：`auhm`

如果权重不存在，模型相关能力将无法正常运行。

## 7. 前后端联调说明

前端通过 `frontend/src/api/phaseAnalysis.js` 请求后端接口，默认读取：

```text
VITE_API_BASE_URL=http://127.0.0.1:8001
```

如果需要修改后端地址，可在前端通过环境变量 `VITE_API_BASE_URL` 覆盖。

当前联调流程如下：

1. 在首页创建项目并上传视频
2. 进入分析页
3. 点击“开始关键步骤分析”
4. 前端调用后端创建任务
5. 后端后台执行分析并保存任务状态
6. 前端轮询任务状态并更新项目结果

## 8. Git 协作建议

### 推荐分支模型

- `main`：始终保持可演示、可交付
- `develop`：日常集成分支
- `feature/*`：新功能开发
- `fix/*`：常规问题修复
- `hotfix/*`：线上或演示紧急修复

### 推荐工作流

1. 从 `develop` 拉取最新代码
2. 创建个人功能分支
3. 在分支内完成开发和自测
4. 发起 PR 合并到 `develop`
5. 联调稳定后，再从 `develop` 合并到 `main`

### 推荐提交信息格式

```text
type(scope): summary
```

示例：

```bash
git commit -m "feat(frontend): add project creation modal"
git commit -m "feat(backend): add phase analysis job polling API"
git commit -m "docs(readme): add project onboarding guide"
```

### 建议优先遵守的最小规则

- 不要直接在 `main` 上开发
- 一人一分支，不共用功能分支
- 一个 PR 只解决一个主题
- 接口字段变更前先同步前后端和算法同学
- 文档和代码尽量一起提交

## 9. 相关文档

项目内已经有团队协作的规范文档，建议在开发前统一阅读：

- [docs/Git_Standard.md](/D:/Codex/SrugAI/CholecInsight/docs/Git_Standard.md)
- [docs/PULL_REQUEST_TEMPLATE.md](/D:/Codex/SrugAI/CholecInsight/docs/PULL_REQUEST_TEMPLATE.md)
- [docs/API_norm.md](/D:/Codex/SrugAI/CholecInsight/docs/API_norm.md)

如果后续你们准备继续扩展，建议逐步补齐这些文档：

- `docs/api-design.md`
- `docs/data-schema.md`
- `docs/model-input-output.md`
- `docs/deployment.md`
