# V1 版本改进说明（与 old version 对比）

> 本文档详细记录 V1（`new version`）相对旧版（`old version`）的全部改进，具体到接口、数据结构与实现细节。旧版定位是**单机可演示原型**，V1 定位是**多用户协作的应用**：在保留全部原有分析能力的基础上，新增了用户系统与完整开源社区。

---

## 一、总体对比

| 维度 | old version | V1（本次） |
|---|---|---|
| 定位 | 单机演示原型 | 多用户社区化应用 |
| 用户系统 | ❌ 无（README 明确"没有用户系统、权限控制"） | ✅ 注册 / 登录 / Bearer Token 鉴权 / 路由守卫 |
| 社区功能 | ❌ 完全没有 | ✅ 开源广场、讨论区、评论、关注、视频分享、我的社区 |
| 数据库 | ❌ 无（任务状态存 JSON 文件） | ✅ SQLite（users / sessions + 6 张社区表） |
| 后端端点 | 4 个 | 30+ 个 |
| 前端视图 | 3 个（Splash / Home / Analysis） | 9 个（+ Login / Community / ProjectDetail / PostDetail / MyCommunity / AuthorProfile） |
| 人工标记片段 | ❌ 无 | ✅ 手动编辑、拖拽调边界、展示优先级 |
| 真实分割 | ❌ 前端几何模拟 | ✅ 后端 /api/segment 真实推理 |
| 文件规模 | 前端 ~2900 行核心页 | 后端 community.py 1330 行 + auth.py 324 行 + 前端新增 ~4000 行 |

---

## 二、后端改进（backend/）

### 2.1 新增用户系统（auth.py，324 行）

旧版无任何用户概念。V1 新增：

- **表结构**：`users`（id / username / email / password_hash / created_at）、`sessions`（token / user_id / created_at / expires_at）
- **密码存储**：`pbkdf2` + 每用户随机盐（`secrets.token_hex(16)`），绝不存明文
- **会话**：不透明 Bearer Token（`secrets.token_urlsafe(32)`），7 天有效期，登出即删记录
- **接口**：`POST /api/auth/register`（用户名 + 邮箱 + 密码）、`POST /api/auth/login`（用户名**或**邮箱均可，字段名 `identifier`）、`GET /api/auth/me`、`POST /api/auth/logout`
- **鉴权依赖**：`get_current_user` 注入每个社区端点；前端 401 时统一 `handleUnauthorized()` 清登录态跳回登录页

### 2.2 新增社区后端（community.py，1330 行）

全部接口前缀 `/api/community`，除视频播放外均要求 `Authorization: Bearer`：

**项目分享**
- `GET /projects` —— 列表，支持 `q` 关键词（标题/描述/术式/作者名）、`sort=popular`（按点赞数排序）、分页、**`mine=true` 只看自己的**、**`author_id=` 只看某位作者的**（博主主页用）
- `POST /projects` —— 分享项目（元数据 + 阶段分析结果 JSON）
- `GET /projects/{id}` / `PUT /projects/{id}` / `DELETE /projects/{id}` —— 详情 / 更新 / 删除（属主校验；删除时连带清理视频文件与点赞收藏关注）

**帖子讨论**
- `GET/POST /posts`、`GET/PUT/DELETE /posts/{id}` —— 讨论区帖子 CRUD，同款搜索分页与 `mine`

**评论（支持任意层级嵌套回复）**
- `GET /comments?target_type=&target_id=` —— 按目标查，`ORDER BY created_at ASC` 后按 `parent_id` 组装**任意深度树**（`by_id` 字典挂接，不递归 SQL）
- `GET /comments?mine=true` —— 查自己的全部评论，LEFT JOIN 带出所属内容标题，附每条评论收到的回复数
- `POST /comments` —— 发布评论/回复，`parent_id` 可选；校验父评论存在、属于同一目标；**不限层级**（旧版无评论）
- `DELETE /comments/{id}` —— 评论作者**或内容发布者**可删；SQLite `ON DELETE CASCADE` 级联删除所有后代回复

