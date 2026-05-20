# image2 图像生成网站实施计划

## Summary

* 在空仓库内搭建一个 `FastAPI + SQLite + Vue3` 的图像生成网站，封装 `image2` 生成能力，并通过统一适配层隔离具体供应方实现。

* 采用“`Key 即令牌`”模式：普通用户通过数据库中的用户 `Key` 访问生成能力，管理员通过后端配置文件中的管理员 `Key` 登录后台；前端不保留复杂登录态，用户页与后台页分别输入对应 `Key`，后续请求统一通过请求头携带该 `Key` 访问后端接口。

* 普通用户额度按“生成成功后扣减”执行：图片生成采用异步任务流，用户提交任务后立即返回任务单号；只有后台任务真正生成成功、文件落盘、数据库记录写入成功后才减少该用户 `Key` 的剩余次数；管理员 `Key` 只用于后台登录与管理，不参与生成扣次。

* 图片文件与数据库解耦：图片原文件单独保存在本地目录，数据库只保存文件名、相对路径、提示词、模板、状态和 `Key` 关联信息。

* 前端界面保持简洁，首页中心区域使用类 AI 对话框交互，配套一组内置静态风格模板，提供示例图、模板说明和提示词快捷填充。

## Project Structure

* 建议项目目录结构如下，作为后续实施时的固定落点：

```text
e:\codes\image2web
├─ backend
│  ├─ .env.example
│  ├─ requirements.txt
│  ├─ app
│  │  ├─ main.py
│  │  ├─ core
│  │  │  ├─ config.py
│  │  │  ├─ db.py
│  │  │  └─ errors.py
│  │  ├─ api
│  │  │  ├─ deps.py
│  │  │  ├─ router.py
│  │  │  └─ routes
│  │  │     ├─ auth.py
│  │  │     ├─ generation.py
│  │  │     └─ admin.py
│  │  ├─ models
│  │  │  ├─ api_key.py
│  │  │  ├─ media_asset.py
│  │  │  ├─ generation_task.py
│  │  │  ├─ generation_input_image.py
│  │  │  ├─ generation_record.py
│  │  │  └─ admin_audit.py
│  │  ├─ schemas
│  │  │  ├─ auth.py
│  │  │  ├─ generation.py
│  │  │  └─ admin.py
│  │  ├─ services
│  │  │  ├─ key_service.py
│  │  │  ├─ admin_auth_service.py
│  │  │  ├─ generation_service.py
│  │  │  ├─ storage_service.py
│  │  │  ├─ admin_service.py
│  │  │  ├─ task_worker_service.py
│  │  │  └─ task_scheduler_service.py
│  │  └─ providers
│  │     ├─ base.py
│  │     ├─ image2_provider.py
│  │     └─ factory.py
│  └─ tests
│     ├─ test_key_service.py
│     ├─ test_generation_api.py
│     ├─ test_task_worker_service.py
│     └─ test_admin_api.py
├─ frontend
│  ├─ .env
│  ├─ .env.development
│  ├─ .env.test
│  ├─ .env.production
│  ├─ package.json
│  ├─ vite.config.ts
│  └─ src
│     ├─ main.ts
│     ├─ api
│     │  ├─ client.ts
│     │  └─ __tests__
│     │     └─ client.spec.ts
│     ├─ config
│     │  └─ env.ts
│     ├─ stores
│     │  ├─ session.ts
│     │  └─ admin-session.ts
│     ├─ composables
│     │  ├─ useGenerationTask.ts
│     │  └─ __tests__
│     │     └─ useGenerationTask.spec.ts
│     ├─ data
│     │  └─ style-templates.ts
│     ├─ components
│     │  ├─ PromptComposer.vue
│     │  ├─ UploadImageTray.vue
│     │  ├─ TemplateGallery.vue
│     │  ├─ GenerationResult.vue
│     │  ├─ TaskStatusPanel.vue
│     │  ├─ HistoryDrawer.vue
│     │  ├─ RevisionChainPanel.vue
│     │  └─ __tests__
│     │     ├─ TemplateGallery.spec.ts
│     │     ├─ PromptComposer.spec.ts
│     │     └─ HistoryDrawer.spec.ts
│     ├─ views
│     │  ├─ HomeView.vue
│     │  └─ AdminView.vue
│     ├─ router
│     │  └─ index.ts
│     ├─ styles
│     │  └─ main.css
│     └─ assets
│        └─ templates
├─ data
│  ├─ app.db
│  ├─ uploads
│  │  └─ YYYY
│  │     └─ MM
│  │        └─ DD
│  └─ images
│     └─ YYYY
│        └─ MM
│           └─ DD
└─ script
   ├─ image2test.py
   ├─ demo.jpg
   └─ output.png
```

