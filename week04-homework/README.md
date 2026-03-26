# 第四周作业

## 任务
构建一个小型多轮对话智能客服，支持工具调用以及模型与插件的热更新。

## 作业完成状态

✅ **阶段一：基础对话系统搭建** - 已完成
✅ **阶段二：多轮对话与工具调用** - 已完成
✅ **阶段三：热更新与生产部署** - 已完成

## 快速开始

### 1. 配置环境

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env 文件，填入你的 OpenAI API Key
# OPENAI_API_KEY=sk-...
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 运行程序

#### 方式 1：CLI 对话模式（Stage 2）

```bash
python -m smart_customer_service.main
```

#### 方式 2：API 服务模式（Stage 3）

```bash
# 启动 API 服务器
python -m smart_customer_service.api

# 访问 API 文档
open http://localhost:8000/docs

# 健康检查
curl http://localhost:8000/health
```

### 4. 运行测试

```bash
# Stage 2 测试：多轮对话
python test_stage2.py

# Stage 3 测试：发票插件
python test_stage3_invoice.py

# Stage 3 测试：热更新
python test_stage3_hot_reload.py

# Stage 3 测试：热更新 API（需要先启动服务器）
python test_stage3_hot_reload.py --api
```

## 作业思路指导

### 阶段一：基础对话系统搭建 ✅
使用 LangChain 构建基础 Chain：Prompt → LLM → OutputParser
- 用户说”我昨天下的单”，系统能结合当前时间推断”昨天”的具体日期
- 实现文件：`smart_customer_service/chain.py`

### 阶段二：多轮对话与工具调用 ✅
实现”订单查询””退款申请”等多轮交互流程，支持工具自动调用。
使用 LangGraph 构建以下流程：
- 用户说”查订单” → 追问”请提供订单号”
- 收到订单号后 → 调用 query_order(order_id) 工具
- 返回订单状态与物流信息

实现文件：
- `smart_customer_service/graph.py` - 对话流程图
- `smart_customer_service/tools.py` - 工具定义
- `smart_customer_service/main.py` - CLI 入口

### 阶段三：热更新与生产部署 ✅
实现模型与插件的热更新，完成系统部署与监控。

#### 1. 模型热更新 ✅
- 运行时动态切换 LLM 模型
- 更新模型配置（model_name, temperature）
- 版本管理和追踪

#### 2. 插件热重载 ✅
- 动态重载工具（tools.py）
- 文件监控自动重载
- 线程安全更新

#### 3. 健康检查接口 ✅
- GET /health - 服务健康状态
- 返回版本信息、配置状态、热重载状态

#### 4. 自动化测试 ✅
- ✅ 测试”发票开具”插件的功能正确性
- ✅ 验证热更新后旧会话不受影响
- ✅ 测试会话隔离机制

实现文件：
- `smart_customer_service/api.py` - FastAPI 应用
- `smart_customer_service/hot_reload.py` - 热重载管理器
- `smart_customer_service/config.py` - 配置管理（增强）
- `test_stage3_invoice.py` - 发票插件测试
- `test_stage3_hot_reload.py` - 热更新测试

## 功能特性

### 核心功能
- ✅ 意图识别（订单查询、退款申请、发票开具）
- ✅ 多轮对话管理
- ✅ 自动参数提取
- ✅ 智能参数追问
- ✅ 工具自动调用
- ✅ 日期时间推理

### 工具支持
- ✅ `query_order` - 订单查询
- ✅ `process_refund` - 退款申请
- ✅ `issue_invoice` - 发票开具

### 生产特性（Stage 3）
- ✅ 模型热更新
- ✅ 插件热重载
- ✅ 会话隔离
- ✅ 健康检查
- ✅ REST API
- ✅ 自动化测试

## API 使用示例

### 开始对话

```bash
curl -X POST http://localhost:8000/chat \
  -H “Content-Type: application/json” \
  -d '{“message”: “我要查订单”}'
```

### 继续对话

```bash
curl -X POST http://localhost:8000/chat \
  -H “Content-Type: application/json” \
  -d '{
    “session_id”: “your-session-id”,
    “message”: “ORD001”
  }'
```

### 触发模型热更新

```bash
curl -X POST http://localhost:8000/admin/reload-model \
  -H “Content-Type: application/json” \
  -d '{“temperature”: 0.7}'
```

### 触发插件热重载

```bash
curl -X POST http://localhost:8000/admin/reload-plugins
```

更多 API 示例请参考：[docs/STAGE3.md](./docs/STAGE3.md)

## 项目结构

```
week04-homework/
├── smart_customer_service/
│   ├── __init__.py
│   ├── main.py              # CLI 入口（Stage 2）
│   ├── api.py               # FastAPI 服务器（Stage 3）★
│   ├── hot_reload.py        # 热重载管理器（Stage 3）★
│   ├── config.py            # 配置管理（增强）★
│   ├── graph.py             # LangGraph 对话流程
│   ├── tools.py             # 工具定义
│   ├── chain.py             # LangChain 链（Stage 1）
│   ├── prompts.py           # Prompt 模板
│   └── schemas.py           # 数据模型
├── docs/
│   ├── STAGE3.md            # Stage 3 详细文档★
│   └── plans/
├── test_stage2.py           # Stage 2 测试
├── test_stage3_invoice.py   # 发票插件测试★
├── test_stage3_hot_reload.py # 热更新测试★
├── .env.example             # 配置示例（更新）★
├── pyproject.toml
└── README.md                # 本文件

★ = Stage 3 新增/更新
```

## 详细文档

- [Stage 3 完整文档](./docs/STAGE3.md) - 热更新、API、部署指南
- [Smart Customer Service README](./smart_customer_service/README.md) - Stage 2 功能说明

## 测试覆盖

### Stage 2 测试
- ✅ 多轮对话流程
- ✅ 参数追问机制
- ✅ 工具调用
- ✅ 订单查询、退款申请

### Stage 3 测试
- ✅ 发票插件功能（个人/企业发票）
- ✅ 参数验证
- ✅ 错误处理
- ✅ 热重载管理器
- ✅ 会话隔离
- ✅ API 端点
- ✅ 版本管理

## 如何提交作业

请fork本仓库，然后在以下目录分别完成编码作业：
- [week04-homework/smart_customer_service](./smart_customer_service)

其中:
- `main.py` - CLI 模式入口
- `api.py` - API 服务入口（Stage 3）

完成作业后，请在【极客时间】上提交你的fork仓库链接，精确到本周的目录，例如：
```
https://github.com/your-username/ai-engineer-training/tree/main/week04-homework
```

## 常见问题

### Q: 如何切换不同的阶段运行？
A:
- Stage 1: 使用 `smart_customer_service/chain.py`
- Stage 2: 运行 `python -m smart_customer_service.main`
- Stage 3: 运行 `python -m smart_customer_service.api`

### Q: 热更新会影响正在进行的对话吗？
A: 不会。每个会话在创建时会固定配置版本，热更新只影响新创建的会话。

### Q: 如何验证热更新是否成功？
A:
1. 访问 `/health` 端点查看版本号
2. 热更新后版本号应该增加
3. 运行 `test_stage3_hot_reload.py` 自动测试

### Q: 文件监控不工作怎么办？
A:
1. 确认 `PLUGIN_WATCH_ENABLED=true`
2. 手动调用 `/admin/reload-plugins` 端点
3. 查看服务器日志排查错误

## 许可证

MIT License