**互动**
- `POST/DELETE /projects/{id}/like`、`/posts/{id}/like` —— 点赞（UNION ALL 查询注意显式 AS 别名）
- `POST/DELETE /projects/{id}/favorite`、`/posts/{id}/favorite` —— 收藏
- `POST/DELETE /users/{id}/follow`、`GET /users/{id}/profile` —— 关注与主页
- `GET /me/favorites`、`GET /me/likes` —— 我的收藏/点赞列表（LEFT JOIN 项目/帖子/作者，只返回仍存在的内容，附目标标题与作者名）
- `GET /me/following` —— 我关注的博主列表（含项目数/帖子数/粉丝数/最近一条分享标题，按最近动态排序）

**开源视频（核心新增）**
- `PUT /projects/{id}/video` —— multipart 上传，**1GB 上限**（413 + 清理已写文件），1MB 分块写盘到 `runtime/videos/{project_id}{后缀}`，仅属主
- `GET /projects/{id}/video?token=` —— 流式播放：`FileResponse` 原生支持 **HTTP Range**（浏览器可拖动进度条，206 响应）；token 走 query（`<video>` 标签无法带 Authorization header）
- `DELETE /projects/{id}/video` —— 删文件并清空记录；删除项目时自动连带清理

### 2.3 新增真实分割（sam_service.py + /api/segment）

- `POST /api/segment` —— 接收图像与点/框提示，后端跑 MobileSAM 推理返回掩码（**旧版是前端几何多边形模拟**，`backend/mobile_sam/` 旧版只剩空壳）
- 含 GPU 不可用时的 CPU 回退逻辑

### 2.4 人工标记片段合并（PUT /api/phase/jobs/{id}/annotations）

- 旧版：任务结果只读，人工标记字段是历史残留（`edited: true, source: "user"` 出现在旧 JSON 里但代码完全不读）
- V1：分析任务支持把用户编辑的片段（`phaseKey / phaseLabel / startSeconds / endSeconds / title / description`）合并回任务结果，作为 `editedSegments` 持久化

### 2.5 数据库与迁移（SQLite）

- 6 张社区表：`community_projects` / `posts` / `comments` / `likes` / `favorites` / `follows`
- 关键细节：
  - 每连接 `PRAGMA foreign_keys = ON`（级联删除生效的前提）
  - `CREATE TABLE IF NOT EXISTS` 不会给已有表加列 → 显式迁移：`PRAGMA table_info` 检查后 `ALTER TABLE ADD COLUMN`（如 `video_file_name`、`comments.parent_id`）
  - `comments.parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE` —— 删父评论自动删所有子孙回复
  - 唯一约束防重复点赞/收藏/关注

---

## 三、前端改进（frontend/src/）

### 3.1 视图与路由

- **旧版**：`/`、`/home`、`/analysis`，无路由守卫
- **V1**：新增 `/login`、`/community`（社区）、`/community/projects/:id`（项目详情）、`/community/posts/:id`（帖子详情）、`/community/mine`（我的社区）
- `router.beforeEach` 守卫：未登录访问受保护页面 → 跳登录；已登录访问登录页 → 跳首页
- `lib/auth.js`：登录态管理（localStorage `auth_token` / `auth_user`）

### 3.2 登录注册页（Login.vue，349 行）

- 注册（用户名/邮箱/密码/确认密码 + 前端校验）与登录（用户名或邮箱）双模式
- 登录成功写入 token 与用户信息并跳转

### 3.3 社区页（Community.vue，612 行）

- 三个 tab：**开源广场**（项目卡片：标题/作者/术式/点赞收藏数/视频图标）、**讨论区**（帖子列表 + 发帖弹窗）、**关注动态**（feed 流）
- 搜索（防抖 300ms）+ 排序切换，卡片上点赞/收藏按钮即时反馈

### 3.4 项目详情页（ProjectDetail.vue，498 行）

- 完整信息展示 + 关注作者按钮 + 点赞收藏
- **视频播放区**：`<video :src="projectVideoUrl(id)">`，query token 播放；加载失败显示"可能已被作者移除"提示
- **阶段分析区**：
  - 分布与步骤**优先按人工标记片段展示**（`editedSegments` 聚合各阶段秒数、映射为步骤时间线，带"✎ 按人工标记"角标与蓝色"人工标记"徽章），无标记时回退 AI 结果（`result.distribution` / `result.steps`）
  - 统计卡：视频时长 / 分析步骤数 / AI 生成片段数 / 人工修正片段数