## Current State Analysis

* 当前仓库还没有正式的前后端工程目录，但已经存在可运行的原型脚本与测试素材：
  * `e:\codes\image2web\script\image2test.py`
  * `e:\codes\image2web\script\demo.jpg`
  * `e:\codes\image2web\script\output.png`

* `image2test.py` 已验证第三方图像编辑能力可用，当前脚本核心流程如下：
  * 读取本地图片并转换为 `data:` 协议的 Base64。
  * 按 OpenAI 兼容消息格式构造 `messages`，其中 `content` 先放文本，再放 `image_url`。
  * 调用 `POST /v1/chat/completions`，使用模型 `gpt-image-2`。
  * 从返回文本中提取图片 URL，再下载到本地文件。

* 当前脚本只支持单张图片输入、命令行运行和同步等待返回，尚未具备网站所需的能力：
  * 不支持最多 3 张图片上传。
  * 不支持异步任务与轮询。
  * 不支持数据库记录、用户额度、历史回顾和二次编辑工作流。

* 因为尚不存在正式网站工程，本次计划仍以“从零搭建但保持最小可用结构”为原则，不引入额外复杂架构。

* 用户已确认的关键决策如下：

  * 仓库按“完整搭建”规划。

  * 后台管理范围为“可维护后台”，需要支持管理员使用配置文件中的独立 `Key` 登录后台，并完成用户 `Key` 创建、次数充值、启停用、生成记录检索。

  * `image2` 接入方式暂未最终确定，因此后端先设计统一适配层，后续只替换具体实现。

  * 鉴权方式为“`Key 即令牌`”，不单独设计用户名密码体系；管理员 `Key` 不入库，通过后端配置文件唯一校验。

  * 次数在“生成成功后”扣减。

  * 风格模板采用“内置静态模板”。

  * 图片生成采用“提交任务 + 异步执行 + 轮询结果”的模式，不使用单个请求长时间等待图片返回。

  * 核心图像生成能力以 `script\image2test.py` 为基准整理为正式后端适配器。

  * 用户端只保留一个工作台页面，不在生成、历史回顾、二次编辑之间做页面跳转。

## Assumptions & Decisions

* 后端工程目录定为 `e:\codes\image2web\backend`，前端工程目录定为 `e:\codes\image2web\frontend`，避免引入不必要的多模块复杂度。

* SQLite 数据库文件存放在 `e:\codes\image2web\data\app.db`，上传图片目录与生成图片目录都由后端配置文件决定，默认分别落在 `e:\codes\image2web\data\uploads` 和 `e:\codes\image2web\data\images`。

* API `Key` 作为访问令牌统一放在请求头 `X-API-Key` 中，前后端均围绕该约定实现；用户接口校验数据库中的用户 `Key`，管理接口直接比对后端配置中的管理员 `Key`。

* 管理员 `Key` 不写入数据库，也不由脚本生成；后端通过配置文件加载唯一管理员 `Key`，后台页面直接使用该 `Key` 访问管理接口。

* 前端使用 `.env`、`.env.development`、`.env.test`、`.env.production` 区分不同环境接口域名，并统一由 Axios 请求层读取。

* 风格模板先以内置 JSON/TS 常量实现，不入库；每个模板包含 `id`、`name`、`preview`、`prompt`、`negativePrompt`、`description`。

* `image2` 统一封装为适配器接口，首个正式实现直接整理自 `e:\codes\image2web\script\image2test.py` 的已跑通逻辑，而不是继续使用占位 provider。

* 后端配置文件同时承载第三方 `image2` 接口的 `base_url`、`api_key`、超时等配置，避免把外部服务参数散落在代码中。

* 图片生成从一开始就采用异步任务模式：`POST` 接口只负责创建任务，后台 worker 消费任务并更新状态，前端通过轮询获取进度和结果。

* 在现有 `FastAPI + SQLite` 技术栈下，优先采用“数据库任务表 + 应用内 worker”方案，不额外引入 Redis、Celery 或消息队列，先保证单机可用与可恢复。

* 前端优先采用轮询而不是 WebSocket/SSE：实现简单、与当前技术栈更匹配；默认每 2 到 3 秒查询一次任务状态，任务完成或失败后自动停止。

* 用户上传图片限制为最多 3 张，且仅允许 `png`、`jpg`、`jpeg`、`webp`，该约束在前端选择器、提交参数校验和后端接口校验三层同时生效。

* 用户历史记录是“独立生成会话列表”，不是连续共享上下文的聊天记忆；用户从历史记录中选择某张生成图再次编辑时，会创建一个新的独立任务，并把该图片作为新的输入图之一。

