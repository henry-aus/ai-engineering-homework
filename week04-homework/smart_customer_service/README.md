# Smart Customer Service - Stage 1

智能客服系统 - 阶段一实现

## 功能特性

✅ **基础对话系统**
- 使用 LangChain 构建 Prompt → LLM → OutputParser 链
- 命令行界面（CLI）交互

✅ **时间推断**
- 支持相对时间表达："昨天"、"今天"、"明天"
- 支持复杂时间表达："三天前"、"上周五"、"上个月15号"
- 自动转换为标准日期格式（YYYY-MM-DD）

✅ **意图识别**
- 订单查询 (order_query)
- 退款申请 (refund_request)
- 发票开具 (invoice_request)
- 一般咨询 (general)

✅ **结构化日志**
- 控制台输出 JSON 格式
- 持久化到 `logs/queries.jsonl` 文件

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

```
🤖 智能客服系统 - Stage 1
============================================================
💡 功能：基础对话 + 时间推断
💬 输入 '退出'、'exit' 或 'quit' 结束对话
============================================================

👤 您: 我昨天下的单

🔍 正在分析...

============================================================
📊 提取的结构化信息:
============================================================
{
  "intent": "order_query",
  "date_mentioned": "2026-03-25",
  "original_date_expression": "昨天",
  "entities": {},
  "raw_message": "我昨天下的单"
}
============================================================

🤖 客服: 好的，我看到您想查询订单，时间是 2026-03-25 (昨天)。[已记录查询意图]
```

## 测试用例

测试不同的时间表达：

1. **简单相对时间**
   - "我今天下的单"
   - "我昨天下的单"
   - "我明天的订单"

2. **复杂相对时间**
   - "我三天前下的单"
   - "我上周五下的单"
   - "我上个月15号的订单"

3. **不同意图**
   - "我要申请退款"
   - "帮我开发票"
   - "你们的营业时间是？"

## 项目结构

```
smart_customer_service/
├── __init__.py
├── main.py          # CLI 入口
├── chain.py         # LangChain 链构建
├── prompts.py       # Prompt 模板
├── schemas.py       # Pydantic 数据模型
├── config.py        # 配置管理
└── README.md        # 本文件
```

## 日志文件

提取的结构化信息会保存到：
- `logs/queries.jsonl` - JSONL 格式，每行一条记录

## 下一步

**Stage 2** 将实现：
- 多轮对话管理
- 工具调用（订单查询、退款申请）
- LangGraph 状态管理

**Stage 3** 将实现：
- 模型热更新
- 插件热重载
- FastAPI 健康检查接口
- 自动化测试
