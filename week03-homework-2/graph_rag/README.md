# Graph RAG System

融合文档检索（RAG）和知识图谱推理（KG）的多跳问答系统。

## 系统特点

✅ **双重信息源**
- 文档检索 (RAG): 使用向量相似度检索相关文档
- 知识图谱 (KG): 使用 Neo4j 进行结构化推理

✅ **多跳推理**
- 支持跨多个实体的推理
- 自动追踪推理路径
- 可配置的跳数限制

✅ **联合评分机制**
- 向量相似度权重 + 图谱可信度权重
- 动态选择主要信息源
- 可配置的置信度阈值

✅ **错误检测与验证**
- 图谱结果有效性验证
- 信息冲突检测
- 可解释性输出

✅ **完整的 API 支持**
- RESTful API 接口
- 交互式 CLI 工具
- 演示模式

## 系统架构

```
用户查询
    ↓
查询分类 & 实体提取 (LLM)
    ├─→ 文档检索 (Vector Store)
    │   - OpenAI Embeddings
    │   - 相似度搜索
    │   - Top-K 文档
    │
    └─→ 图谱推理 (Neo4j)
        - Cypher 查询
        - 多跳路径查找
        - 关系提取
    ↓
结果融合 & 评分
    ├─ 向量权重: 50%
    └─ 图谱权重: 50%
    ↓
结果验证
    ↓
LLM 生成答案
    ↓
可解释性输出
```

## 前置要求

1. **启动服务**
   ```bash
   cd ..
   ./services.sh start
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 添加 OPENAI_API_KEY
   ```

3. **验证服务**
   - Neo4j: http://localhost:7474 (neo4j/password123)
   - 检查连接状态

## 使用方法

### 1. 初始化系统（首次运行）

```bash
python -m graph_rag.main --mode init
```

初始化会：
- 清空 Neo4j 图谱
- 加载公司数据（10家公司）
- 创建关系（12种关系）
- 构建向量索引

### 2. 演示模式

```bash
python -m graph_rag.main --mode demo
```

运行预定义的查询示例：
- "阿里巴巴集团的最大股东是谁？"
- "蚂蚁集团是谁投资的？"
- "阿里巴巴有哪些子公司？"
- "软银集团和阿里巴巴是什么关系？"
- "腾讯和阿里巴巴有什么关系？"

### 3. 交互式查询

```bash
python -m graph_rag.main --mode query
```

交互式 CLI，支持：
- 自然语言查询
- 输入 'stats' 查看图谱统计
- 输入 'quit' 退出

### 4. API 模式

```bash
python -m graph_rag.main --mode api
```

启动 REST API 服务：
- 地址: http://localhost:8001
- 文档: http://localhost:8001/docs

## API 使用示例

### 查询问答

```bash
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "阿里巴巴集团的最大股东是谁？",
    "include_reasoning": true,
    "include_sources": true
  }'
```

### 获取公司信息

```bash
curl -X POST "http://localhost:8001/graph/company" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "阿里巴巴"
  }'
```

### 查找股东

```bash
curl -X POST "http://localhost:8001/graph/shareholders" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "阿里巴巴"
  }'
```

### 图谱统计

```bash
curl "http://localhost:8001/graph/stats"
```

### 系统状态

```bash
curl "http://localhost:8001/status"
```

## 配置说明

编辑 `config.py` 或设置环境变量：

```python
# Neo4j 配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"

# 检索配置
TOP_K_DOCS = 3        # 文档检索数量
TOP_K_GRAPH = 5       # 图谱结果数量
MAX_HOP = 3           # 最大跳数

# 融合评分权重
VECTOR_WEIGHT = 0.5   # 向量权重
GRAPH_WEIGHT = 0.5    # 图谱权重
CONFIDENCE_THRESHOLD = 0.6  # 置信度阈值

# OpenAI 配置
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"
```

## 项目结构

```
graph_rag/
├── __init__.py          # 包初始化
├── main.py             # 主入口（CLI）
├── api.py              # FastAPI REST API
├── config.py           # 配置文件
├── graph_store.py      # Neo4j 图谱存储
├── vector_store.py     # 向量存储
├── hybrid_query.py     # 混合查询引擎
├── data/               # 数据目录
│   ├── companies.json      # 公司数据
│   └── relationships.json  # 关系数据
├── README.md           # 本文件
└── report.md           # 实验报告
```

## 知识图谱

### 节点类型
- **Company**: 公司节点
  - 属性: id, name, type, industry, founded, description

### 关系类型
1. **MAJOR_SHAREHOLDER**: 主要股东（持股 > 5%）
2. **CONTROLS**: 控股（持股 > 50%）
3. **WHOLLY_OWNS**: 全资拥有（持股 100%）
4. **INVESTED_IN**: 投资关系
5. **COMPETES_WITH**: 竞争关系
6. **FOUNDED_BY**: 创立关系