* 后端对所有图片文件做统一文件管理：
  * 用户上传图和生成结果图都必须重新命名。
  * 文件按日期目录分层保存，例如 `YYYY/MM/DD`。
  * 数据库记录文件类型、来源 Key、原始文件名、重命名后的文件名、相对路径、来源任务和来源记录。

## Proposed Changes

### 1. 工程初始化

* 新建 `e:\codes\image2web\backend\requirements.txt`

  * 固定基础依赖：`fastapi`、`uvicorn`、`sqlalchemy`、`pydantic`、`python-multipart`、`httpx`、`alembic`。

  * 保持最小依赖集，不提前引入 Redis、Celery、复杂权限框架。

* 新建 `e:\codes\image2web\backend\app\main.py`

  * 作为 FastAPI 启动入口。

  * 注册路由、异常处理、CORS、中间件和静态文件挂载。

* 新建 `e:\codes\image2web\backend\app\core\config.py`
  * 作为后端统一配置入口。
  * 管理数据库路径、上传图片根目录、生成图片根目录、第三方 `image2` 接口 `url`、第三方 `API_KEY`、管理员登录 `Key` 等配置。
  * 增加任务轮询间隔、worker 并发数、单任务超时时间、失败重试次数等异步任务参数。

* 新建 `e:\codes\image2web\backend\.env.example`
  * 提供后端配置样例，至少包含数据库路径、`UPLOAD_IMAGE_DIR`、`GENERATED_IMAGE_DIR`、`IMAGE2_BASE_URL`、`IMAGE2_API_KEY`、`ADMIN_LOGIN_KEY`。

* 新建 `e:\codes\image2web\backend\app\core\db.py`

  * 提供 SQLAlchemy `engine`、`SessionLocal`、`Base`。

* 新建 `e:\codes\image2web\backend\app\core\errors.py`

  * 统一业务错误码与异常结构，覆盖 `Key` 无效、余额不足、生成失败、图片保存失败、管理员未授权等错误。
  * 增加上传图片数量超限、图片格式不支持、单图过大、任务不存在等错误码。

* 新建 `e:\codes\image2web\frontend\package.json`、`vite.config.ts`、`src\main.ts`

  * 初始化 Vue3 + Vite 前端工程。

* 新建 `e:\codes\image2web\frontend\.env`、`.env.development`、`.env.test`、`.env.production`
  * 使用 `VITE_API_BASE_URL` 区分开发、测试、生产环境的后端接口域名。
  * 所有前端接口地址统一从环境变量读取，不在组件内硬编码。

### 2. 后端数据模型

* 新建 `e:\codes\image2web\backend\app\models\api_key.py`
  * 定义 `ApiKey` 表：`id`、`key_value`、`name`、`remaining_count`、`status`、`created_at`、`updated_at`、`last_used_at`。
  * 仅存储普通用户 `Key`；`status` 支持 `active`、`disabled`。

* 新建 `e:\codes\image2web\backend\app\models\media_asset.py`
  * 定义统一文件资产表：`id`、`api_key_id`、`asset_type`、`source_type`、`original_name`、`stored_name`、`relative_path`、`absolute_dir`、`mime_type`、`file_size`、`width`、`height`、`task_id`、`record_id`、`created_at`。
  * `asset_type` 支持 `input_image`、`generated_image`。
  * `source_type` 支持 `upload`、`history_record`、`generation_result`。
  * 该表作为后端统一文件管理中心，用于回答“这个图片来自哪个 Key、哪次任务、保存在哪里”。

* 新建 `e:\codes\image2web\backend\app\models\generation_task.py`
  * 定义 `GenerationTask` 表：`id`、`api_key_id`、`prompt`、`negative_prompt`、`template_id`、`status`、`progress_message`、`retry_count`、`provider`、`error_message`、`result_record_id`、`created_at`、`started_at`、`finished_at`。
  * `status` 至少支持 `pending`、`processing`、`success`、`failed`。
  * 用于承载异步任务生命周期，不把排队状态和最终结果强行混在同一张表里。

* 新建 `e:\codes\image2web\backend\app\models\generation_input_image.py`
  * 定义输入图关联表：`id`、`task_id`、`media_asset_id`、`source_type`、`sort_order`、`source_record_id`、`created_at`。
  * 用于记录每次任务附带的 0 到 3 张输入图。
  * `source_type` 支持 `upload`、`history_record`，便于二次编辑时复用历史生成图。

* 新建 `e:\codes\image2web\backend\app\models\generation_record.py`

  * 定义 `GenerationRecord` 表：`id`、`api_key_id`、`prompt`、`negative_prompt`、`template_id`、`status`、`result_media_asset_id`、`provider`、`error_message`、`created_at`。

  * `status` 至少支持 `success`、`failed`。
  * 只保存最终生成结果，不承担排队和执行中状态。
  * 增加 `parent_record_id` 字段，标记本次结果是否由历史图片二次编辑而来，支撑历史回顾链路。

