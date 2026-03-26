# Smart Customer Service - Stage 2

智能客服系统 - 阶段二实现（多轮对话与工具调用）

## 功能特性

✅ **多轮对话管理**（新增）
- 使用 LangGraph 构建状态化对话流程
- 支持上下文保持和参数收集
- 智能追问缺失参数

✅ **工具调用**（新增）
- 订单查询工具：`query_order(order_id)`
- 退款申请工具：`process_refund(order_id, reason)`
- 发票开具工具：`issue_invoice(order_id, invoice_type, invoice_title)`
- 自动工具选择和参数绑定

✅ **智能意图识别**
- 订单查询 (order_query)
- 退款申请 (refund_request)
- 发票开具 (invoice_request)
- 一般咨询 (general)
- 对话上下文感知，保持意图连贯性

✅ **参数自动提取**
- 从用户消息中提取关键参数
- 参数不完整时自动追问
- 多轮对话中累积参数

✅ **结构化日志**
- 对话状态持久化
- 工具调用记录
- 保存到 `logs/conversations.jsonl` 文件

## 快速开始

### 1. 配置环境变量

复制示例配置文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 OpenAI API Key：
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
```

### 2. 安装依赖（如果还没有）

```bash
uv sync
```

### 3. 运行程序

```bash
python -m smart_customer_service.main
```

或者在项目根目录：
```bash
cd ..
python -m smart_customer_service.main
```

## 使用示例

### 示例 1：多轮订单查询

```
🤖 智能客服系统 - Stage 2
============================================================
💡 功能：多轮对话 + 工具调用
🔧 支持：订单查询、退款申请、发票开具
💬 输入 '退出'、'exit' 或 'quit' 结束对话
💬 输入 'reset' 重置对话状态
============================================================

👤 您: 查订单

🔍 正在处理...
🤖 客服: 请提供您的订单号，格式如：ORD001

👤 您: ORD001

🔍 正在处理...
🤖 客服: 📦 订单信息查询成功

订单号：ORD001
订单状态：已发货
下单时间：2026-03-24 10:30:00
订单金额：¥7999.00

📍 物流信息：
物流公司：顺丰速运
运单号：SF1234567890
当前位置：上海分拨中心
预计送达：2026-03-27
```

### 示例 2：退款申请流程

```
👤 您: 我要申请退款

🔍 正在处理...
🤖 客服: 请提供您的订单号，格式如：ORD001

👤 您: ORD003

🔍 正在处理...
🤖 客服: ✅ 退款申请已提交，退款金额: ¥3998.00

退款单号：REF003
退款金额：¥3998.00
处理状态：退款处理中
预计到账：3-5个工作日
```

### 示例 3：直接查询（提供完整信息）

```
👤 您: 查询订单 ORD002

🔍 正在处理...
🤖 客服: 📦 订单信息查询成功

订单号：ORD002
订单状态：配送中
下单时间：2026-03-23 15:20:00
订单金额：¥15999.00

📍 物流信息：
物流公司：京东物流
运单号：JD9876543210
当前位置：北京朝阳区配送站
预计送达：2026-03-26
```

## 测试用例

运行自动化测试：

```bash
python test_stage2.py
```

测试覆盖场景：

1. **多轮对话流程**
   - 用户说"查订单"但未提供订单号
   - 系统追问订单号
   - 用户提供订单号
   - 系统调用工具并返回结果

2. **退款申请流程**
   - 用户说"我要申请退款"
   - 系统追问订单号
   - 用户提供订单号
   - 系统调用退款工具

3. **直接查询（一次性提供完整信息）**
   - 用户说"查询订单 ORD002"
   - 系统直接调用工具返回结果

4. **不同订单的工具调用**
   - ORD001：已发货状态
   - ORD002：配送中状态
   - ORD003：已签收状态

5. **对话状态管理**
   - 使用 `reset` 命令重置对话
   - 测试上下文保持功能

## 项目结构

```
smart_customer_service/
├── __init__.py
├── main.py          # CLI 入口（Stage 2：多轮对话）
├── graph.py         # LangGraph 对话流程（新增）
├── tools.py         # 工具定义（新增）
├── chain.py         # LangChain 链构建（Stage 1）
├── prompts.py       # Prompt 模板
├── schemas.py       # Pydantic 数据模型
├── config.py        # 配置管理
└── README.md        # 本文件

tests/
└── test_stage2.py   # Stage 2 自动化测试
```

## 日志文件

对话信息会保存到：
- `logs/conversations.jsonl` - 对话状态和工具调用记录（Stage 2）
- `logs/queries.jsonl` - 结构化信息提取记录（Stage 1，已弃用）

每条记录包含：
- `timestamp`: 时间戳
- `intent`: 识别的意图
- `parameters`: 收集的参数
- `tool_result`: 工具调用结果
- `message_count`: 消息数量

## 技术架构

### LangGraph 对话流程

```
用户输入
    ↓
extract_intent (提取意图和参数)
    ↓
check_params (检查必需参数)
    ↓
   ┌─────────────┐
   │ 参数完整？   │
   └─────────────┘
     Yes ↓    ↓ No
call_tool   ask (追问缺失参数)
     ↓         ↓
generate_response  返回用户
     ↓
  返回用户
```

### 工具定义

所有工具使用 `@tool` 装饰器定义，支持：
- 自动参数验证
- 类型检查
- 文档生成

### 状态管理

使用 TypedDict 定义对话状态：
- `messages`: 消息历史
- `intent`: 当前意图
- `parameters`: 已收集参数
- `tool_result`: 工具调用结果
- `waiting_for_parameter`: 等待的参数
- `completed`: 完成标志

## 下一步

**Stage 3** 将实现：
- 模型热更新
- 插件热重载
- FastAPI 健康检查接口 `/health`
- 完整的自动化测试套件
- 生产环境部署