### 示例数据
- 10 家公司：阿里巴巴、蚂蚁集团、软银、淘宝、阿里云、腾讯等
- 12 条关系：涵盖股权、控制、投资、竞争等

## 技术实现

### 1. 查询分类
使用 LLM 将查询分类为：
- `ownership`: 股权股东查询
- `relation`: 公司关系查询
- `general`: 一般信息查询
- `multi_hop`: 多跳推理查询

### 2. 实体提取
使用 LLM 从查询中提取公司名称

### 3. 文档检索 (RAG)
- 使用 OpenAI embeddings
- 向量相似度搜索
- 返回 Top-K 文档和相似度分数

### 4. 图谱推理 (KG)
根据查询类型执行不同的 Cypher 查询：

**股权查询:**
```cypher
MATCH path = (shareholder:Company)-[r:MAJOR_SHAREHOLDER|CONTROLS*1..3]->(target:Company)
WHERE target.name CONTAINS $name
RETURN shareholder, target, relationships(path)
```

**多跳推理:**
```cypher
MATCH path = (start:Company)-[*1..3]-(end:Company)
WHERE start.name CONTAINS $start_name AND end.name CONTAINS $end_name
RETURN nodes(path), relationships(path), length(path)
```

### 5. 结果融合
```python
hybrid_score = VECTOR_WEIGHT * vector_confidence + GRAPH_WEIGHT * graph_confidence
```

### 6. 结果验证
- 检查图谱结果是否为空
- 检查数据一致性
- 标记潜在错误

### 7. 答案生成
使用 LLM 综合所有信息生成最终答案，包括：
- 文档上下文
- 图谱推理结果
- 可信度评估
- 冲突处理

## 查询示例

### 示例 1: 股东查询
**问题:** "阿里巴巴集团的最大股东是谁？"

**推理路径:**
1. 识别查询类型：ownership
2. 提取实体：阿里巴巴集团
3. 文档检索：找到相关文档
4. 图谱查询：执行股东查询
5. 结果融合：图谱可信度更高
6. 生成答案：软银集团持股 24.8%

### 示例 2: 多跳推理
**问题:** "软银集团和蚂蚁集团有什么关系？"

**推理路径:**
1. 识别查询类型：multi_hop
2. 提取实体：软银集团、蚂蚁集团
3. 文档检索：找到两家公司文档
4. 图谱查询：查找路径
   - 软银 → 阿里巴巴 (24.8% 股权)
   - 阿里巴巴 → 蚂蚁 (33% 股权)
5. 结果融合：综合两个来源
6. 生成答案：间接关系，通过阿里巴巴

## 性能指标

- **查询延迟**: 2-5秒（包含 LLM 生成）
- **向量检索**: ~100ms
- **图谱查询**: ~50-200ms（取决于复杂度）
- **LLM 生成**: ~1-3秒

## 错误处理

### 图谱查询失败
系统会：
1. 记录错误
2. 降低图谱可信度为 0
3. 依赖向量检索结果
4. 在答案中说明

### 信息冲突
系统会：
1. 标记冲突
2. 显示两个来源的信息
3. 让 LLM 解释差异
4. 给出推荐答案

### 实体未找到
系统会：
1. 尝试模糊匹配
2. 使用向量检索兜底
3. 说明实体不存在

## 故障排查

### Neo4j 连接失败
```bash
# 检查 Neo4j 运行状态
docker ps | grep neo4j

# 重启服务
./services.sh restart

# 查看日志
./services.sh logs neo4j
```

### 图谱为空
```bash
# 重新初始化
python -m graph_rag.main --mode init
```

### 向量索引错误
```bash
# 重建索引
python -m graph_rag.main --mode init
```

## 扩展性

### 添加新公司
编辑 `data/companies.json`，然后：
```bash
python -m graph_rag.main --mode init
```

### 添加新关系类型
1. 编辑 `data/relationships.json`
2. 更新 `graph_store.py` 中的查询逻辑
3. 重新初始化

### 调整权重
编辑 `config.py`:
```python
VECTOR_WEIGHT = 0.3  # 降低向量权重
GRAPH_WEIGHT = 0.7   # 提高图谱权重
```

## 最佳实践

1. **首次运行**：使用 `--mode init` 初始化
2. **开发调试**：使用 `--mode demo` 测试
3. **生产部署**：使用 `--mode api` 提供服务
4. **定期备份** Neo4j 数据
5. **监控查询性能**和准确性

## License

Part of AI Engineer Training Homework - Week 3
