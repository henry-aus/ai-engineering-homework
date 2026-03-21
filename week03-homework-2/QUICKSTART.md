# Quick Start Guide

This guide will help you quickly get started with the Week 3 homework assignments.

## Prerequisites

1. **Python 3.11+** installed
2. **Docker** installed (for Milvus and Neo4j)
3. **OpenAI API Key**

## Setup Steps

### 1. Install Dependencies

```bash
# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# Required: OPENAI_API_KEY=sk-...
```

### 3. Start Services

```bash
# Start Milvus and Neo4j with Docker
./services.sh start

# Check service status
./services.sh status

# View logs
./services.sh logs
```

**Service URLs:**
- Milvus: `localhost:19530`
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Neo4j Browser: http://localhost:7474 (neo4j/password123)

## Assignment 1: Milvus FAQ System

### Quick Test

```bash
# Run demo mode (recommended first)
python -m milvus_faq.main --mode demo

# Interactive query mode
python -m milvus_faq.main --mode query

# Start REST API
python -m milvus_faq.main --mode api
```

### API Usage

```bash
# Query FAQ
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "如何退货？", "top_k": 3}'

# Add new FAQ (hot update)
curl -X POST "http://localhost:8000/faq" \
  -H "Content-Type: application/json" \
  -d '{
    "faq_id": "faq_016",
    "question": "如何申请价保？",
    "answer": "如果您购买的商品在7天内降价，可以申请价保..."
  }'

# Get status
curl "http://localhost:8000/status"
```

**API Docs:** http://localhost:8000/docs

### Features Implemented

✅ Vector-based semantic search with Milvus
✅ OpenAI embeddings (text-embedding-3-small)
✅ LLM answer generation (GPT-4o-mini)
✅ Semantic chunking with overlap
✅ Hot reload support (add/update/delete)
✅ FastAPI REST API
✅ Multiple query modes

## Assignment 2: Graph RAG System

### Quick Test

```bash
# Initialize system (first time only)
python -m graph_rag.main --mode init

# Run demo mode (recommended first)
python -m graph_rag.main --mode demo

# Interactive query mode
python -m graph_rag.main --mode query

# Start REST API
python -m graph_rag.main --mode api
```

### API Usage

```bash
# Query the system
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "阿里巴巴集团的最大股东是谁？",
    "include_reasoning": true
  }'

# Get company info
curl -X POST "http://localhost:8001/graph/company" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "阿里巴巴"}'

# Find shareholders
curl -X POST "http://localhost:8001/graph/shareholders" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "阿里巴巴"}'

# Get graph statistics
curl "http://localhost:8001/graph/stats"

# Get status
curl "http://localhost:8001/status"
```

**API Docs:** http://localhost:8001/docs

### Features Implemented

✅ Hybrid query engine (RAG + KG)
✅ Neo4j knowledge graph with 10 companies
✅ Multi-hop reasoning (up to 3 hops)
✅ Query classification and entity extraction
✅ Joint scoring mechanism (vector + graph)
✅ Error detection and validation
✅ Explainable reasoning paths
✅ FastAPI REST API
✅ Multiple query modes

### Sample Queries

The demo includes queries like:
- "阿里巴巴集团的最大股东是谁？" (ownership)
- "蚂蚁集团是谁投资的？" (investment)
- "阿里巴巴有哪些子公司？" (subsidiaries)
- "软银集团和阿里巴巴是什么关系？" (relationships)
- "腾讯和阿里巴巴有什么关系？" (multi-hop)

## Troubleshooting

### Services not starting

```bash
# Check Docker
docker ps

# Restart services
./services.sh restart

# Clean and restart (WARNING: deletes data)
./services.sh clean
./services.sh start
```

### Milvus connection error

```bash
# Check Milvus is running
docker ps | grep milvus

# Check port is accessible
nc -zv localhost 19530
```

### OpenAI API error

```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Python import errors

```bash
# Reinstall dependencies
uv sync --force

# Verify installation
python -c "import llama_index; print('OK')"
python -c "import pymilvus; print('OK')"
```

## Project Structure

```
week03-homework-2/
├── milvus_faq/              # Assignment 1: FAQ System
│   ├── main.py             # Entry point (4 modes)
│   ├── api.py              # REST API (port 8000)
│   ├── vector_store.py     # Milvus integration
│   ├── data_loader.py      # Data utilities
│   ├── config.py           # Configuration
│   ├── faq_data.json       # FAQ dataset (15 entries)
│   ├── test_faq.py         # Test script
│   ├── README.md           # Detailed docs
│   └── report.md           # Experiment report
├── graph_rag/              # Assignment 2: Graph RAG
│   ├── main.py            # Entry point (4 modes)
│   ├── api.py             # REST API (port 8001)
│   ├── graph_store.py     # Neo4j integration
│   ├── vector_store.py    # Document retrieval
│   ├── hybrid_query.py    # Hybrid query engine
│   ├── config.py          # Configuration
│   ├── data/              # Data directory
│   │   ├── companies.json      # 10 companies
│   │   └── relationships.json  # 12 relationships
│   ├── test_graph_rag.py  # Test script
│   ├── README.md          # Detailed docs
│   └── report.md          # Experiment report
├── data/                   # Docker volume data
│   ├── milvus/            # Milvus data
│   └── neo4j/             # Neo4j data
├── docker-compose.yml      # Service definitions
├── services.sh             # Service management script
├── .env                    # Environment config
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── QUICKSTART.md           # This file
└── pyproject.toml          # Dependencies
```

## Next Steps

1. ✅ Complete Assignment 1 setup and testing
2. ✅ Complete Assignment 2 setup and testing
3. ⬜ Write experiment reports (report.md in each folder)
4. ⬜ Submit homework

### Running Tests

```bash
# Test Assignment 1
python -m milvus_faq.test_faq

# Test Assignment 2
python -m graph_rag.test_graph_rag
```

## Getting Help

- Check `milvus_faq/README.md` for detailed documentation
- View logs: `./services.sh logs`
- Check service status: `./services.sh status`
- Review API docs: http://localhost:8000/docs

## Common Commands

```bash
# Start all services (Milvus + Neo4j)
./services.sh start

# Stop services
./services.sh stop

# View logs
./services.sh logs

# Check status
./services.sh status

# === Assignment 1: Milvus FAQ ===
# Run FAQ demo
python -m milvus_faq.main --mode demo

# Interactive FAQ query
python -m milvus_faq.main --mode query

# Start FAQ API server
python -m milvus_faq.main --mode api

# Test FAQ implementation
python -m milvus_faq.test_faq

# === Assignment 2: Graph RAG ===
# Initialize Graph RAG (first time)
python -m graph_rag.main --mode init

# Run Graph RAG demo
python -m graph_rag.main --mode demo

# Interactive Graph RAG query
python -m graph_rag.main --mode query

# Start Graph RAG API server
python -m graph_rag.main --mode api

# Test Graph RAG implementation
python -m graph_rag.test_graph_rag
```

Good luck with your homework! 🚀