* 新建 `e:\codes\image2web\backend\app\models\admin_audit.py`

  * 记录后台管理动作，如创建 `Key`、充值次数、禁用/启用。

### 3. 后端业务分层

* 新建 `e:\codes\image2web\backend\app\schemas\auth.py`
  * 定义用户端与后台端的 `Key` 校验响应结构，如 `key_name`、`remaining_count`、`status`、`isAdmin`。

* 新建 `e:\codes\image2web\backend\app\schemas\generation.py`

  * 定义任务创建、任务详情、任务列表、最终结果 DTO。

  * 创建请求字段包含 `prompt`、`negativePrompt`、`templateId`、`referenceRecordId`，以及最多 3 张图片文件。

  * 创建响应字段包含 `taskId`、`status`、`queuePosition`。

  * 查询响应字段包含 `taskId`、`status`、`progressMessage`、`imageUrl`、`remainingCount`、`errorMessage`、`inputImages`、`referenceRecordId`。

* 新建 `e:\codes\image2web\backend\app\schemas\admin.py`
  * 定义管理后台用户 `Key` 创建、充值、启停用、列表查询、记录检索 DTO。
  * 管理接口只管理用户 `Key`，管理员 `Key` 不出现在数据库列表中。

* 新建 `e:\codes\image2web\backend\app\services\key_service.py`
  * 封装用户 `Key` 校验、余额检查、成功扣次、最后使用时间更新。
  * 生成接口只允许数据库中的有效用户 `Key` 调用。
  * 任务创建阶段只做资格校验，不扣减次数；任务成功收尾时才执行次数扣减，并与结果记录写入放在一个事务中。


* 新建 `e:\codes\image2web\backend\app\services\admin_auth_service.py`
  * 专门封装管理员 `Key` 校验逻辑。
  * 从配置文件读取唯一管理员 `Key`，与请求头中的 `X-API-Key` 做常量时间比对。

* 新建 `e:\codes\image2web\backend\app\services\generation_service.py`

  * 封装任务创建和任务查询能力。

  * `create_task` 负责鉴权、校验额度、校验最多 3 张图片、保存上传图到统一文件管理体系、写入 `pending` 任务并立即返回。

  * `get_task_detail` 负责返回当前任务状态、进度文案、结果图地址和失败原因。

  * 增加 `list_task_history`，返回独立会话式的历史生成记录，供前端单页历史面板展示。

* 新建 `e:\codes\image2web\backend\app\services\storage_service.py`

  * 负责统一文件命名、日期目录创建、二进制写盘、URL 映射和文件元数据落库。
  * 区分输入图目录与结果图目录，例如 `data\uploads\YYYY\MM\DD` 和 `data\images\YYYY\MM\DD`。
  * 文件命名策略建议为：`{timestamp}_{short_uuid}.{ext}`，避免用户原文件名直接暴露到存储路径。
  * 保存文件时同步写入 `media_asset` 表，记录该图片来自哪个 `api_key_id`、哪个任务、哪条生成记录。

* 新建 `e:\codes\image2web\backend\app\services\admin_service.py`
  * 封装管理操作：创建用户 `Key`、充值、列表、禁用/启用、查看生成记录、查看平台总生成次数统计。

* 新建 `e:\codes\image2web\backend\app\services\task_worker_service.py`
  * 负责异步消费 `GenerationTask`。
  * 从数据库领取 `pending` 任务，更新为 `processing` 后调用 `image2` 适配层。
  * 生成成功时保存结果图到统一文件管理体系、写入 `GenerationRecord`、扣减次数、回填 `result_record_id`、更新任务为 `success`。
  * 生成失败时更新任务为 `failed` 并记录 `error_message`，不扣减次数。
  * 在执行任务前读取关联的输入图列表，并按脚本逻辑组装第三方所需的 `messages`。

* 新建 `e:\codes\image2web\backend\app\services\task_scheduler_service.py`
  * 在应用启动时拉起轻量 worker 循环。
  * 定时扫描 `pending` 任务，并接管异常中断遗留的 `processing` 超时任务。

* 新建 `e:\codes\image2web\backend\app\providers\base.py`

  * 定义统一 `image2` 适配器接口，例如 `generate_image(prompt, input_images, negative_prompt)`。

* 新建 `e:\codes\image2web\backend\app\providers\image2_provider.py`
  * 基于 `e:\codes\image2web\script\image2test.py` 整理正式 provider。
  * 复用脚本中的三段核心逻辑：本地图片转 Base64、组装 `messages`、提取返回中的图片 URL 并下载结果图。
  * 将脚本里的单张 `image_url` 扩展为最多 3 张：`content` 数组顺序为 1 个文本块 + 1 到 3 个 `image_url` 块。
  * 把脚本中的硬编码 `API_BASE_URL`、`API_KEY`、`IMAGE_MODEL` 改为读取后端配置文件。