- 评论区：项目作者（`isSelf`）可删除**任意**评论

### 3.5 帖子详情页（PostDetail.vue，314 行）

- 轻量 markdown 渲染（`lib/markdown.js`：先 `escapeHtml` 再解析行结构，**防 XSS**）
- 关注/点赞/收藏 + 评论

### 3.6 我的社区（MyCommunity.vue，483 行）—— 全新

- 三 tab：**我的项目 / 我的帖子 / 我的评论**，每条可"查看"或"删除"（确认弹窗）
- **评论管理面板**：对任一自己发布的内容，列出全部评论（任意层级树，按深度缩进、回复带标记），**按内容关键词筛选**（父评论不匹配但子回复匹配时保留父链），逐条删除（有回复时确认级联数量）

### 3.7 递归评论组件（components/CommentItem.vue + CommentList.vue）

- `CommentItem.vue` 通过**文件名隐式自引用**实现无限层级嵌套回复渲染；每层缩进 `ml-5 pl-4 border-l-2` + 左侧竖线
- 删除按钮条件 `comment.isMine || canManage`（canManage = 内容作者）
- 评论总数**递归统计**（含所有层级回复）
- 删除有回复的评论先弹确认（提示将级联删除）

### 3.8 分享流程改造（Home.vue，798 行）

- 分享模态框新增"**包含手术视频**"复选框（默认勾选，1GB 上限提示）
- **两步分享**：① 元数据 POST ② 若有视频，从 IndexedDB 取 File → XHR + FormData 上传 → 进度条实时百分比 → 按钮文字"分享中(元数据)… / 上传视频 xx%"
- "更新分享"走同样流程重新覆盖上传；分享映射存 `communityShareStore.js`（localStorage `surgreview-share-map`，本地项目 id → 社区项目 id，用于"已分享"徽标与联动删除）
- **数据一致性修复**：删除本地项目时若发现分享映射，**自动同步取消社区分享**（后端连带删视频文件），避免孤儿视频；失败则 toast 提示

### 3.9 API 层（api/community.js，194 行）

- 统一 `request()` 封装：自动带 Bearer token、401 统一处理、错误取 `payload.detail`
- 视频上传必须 **FormData 包裹 File**：直接 `xhr.send(file)` 缺少 multipart boundary 会触发 FastAPI 422（detail 是数组 → 转字符串变成 `[object Object]`）；同时错误兜底 `typeof detail === 'string'`，否则显示通用中文提示
- `projectVideoUrl()` 拼 query token 供 `<video>` 使用

---

## 四、核心问题修复清单（开发过程中实际踩过的坑）

1. **视频上传失败 "[object Object]"**：`xhr.send(File)` 无 boundary → 422 数组 detail → 修复为 FormData + 非字符串 detail 兜底
2. **评论只能一层回复**：后端限制 `parent.parent_id is None` → 移除限制，支持任意层级
3. **自己不能回复自己的评论**：回复按钮 `v-if="!comment.isMine"` → 移除，人人可回复
4. **placeholder 显示字面量 `{{}}`**：改为 `:placeholder` 绑定（模板字符串）避免歧义
5. **回复按钮不可见**：旧逻辑只显示删除按钮 → 每个评论独立"回复"按钮 + 回复框
6. **"我的项目"点查看空白页**：跳转路径单数 `/community/project/` 与路由复数 `/community/projects/` 不匹配 → 修正 3 处跳转
7. **删本地项目留下孤儿分享**：删除不联动社区 → 增加分享映射检查与自动取消分享
8. **Windows 控制台中文乱码**：调试脚本统一走 UTF-8 解码，测试不依赖终端显示
9. **uvicorn --reload 在 Windows 不可靠**：Python 改动后必须重启进程
10. **Range/query token 参数校验**：`Query(...)` 必填会让无 token 请求返回 422 而非 401 → 改 `Query(default=None)` 手动返回 401

---

## 五、旧版原有、V1 保留的能力（未回退）

- 项目 CRUD（localStorage）+ 视频 IndexedDB 持久化
- 关键步骤分析：后端 MS-TCN（ResNet50-GN 特征 + 时序头，7 类胆囊切除阶段），4 秒轮询进度，Home 页 5 秒全量同步
- 文字注释（时间段记录 + 片段循环播放）
- 分割点标注与掩码（V1 升级为真实 SAM 推理）
- 器械频率统计、豆包 AI 问答（`/api/chat`）、报告导出（JSON / HTML 打印 PDF）
- 启动闪屏页

