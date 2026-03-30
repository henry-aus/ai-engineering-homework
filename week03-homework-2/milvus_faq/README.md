# Milvus FAQ Retrieval System

A production-ready FAQ retrieval system powered by Milvus vector database and LlamaIndex.

## Features

✅ **Vector-based semantic search** using Milvus
✅ **LLM-powered answer generation** with OpenAI GPT-4
✅ **Hot reload support** - add/update/delete FAQs without restart
✅ **RESTful API** with FastAPI
✅ **Semantic chunking** with overlap for better retrieval
✅ **Multiple query modes** - CLI, API, and demo

## Architecture

```
User Query
    ↓
OpenAI Embedding (text-embedding-3-small)
    ↓
Milvus Vector Search (similarity search)
    ↓
Retrieved Top-K FAQs
    ↓
OpenAI LLM (GPT-4o-mini) - Answer Synthesis
    ↓
Final Answer + Sources
```

## Prerequisites

1. **Start Milvus service:**
   ```bash
   cd ..
   ./services.sh start
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Usage

### 1. Interactive Query Mode (Default)

```bash
python -m milvus_faq.main
```

Interactive CLI for querying the FAQ system.

### 2. Demo Mode

```bash
python -m milvus_faq.main --mode demo
```

Runs predefined demo queries to showcase the system.

### 3. API Mode

```bash
python -m milvus_faq.main --mode api
```

Starts FastAPI server at http://localhost:8000

**API Endpoints:**
- `GET /` - API information
- `POST /query` - Query FAQ system
- `POST /faq` - Add new FAQ (hot update)
- `PUT /faq/{faq_id}` - Update FAQ (hot update)
- `DELETE /faq/{faq_id}` - Delete FAQ (hot update)
- `POST /reload` - Reload index from file
- `GET /status` - System status
- `GET /health` - Health check

**API Documentation:** http://localhost:8000/docs

### 4. Build Index Mode

```bash
python -m milvus_faq.main --mode build
```

Builds or rebuilds the vector index from scratch.

## API Examples

### Query FAQ
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "如何退货？",
    "top_k": 3
  }'
```

### Add New FAQ (Hot Update)
```bash
curl -X POST "http://localhost:8000/faq" \
  -H "Content-Type: application/json" \
  -d '{
    "faq_id": "faq_016",
    "question": "如何申请价保？",
    "answer": "如果您购买的商品在7天内降价，可以申请价保..."
  }'
```

### Update FAQ (Hot Update)
```bash
curl -X PUT "http://localhost:8000/faq/faq_001" \
  -H "Content-Type: application/json" \
  -d '{
    "faq_id": "faq_001",
    "question": "如何退货？",
    "answer": "更新后的退货说明..."
  }'
```

### Delete FAQ (Hot Update)
```bash
curl -X DELETE "http://localhost:8000/faq/faq_001"
```

### Get System Status
```bash
curl "http://localhost:8000/status"
```

## Configuration

Edit `config.py` or set environment variables:

```python
# OpenAI
OPENAI_API_KEY = "your-key"
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# Milvus
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
MILVUS_COLLECTION_NAME = "faq_collection"

# Chunking
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Retrieval
TOP_K = 3
SIMILARITY_THRESHOLD = 0.7
```

## Project Structure

```
milvus_faq/
├── __init__.py           # Package initializer
├── main.py              # Main entry point
├── config.py            # Configuration settings
├── vector_store.py      # Milvus vector store
├── data_loader.py       # FAQ data loader
├── api.py               # FastAPI REST API
├── faq_data.json        # FAQ dataset
├── README.md            # This file
└── report.md            # Experiment report
```

## Technical Details

### Document Chunking
- **Strategy:** Semantic sentence splitting
- **Chunk Size:** 512 tokens
- **Overlap:** 50 tokens
- Preserves context across chunks for better retrieval

### Vector Search
- **Embedding Model:** OpenAI text-embedding-3-small (1536 dimensions)
- **Vector DB:** Milvus standalone
- **Similarity Metric:** Cosine similarity
- **Top-K Retrieval:** Configurable (default: 3)

### Answer Generation
- **LLM:** GPT-4o-mini
- **Response Mode:** Tree summarize
- Combines multiple retrieved contexts for comprehensive answers

### Hot Reload
All index operations support hot updates:
- ✅ Add new FAQ entries
- ✅ Update existing entries
- ✅ Delete entries
- ✅ Full index rebuild
- No service restart required

## Performance

- **Query Latency:** < 2s (including LLM generation)
- **Embedding:** ~100ms
- **Vector Search:** ~50ms
- **LLM Generation:** ~1-2s

## Troubleshooting

### Milvus Connection Error
```bash
# Check if Milvus is running
docker ps | grep milvus

# Restart services
./services.sh restart
```

### Index Not Found
```bash
# Build index manually
python -m milvus_faq.main --mode build
```

### OpenAI API Error
```bash
# Check if API key is set
echo $OPENAI_API_KEY

# Test API connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## License

Part of AI Engineer Training Homework - Week 3