* 新建 `e:\codes\image2web\backend\app\providers\factory.py`
  * 根据配置选择当前供应方实现，保证后续替换真实 `image2` 服务时改动最小。

### 4. 后端 API 设计

* 新建 `e:\codes\image2web\backend\app\api\deps.py`
  * 提供统一 `X-API-Key` 解析。
  * 在依赖层进一步区分“当前用户 Key”和“当前管理员 Key”。
  * 用户依赖走数据库校验，管理员依赖走配置文件校验。

* 新建 `e:\codes\image2web\backend\app\api\routes\auth.py`
  * `GET /api/auth/me`
  * 用于用户端校验当前 `Key` 是否有效并返回名称、剩余次数、状态。

* 新建 `e:\codes\image2web\backend\app\api\routes\generation.py`

  * `POST /api/generations`

  * 创建图片生成任务，立即返回 `taskId` 和当前状态，不直接等待图片结果。
  * 请求体采用 `multipart/form-data`，字段包括：
    * `prompt`
    * `negativePrompt`
    * `templateId`
    * `referenceRecordId`
    * `images[]`，最多 3 个文件

  * `GET /api/generations/tasks/{task_id}`

  * 返回指定任务的执行状态、进度文案、失败原因和结果图地址。

  * `GET /api/generations/tasks`

  * 返回当前 `Key` 自己提交的任务列表，便于前端恢复页面状态。

  * `GET /api/generations`

  * 返回当前 `Key` 自己的最终生成记录列表。

  * `GET /api/generations/history`

  * 返回用户侧历史工作台列表，按时间倒序聚合每次独立生成，用于单页历史抽屉而不是单独历史页面。

* 新建 `e:\codes\image2web\backend\app\api\routes\admin.py`
  * `GET /api/admin/me`
  * 校验当前管理员 `Key` 是否有效。
  * `POST /api/admin/keys`
  * `PATCH /api/admin/keys/{id}/recharge`
  * `PATCH /api/admin/keys/{id}/status`
  * `GET /api/admin/keys`
  * `GET /api/admin/generations`
  * `GET /api/admin/tasks`
  * `GET /api/admin/stats`
  * 提供平台总生成次数、成功次数、失败次数、用户 Key 数量等概览。
  * 管理后台可额外查看任务队列状态，如等待中、执行中、失败任务数量。
  * 所有管理接口都通过 `X-API-Key` 传入管理员 `Key`，并直接比对配置文件中的唯一管理员 `Key`。




* 新建 `e:\codes\image2web\backend\app\api\router.py`

  * 汇总所有路由，确保接口边界明确。

### 5. 前端用户界面

* 新建 `e:\codes\image2web\frontend\src\api\client.ts`
  * 统一封装 Axios 请求实例。
  * 基于 `import.meta.env.VITE_API_BASE_URL` 生成基础地址。
  * 自动携带本地保存的 `X-API-Key`，并支持按用户页与后台页分别存储不同的 `Key`。
  * 提供 JSON 请求实例和 `multipart/form-data` 上传辅助方法。

* 新建 `e:\codes\image2web\frontend\src\config\env.ts`
  * 对 `import.meta.env` 做统一读取和兜底封装，避免业务代码直接散读环境变量。

* 新建 `e:\codes\image2web\frontend\src\stores\session.ts`

  * 保存当前输入的用户 `Key`、剩余次数、最近任务状态和校验状态。
  * 额外保存当前工作台草稿、已选图片、当前选中的历史记录和最近一次参考编辑来源。

* 新建 `e:\codes\image2web\frontend\src\stores\admin-session.ts`

  * 保存管理员 `Key`、管理员身份校验状态和后台统计信息。

* 新建 `e:\codes\image2web\frontend\src\composables\useGenerationTask.ts`
  * 封装任务提交、轮询、停止轮询、页面恢复轮询逻辑。
  * 轮询间隔默认 2 到 3 秒；任务进入 `success` 或 `failed` 后自动停止。
  * 提交前统一校验图片数量不超过 3 张。

* 新建 `e:\codes\image2web\frontend\src\data\style-templates.ts`

  * 内置风格模板数据，包含示例图、提示词、说明。
  * 模板内容围绕图像编辑与风格转换设计，而不是泛聊天话术。