---

## 六、数据与安全细节

| 项目 | 说明 |
|---|---|
| 用户数据 | SQLite `runtime/users.db`（密码加盐哈希，不落明文） |
| 社区视频 | 文件系统 `runtime/videos/`（不入库，SQLite 只存文件名） |
| 视频鉴权 | 播放走 query token，登录校验；上传/删除走 Bearer + 属主校验 |
| 评论删除权限 | 评论作者 或 内容发布者，其他人 403 |
| Markdown | 先 HTML 转义再渲染，杜绝脚本注入 |
| 大文件 | 视频上传 1MB 分块流式写盘，1GB 上限，超限清理 |
| 级联一致性 | 删评论 → 删所有回复；删项目/帖子 → 删视频文件 + 点赞收藏关注 + 评论树 |

---

## 七、文件规模对照（含新增代码量）

| 文件 | old version | V1 | 说明 |
|---|---|---|---|
| backend/app.py | ~170 行 | 274 行 | + 分割、注释合并端点 |
| backend/auth.py | 无 | 324 行 | 用户系统 |
| backend/community.py | 无 | 1330 行 | 社区全套 |
| backend/sam_service.py | 无 | 124 行 | 真实分割 |
| frontend views | 3 个 | 9 个 | + Login/Community/详情×2/MyCommunity/AuthorProfile |
| frontend components | 无 | 2 个 | 递归评论组件 |
| frontend api/ | 2 个 | 5 个 | + auth/community/segment/chat 拆分 |
| frontend lib/ | 无 | 2 个 | auth 登录态、markdown 渲染 |

---

## 八、V1.1 更新（2026-08-22）：关注关系与收藏体系

在 V1 基础上补全"以博主为中心"的社交闭环，共 5 处改动：

### 8.1 关注动态改为博主列表

- **之前**：关注动态（feed）展示关注者的每一条项目/帖子（"新项目"“新帖子”卡片），点击卡片进对应内容详情
- **现在**：关注动态展示**博主卡片列表**——头像、用户名、分享项目数 / 帖子数 / 粉丝数、最新一条分享标题；点击卡片进入**博主主页**，而非单条内容
- 后端新增 `GET /me/following`：子查询统计每位博主的项目/帖子/粉丝数，`MAX(UNION ALL 时间)` 取最近动态排序（`NULLS LAST`）

### 8.2 新增博主主页（AuthorProfile.vue，/community/users/:id）

- 作者信息卡：头像（用户名首字母）、加入时间、关注按钮（未关注时"关注作者"，已关注显示"已关注"可取消，实时更新粉丝数）
- 统计栏：分享项目 / 发帖 / 粉丝 / 关注 四格
- 两个 tab：**分享的项目**（`GET /projects?author_id=`，含视频图标、点赞收藏数）与**帖子**（`GET /posts?author_id=`）
- `list_projects` / `list_posts` 新增 `author_id` 过滤参数（conditions 拼接，可与其他条件组合）

### 8.3 广场帖子卡片补全收藏

- 之前帖子卡片只有点赞数和评论数展示（点赞不可点、无收藏）；现在点赞、**收藏**都可点击切换，收藏高亮琥珀色

### 8.4 我的社区新增「我的收藏 / 我的点赞」

- 两个新 tab，展示收藏/点赞过的项目与帖子：类型图标（项目蓝色/帖子紫色）、标题、作者（可点击跳博主主页）、时间
- 每条可「查看」（跳详情页）或「取消收藏/取消点赞」（确认弹窗后本地移除）
- 后端 `_my_engagement()` 统一实现：LEFT JOIN 项目/帖子/作者，**只返回仍存在的内容**（目标被删则不显示）

### 8.5 修复：博主主页显示"用户不存在或已被删除"

- 原因：`user_profile` 接口直接返回 `{user, stats, isFollowing, isSelf, ...}`（无 `.item` 包装），AuthorProfile 却取了 `.item` → `undefined` 被当成 404
- 修复：去掉 `.item` 直接取返回值（与 ProjectDetail / PostDetail 的用法保持一致）
