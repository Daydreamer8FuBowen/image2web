# image2web

一个基于 `FastAPI + SQLite + Vue3` 的图像生成与编辑网站，封装第三方 `image2` 接口，支持 `Key` 鉴权、异步任务生成、历史回顾、结果二次编辑、图片文件统一管理。

## 项目特点

- 用户通过 `Key` 使用网站，按生成成功后扣减次数
- 管理后台通过配置文件中的管理员 `Key` 登录，不入库
- 图像生成采用“提交任务 -> 后台异步执行 -> 前端轮询结果”模式
- 单页工作台交互，支持最多上传 `3` 张图片
- 用户上传图和生成结果图统一重命名，并按日期目录保存
- 数据库可追踪图片来源 `Key`、任务、记录和文件路径

## 当前结构

```text
image2web
├─ backend                 # FastAPI 后端
├─ frontend                # Vue3 + Vite 前端
├─ data                    # SQLite 与图片存储目录
├─ script                  # 已跑通的 image2 原型脚本
└─ README.md
```

## 后端结构

```text
backend
├─ app
│  ├─ api                  # 路由与依赖
│  ├─ core                 # 配置、数据库、错误码
│  ├─ models               # SQLAlchemy 模型
│  ├─ providers            # 第三方 image2 适配器
│  ├─ schemas              # Pydantic DTO
│  ├─ services             # 业务服务、任务 worker、文件管理
│  └─ main.py              # FastAPI 启动入口
├─ tests                   # 后端单元测试
├─ .env.example            # 后端配置样例
└─ requirements.txt
```

## 前端结构

```text
frontend
├─ src
│  ├─ api                  # Axios 请求封装
│  ├─ components           # 单页工作台组件
│  ├─ composables          # 任务轮询逻辑
│  ├─ config               # 环境变量读取
│  ├─ data                 # 风格模板数据
│  ├─ router               # 路由
│  ├─ stores               # Pinia 状态
│  ├─ styles               # 页面样式
│  └─ views                # 用户页 / 后台页
├─ .env*                   # 前端分环境配置
└─ package.json
```

## 核心能力

### 1. 用户侧

- 输入用户 `Key` 后进入图像工作台
- 上传 `0~3` 张参考图并输入提示词
- 提交后立即返回任务，不阻塞请求
- 前端轮询任务状态，完成后展示结果图
- 历史结果支持再次加入输入区进行二次编辑

### 2. 管理侧

- 使用配置文件中的 `ADMIN_LOGIN_KEY` 进入后台
- 查看平台统计信息
- 创建用户 `Key`
- 查看用户 `Key` 列表

### 3. 文件管理

- 上传图保存到 `data/uploads/YYYY/MM/DD`
- 生成图保存到 `data/images/YYYY/MM/DD`
- 所有图片统一重命名，避免直接暴露原文件名
- 通过 `media_assets` 表追踪文件来源

## 第三方 image2 接口来源

当前正式适配器逻辑整理自已跑通原型脚本：

- [image2test.py](file:///e:/codes/image2web/script/image2test.py)

该脚本已经验证了以下能力：

- 本地图片转 Base64 Data URL
- 按 `chat/completions` 结构组装 `messages`
- 从返回文本中提取结果图 URL
- 下载结果图到本地

在后端中，这部分逻辑已收敛到：

- [image2_provider.py](file:///e:/codes/image2web/backend/app/providers/image2_provider.py)

## 配置说明

后端配置样例见：

- [backend/.env.example](file:///e:/codes/image2web/backend/.env.example)

主要字段：

- `DATABASE_URL`: SQLite 数据库地址
- `UPLOAD_IMAGE_DIR`: 用户上传图根目录
- `GENERATED_IMAGE_DIR`: 生成结果图根目录
- `IMAGE2_BASE_URL`: 第三方接口地址
- `IMAGE2_API_KEY`: 第三方接口密钥
- `IMAGE2_MODEL`: 模型名，当前默认 `gpt-image-2`
- `ADMIN_LOGIN_KEY`: 管理后台登录 Key
- `CORS_ORIGINS`: 前端访问域名

前端通过以下文件区分环境接口地址：

- `frontend/.env`
- `frontend/.env.development`
- `frontend/.env.test`
- `frontend/.env.production`

关键变量：

- `VITE_API_BASE_URL`

## 本地开发

### 1. 后端



安装依赖：

```bash
python.exe -m pip install -r backend/requirements.txt
```

启动服务：

```bash
python.exe -m uvicorn app.main:app --reload --app-dir backend
```

默认接口：

- 健康检查：`GET /health`
- 用户鉴权：`GET /api/auth/me`
- 创建任务：`POST /api/generations`
- 查询任务：`GET /api/generations/tasks/{task_id}`
- 历史记录：`GET /api/generations/history`
- 管理后台：`/api/admin/*`

### 2. 前端

安装依赖：

```bash
cd frontend
npm install
```

启动开发环境：

```bash
npm run dev
```

生产构建：

```bash
npm run build
```

测试：

```bash
npm run test
```

## 测试说明

后端要求按模块开发后及时补测试并先跑通再继续开发。

当前后端测试文件：

- [test_key_service.py](file:///e:/codes/image2web/backend/tests/test_key_service.py)
- [test_admin_api.py](file:///e:/codes/image2web/backend/tests/test_admin_api.py)
- [test_generation_api.py](file:///e:/codes/image2web/backend/tests/test_generation_api.py)
- [test_task_worker_service.py](file:///e:/codes/image2web/backend/tests/test_task_worker_service.py)

执行方式：

```bash
set PYTHONPATH=E:\codes\image2web\backend
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
D:\Anaconda3\envs\pythonProject\python.exe -m pytest backend/tests -q
```

前端测试文件：

- [client.spec.ts](file:///e:/codes/image2web/frontend/src/api/__tests__/client.spec.ts)
- [TemplateGallery.spec.ts](file:///e:/codes/image2web/frontend/src/components/__tests__/TemplateGallery.spec.ts)
- [PromptComposer.spec.ts](file:///e:/codes/image2web/frontend/src/components/__tests__/PromptComposer.spec.ts)
- [HistoryDrawer.spec.ts](file:///e:/codes/image2web/frontend/src/components/__tests__/HistoryDrawer.spec.ts)
- [useGenerationTask.spec.ts](file:///e:/codes/image2web/frontend/src/composables/__tests__/useGenerationTask.spec.ts)

## 当前实现进度

已完成：

- 后端项目骨架
- 用户 `Key` 鉴权
- 管理员配置式登录
- 异步任务创建与查询
- 文件统一保存与重命名
- image2 provider 首版接入
- 前端单页图像工作台
- 风格模板展示
- 基础后台统计与用户 Key 创建
- 前后端基础测试与构建验证

待继续补充：

- 后台页中的 Key 充值与禁用/启用交互
- 管理后台任务列表与生成记录列表
- 更完整的联调启动脚本
- 更细粒度的任务状态和失败恢复策略

## 注意事项

- 用户侧每次生成都是独立任务，不共享历史对话记忆
- 历史结果“再次编辑”本质上是把旧图重新作为输入图，发起新的独立任务
- 上传图片限制为最多 `3` 张
- 如果本机 `pytest` 被全局插件污染，需设置：

```bash
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
```