* 新建 `e:\codes\image2web\frontend\src\views\HomeView.vue`

  * 首页主视图，也是用户唯一工作台页面。
  * 采用“仿 ChatGPT 但以图像生成为主导”的布局：左侧为历史抽屉，中间为对话式工作台，右侧为风格模板与快捷操作区；在窄屏下折叠为抽屉和底部面板。
  * 所有核心行为都留在同一页面内完成：上传图片、填写提示词、提交任务、查看状态、回顾历史、选择旧图再次编辑。
  * 提交后按钮进入 `生成中` 状态，界面展示排队中或执行中的文案，不阻塞整页交互。

* 新建 `e:\codes\image2web\frontend\src\components\PromptComposer.vue`

  * 输入主提示词、负向提示词、模板快捷填充。
  * 集成上传图片区，限制最多 3 张，超出上限立即前端提示并禁止继续添加。

* 新建 `e:\codes\image2web\frontend\src\components\UploadImageTray.vue`
  * 展示 0 到 3 张已选图片缩略图。
  * 支持拖拽上传、删除、替换、从历史结果图一键加入当前输入区。
  * 当达到 3 张时，上传入口变为禁用态并给出原因提示。

* 新建 `e:\codes\image2web\frontend\src\components\TemplateGallery.vue`

  * 展示静态模板卡片，点击后可自动填充提示词。
  * 模板区强调“图像处理结果预期”，例如“室内换景”“产品主图精修”“二次元重绘”“光影增强”“材质替换”“海报风格化”。

* 新建 `e:\codes\image2web\frontend\src\components\GenerationResult.vue`

  * 展示最近生成图、任务状态、错误提示、加载状态。
  * 结果图卡片内直接提供“再次编辑”“设为输入图”“复制提示词”“对比查看原图”操作。

* 新建 `e:\codes\image2web\frontend\src\components\TaskStatusPanel.vue`
  * 展示“排队中 / 生成中 / 已完成 / 失败”状态。
  * 在生成过程中显示进度文案，如“任务已提交”“正在调用生成接口”“图片保存中”。

* 新建 `e:\codes\image2web\frontend\src\components\HistoryDrawer.vue`
  * 单页左侧历史抽屉，按时间倒序展示每次独立生成记录。
  * 每条历史显示缩略图、提示词摘要、创建时间、状态标签。
  * 点击历史项不会跳转页面，而是在当前工作台中展开详情并支持再次编辑。

* 新建 `e:\codes\image2web\frontend\src\components\RevisionChainPanel.vue`
  * 展示当前结果与其来源记录的关系链。
  * 帮助用户理解“当前编辑来自哪一次结果”，但不把它渲染成多轮记忆聊天。

* 新建 `e:\codes\image2web\frontend\src\views\AdminView.vue`

  * 提供平台生成次数统计、任务队列状态、用户 `Key` 列表、创建、充值、状态切换、生成记录查询。
  * 独立管理界面，使用管理员 `Key` 进入。

* 新建 `e:\codes\image2web\frontend\src\router\index.ts`

  * 至少拆分为 `/` 用户页与 `/admin` 管理页。

* 新建 `e:\codes\image2web\frontend\src\styles\main.css`

  * 采用暗色工作台风格，整体参考 ChatGPT 的沉浸式编辑体验，但把视觉中心放在图片、输入区和结果卡片。
  * 首页重点突出生成输入区、图片上传区、结果图区和历史抽屉，不做复杂营销型首页。
  * 增加以下关键动效：
    * 结果图进入时使用渐显和轻微上浮动画。
    * 历史抽屉展开和收起使用平滑滑入动画。
    * 任务状态切换时使用进度条和脉冲态反馈。
    * “再次编辑”加入输入区时，缩略图有吸附到上传托盘的过渡动画。

### 6. 模板与示例资源

* 新建 `e:\codes\image2web\frontend\src\assets\templates\`

  * 存放静态模板示例图。

  * 初始可准备 4 到 6 组模板，如写实、人像、二次元、海报、极简插画、产品图。

* 在 `style-templates.ts` 中为每个模板定义：

  * 模板名称。

  * 示例图路径。

  * 推荐提示词。

  * 负向提示词。

  * 适用场景说明。

* 初始模板建议细化为以下 6 类，保证更贴近图像生成主场景：
  * 产品精修：去杂物、统一背景、提升商业感。
  * 室内换景：替换桌面、墙面、地板、光照氛围。
  * 人像风格化：保留主体结构，改变服装、妆造、质感。
  * 二次元重绘：把实拍或草图转成插画风。
  * 海报增强：增加标题感、戏剧光影和视觉冲击。
  * 材质替换：把物体表面切换成木纹、金属、玻璃、陶瓷等。

### 7. 核心生成接口详细文档

* 核心第三方接口整理来源：
  * 以 [image2test.py](file:///e:/codes/image2web/script/image2test.py#L77-L159) 为当前唯一已跑通的事实来源。
  * 重点沿用其中的消息体结构、图片转 Base64 逻辑、返回图片 URL 提取逻辑和结果图下载逻辑。

* 第三方请求组装规则：
  * `messages` 始终为单轮数组，只有一个 `role=user` 的消息体。
  * `content` 数组第一个元素固定为文本块 `{ type: "text", text: prompt }`。
  * 后续追加 1 到 3 个图片块 `{ type: "image_url", image_url: { url: dataUri } }`。
  * 这意味着用户每次生成都是独立请求，不带历史上下文记忆。

* 网站内部任务创建接口建议：
  * `POST /api/generations`
  * `Content-Type: multipart/form-data`
  * 字段：
    * `prompt: string`
    * `negativePrompt?: string`
    * `templateId?: string`
    * `referenceRecordId?: string`
    * `images[]: File[]`，最多 3 个
  * 校验规则：
    * `images.length <= 3`
    * 至少满足“文本非空”或“有 1 张输入图”之一
    * 文件类型仅允许 `png/jpg/jpeg/webp`

* 网站内部任务状态接口建议：
  * `GET /api/generations/tasks/{taskId}`
  * 返回：
    * `status`
    * `progressMessage`
    * `inputImages`
    * `resultImage`
    * `referenceRecordId`
    * `errorMessage`
    * `remainingCount`
    * `apiKeyName`

* worker 内部执行步骤建议：
  * 读取任务和输入图。
  * 将输入图逐一转成 Base64 Data URL。
  * 构造第三方 `messages`。
  * 调用上游 `chat/completions` 接口。
  * 从返回内容中提取结果图 URL。
  * 下载结果图到按日期分目录的本地路径，并完成重命名。
  * 写入统一文件资产记录、生成记录并完成扣次。

### 8. 用户端交互详细文档

* 页面定位：
  * 用户只有一个图像生成工作台页面，不存在“首页 -> 历史页 -> 编辑页”的跳转链路。
  * 历史、模板、当前输入、生成结果都在同一屏幕内完成。

* 页面主结构：
  * 左侧：历史抽屉，展示每次独立生成记录。
  * 中间：当前工作台，包含提示词编辑、图片上传、任务状态和结果展示。
  * 右侧：风格模板、快捷操作、当前可复用的历史图片。

* 独立生成与历史回顾规则：
  * 每次点击“生成”都创建新的独立任务。
  * 历史记录只负责回顾和再利用，不会自动带入整段上下文。
  * 点击历史结果的“再次编辑”后，只把选中的图片和必要提示词带回当前工作台，不带入历史上下文消息。

* 二次编辑交互：
  * 用户可从最近结果或历史抽屉中点击“设为输入图”。
  * 被选中的历史结果图会以缩略图形式进入上传托盘，占用 3 张上限中的一个位置。
  * 若已达到 3 张上限，则要求用户先移除一张，再加入新的参考图。

* 动画与反馈：
  * 任务提交成功后，提交按钮切为加载态，输入区顶部出现流动态进度提示。
  * 历史记录新增项时，从顶部轻微滑入。
  * 新结果生成完成后，结果卡片渐显并自动滚动到可见区域。
  * 把历史图加入当前输入托盘时，使用“缩略图飞入”动画提升操作反馈。

### 9. 事务与错误处理策略

* 异步生成流程按以下顺序执行：
  * 用户调用 `POST /api/generations`，后端校验 `Key` 是否存在、启用且剩余次数大于 0。

  * 后端写入一条 `pending` 状态的 `GenerationTask` 并立即返回 `taskId`。

  * worker 轮询领取任务，将状态更新为 `processing`。

  * worker 调用 `image2` 适配层生成图片。

  * 生成成功后图片写入本地目录。

  * 写入 `GenerationRecord`。

  * 扣减 `remaining_count`。

  * 更新任务为 `success`，回填结果图地址与关联记录。

* 失败分支处理：
  * 上游生成失败：任务标记为 `failed`，记录错误信息，不扣减次数。
  * 图片写盘失败：任务标记为 `failed`，不扣减次数。
  * 数据库提交失败：回滚事务，并按需删除已写入的孤儿文件。
  * worker 异常退出：应用启动时扫描超时的 `processing` 任务并重置为 `pending` 或标记失败。
  * 管理员 `Key` 误调生成接口：因不在用户 `Key` 表中，直接返回无效或无权限错误，不创建生成记录。

* 前端交互策略：
  * 提交任务成功后立即进入轮询，不等待单个 HTTP 请求挂起。
  * 用户刷新页面后，可通过最近任务列表恢复轮询状态。
  * 连续轮询达到上限后提示“后台仍在处理中”，允许用户稍后手动刷新。
  * 上传图片超过 3 张时在前端即时拦截，同时后端仍保持兜底校验。

### 10. 验证与测试

* 新建 `e:\codes\image2web\backend\tests\test_key_service.py`
  * 校验无效 `Key`、禁用 `Key`、余额不足、管理员 `Key` 越权调用、成功扣减逻辑。

* 新建 `e:\codes\image2web\backend\tests\test_generation_api.py`

  * 校验任务创建成功立即返回 `taskId`。
  * 校验任务成功时状态流转、结果落库、扣减次数。
  * 校验任务失败时不扣减次数。
  * 校验上传第 4 张图片时被拒绝。

* 新建 `e:\codes\image2web\backend\tests\test_task_worker_service.py`
  * 校验 worker 领取任务、状态更新、超时回收、失败回写逻辑。
  * 校验 provider 会按脚本逻辑把 1 到 3 张图片组装进 `messages`。

* 新建 `e:\codes\image2web\backend\tests\test_admin_api.py`
  * 校验配置文件中的管理员 `Key` 登录、创建用户 `Key`、充值、启停用、记录检索、统计接口。

* 新建 `e:\codes\image2web\frontend\src\api\__tests__\client.spec.ts`
  * 校验 Axios 基础地址来自环境变量，且请求头能正确注入 `X-API-Key`。

* 新建 `e:\codes\image2web\frontend\src\components\__tests__\TemplateGallery.spec.ts`

  * 校验模板点击后能回填提示词。

* 新建 `e:\codes\image2web\frontend\src\components\__tests__\PromptComposer.spec.ts`

  * 校验提交参数拼装与 `Key` 校验前置提示。
  * 校验第 4 张图片无法加入上传区。

* 新建 `e:\codes\image2web\frontend\src\composables\__tests__\useGenerationTask.spec.ts`
  * 校验任务轮询启动、停止、成功收敛与失败收敛逻辑。

* 新建 `e:\codes\image2web\frontend\src\components\__tests__\HistoryDrawer.spec.ts`
  * 校验历史项点击后不会发生路由跳转，而是回填当前工作台状态。

## Verification Steps

* 后端验证
  * 安装依赖后启动 FastAPI 服务，确认 `GET /api/auth/me`、`POST /api/generations`、`GET /api/generations/tasks/{task_id}`、`GET /api/admin/me`、管理接口都可访问。
  * 在后端配置文件中设置管理员 `Key`、第三方接口 `url` 与 `API_KEY`，验证服务能正常加载配置。
  * 验证用户提交生成后能立即拿到 `taskId`，且请求不会长时间阻塞等待图片。
  * 验证 worker 能将任务从 `pending` 推进到 `processing`、`success` 或 `failed`。
  * 验证用户 `Key` 可生成、配置中的管理员 `Key` 可进后台但不能调用生成接口。
  * 验证无效或余额为 0 的用户 `Key` 被拒绝。
  * 验证单次任务上传 0 到 3 张图片均可正常处理，第 4 张会被接口拒绝。
  * 验证 `script\image2test.py` 中的单图消息结构已被扩展为多图消息结构，并能成功调用上游接口。
  * 验证上传图与生成图都会被重命名，并分别保存到按日期分层的目录中。
  * 验证 `media_asset`、`generation_input_image`、`generation_record` 中都能追溯图片来源 `api_key_id`、任务和文件路径。
  * 验证生成成功后数据库记录与磁盘文件一致，且 `remaining_count` 正确减 1。
  * 验证生成失败时会记录失败状态但不扣减次数。

* 前端验证
  * 输入有效 `Key` 后可展示剩余次数并发起生成。
  * 提交任务后页面立即显示“排队中 / 生成中”，并通过轮询更新状态。
  * 任务完成后自动展示图片；任务失败后展示错误原因并停止轮询。
  * 上传第 4 张图片时即时提示“最多上传 3 张”。
  * 从历史结果图点击“再次编辑”后，不发生页面跳转，而是把图片带回当前工作台继续创建新任务。
  * 管理页使用管理员 `Key` 进入后，可查看总生成次数、创建用户 `Key`、充值、切换启停用，并查看生成记录。
  * 管理页可查看任务队列概览和失败任务。
  * 切换开发、测试、生产环境时，Axios 会自动指向对应的 `VITE_API_BASE_URL`。

* 联调验证
  * 前后端联调后，确认异步任务从提交到出图的完整链路可用。
  * 前后端联调后，确认静态图片 URL 能正确访问。
  * 确认用户端所有核心操作都在单页工作台内完成，不触发路由跳转。
  * 确认同一请求头下，用户接口走数据库用户 `Key` 校验，管理接口走配置文件管理员 `Key` 校验，权限严格隔离。
