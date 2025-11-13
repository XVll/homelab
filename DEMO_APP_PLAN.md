# Demo AI App - Development Plan

## App: "SmartDocs AI" - Testing All Infrastructure & AI Libraries

**Goal**: Simple document chat app demonstrating ALL AI libraries, infrastructure services, and modern TypeScript patterns. Focus on testing integrations, not building a production-ready product.

---

## Tech Stack

### Frontend
- **Next.js 15** (App Router, React Server Components)
- **Tailwind CSS** + **shadcn/ui**
- **TypeScript**

### Backend
- **Bun** (Runtime)
- **Hono** (API Framework)
- **Drizzle ORM** (Database)
- **TypeScript**

### AI Libraries (TypeScript)
- **LangChain.js** - RAG pipelines, chains, agents
- **LangGraph.js** - Stateful workflows
- **LlamaIndex.TS** - Advanced retrieval
- **Vercel AI SDK** - Streaming, structured outputs
- **Inngest** - Durable workflows
- **Langfuse SDK** - AI observability
- **Zep** - Conversation memory (TypeScript alternative to Mem0)

### Python Microservices
- **FastAPI** - API framework
- **LiteLLM Proxy** - Model gateway (standalone server)
- **Docling** - Document processing service
- **Mem0 API** - Memory service (if needed alongside Zep)

### Infrastructure
- All existing homelab services (PostgreSQL, MongoDB, Redis, MinIO, Qdrant, ClickHouse, RabbitMQ, Kafka, Mosquitto, Meilisearch)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js 15 Frontend                          │
│                   (React Server Components)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │ Traefik │ (Reverse Proxy + SSL)
                    └────┬────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│              Hono + Bun API (TypeScript)                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Routes: /upload, /chat, /search, /analyze, /test/*       │  │
│  │                                                            │  │
│  │  AI Components:                                            │  │
│  │  - LangChain.js RAG chains                                │  │
│  │  - LangGraph.js workflows                                 │  │
│  │  - LlamaIndex.TS retrieval                                │  │
│  │  - Vercel AI SDK structured outputs                       │  │
│  │  - Zep memory management                                  │  │
│  │  - Inngest durable functions                              │  │
│  │  - Langfuse observability                                 │  │
│  └────────────────────────────────────────────────────────────┘  │
└──┬────┬────┬────┬────┬────┬────┬────┬────┬────┬──────────────┘
   │    │    │    │    │    │    │    │    │    │
   ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Python Microservices                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  - LiteLLM Proxy (model gateway)                          │  │
│  │  - Docling Service (document processing)                  │  │
│  │  - Mem0 API (memory service)                              │  │
│  └────────────────────────────────────────────────────────────┘  │
└──┬────┬────┬────┬────┬────┬────┬────┬────┬────┬──────────────┘
   │    │    │    │    │    │    │    │    │    │
   ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Infrastructure Services                        │
│                                                                  │
│  AI Stack (10.10.10.115):                                       │
│  - LiteLLM Proxy → Model gateway                                │
│  - Docling Service → Document parsing                           │
│  - Mem0 API → Memory management                                 │
│  - n8n → Workflow automation                                    │
│                                                                  │
│  Database Stack (10.10.10.111):                                 │
│  - PostgreSQL → Users, sessions, metadata (Drizzle)             │
│  - MongoDB → Document chunks, raw data                          │
│  - Redis → Cache, rate limiting, pub/sub                        │
│  - Qdrant → Vector embeddings                                   │
│  - MinIO → File storage                                         │
│  - ClickHouse → Analytics, metrics                              │
│  - RabbitMQ → Task queue                                        │
│  - Kafka → Event streaming                                      │
│  - Mosquitto → MQTT real-time                                   │
│                                                                  │
│  Dev Stack (10.10.10.114):                                      │
│  - Meilisearch → Full-text search                               │
│  - Inngest → Workflow execution                                 │
│  - Gitea → Git + CI/CD + Registry                               │
│                                                                  │
│  Observability (10.10.10.112):                                  │
│  - Langfuse → AI observability                                  │
│  - Grafana → Dashboards                                         │
│  - Loki → Logs                                                  │
│  - Tempo → Traces                                               │
│  - Alloy → Metrics collection                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Examples

### Document Upload Flow
```
User uploads PDF
  │
  ▼
Next.js → Traefik → Hono API
  │
  ├─▶ MinIO (store file)
  ├─▶ PostgreSQL (metadata) via Drizzle
  └─▶ Inngest (trigger processing workflow)
  │
  ▼
Inngest Workflow:
  ├─▶ Docling Service (parse PDF)
  ├─▶ LangChain.js (chunk text)
  ├─▶ LiteLLM Proxy (generate embeddings)
  ├─▶ Qdrant (store vectors)
  ├─▶ Meilisearch (full-text index)
  ├─▶ MongoDB (store chunks)
  └─▶ Kafka (publish event)
  │
  ▼
MQTT notification → Real-time UI update
Langfuse → Track all AI operations
ClickHouse → Log metrics
```

### Chat Query Flow
```
User sends message
  │
  ▼
Next.js → Traefik → Hono API
  │
  ├─▶ Redis (check rate limit)
  ├─▶ Zep (get conversation memory)
  └─▶ PostgreSQL (fetch history) via Drizzle
  │
  ▼
LangGraph.js Workflow:
  ├─▶ Node 1: Classify query (Vercel AI SDK)
  ├─▶ Node 2: Retrieve docs (LlamaIndex.TS)
  │     ├─▶ Qdrant (semantic search)
  │     └─▶ Meilisearch (keyword search)
  ├─▶ Node 3: Build context (LangChain.js)
  ├─▶ Node 4: Generate answer (LiteLLM via Vercel AI SDK)
  └─▶ Node 5: Update memory (Zep)
  │
  ▼
Stream response to user (Vercel AI SDK)
Save to PostgreSQL (Drizzle)
Publish to Kafka (analytics)
Log to Langfuse (observability)
Store metrics in ClickHouse
```

---

## AI Libraries - Usage Scenarios

### LangChain.js
| Feature | Use Case |
|---------|----------|
| Prompt Templates | Reusable chat prompts |
| RAG Chain | Document Q&A pipeline |
| Memory | Conversation history |
| Document Loaders | Load PDFs, text files |
| Text Splitters | Chunk documents |
| Output Parsers | Parse LLM responses |
| Chains (LCEL) | Compose operations |
| Agents | Tool-using AI |
| Retrievers | Search documents |
| Callbacks | Trace execution with Langfuse |

### LangGraph.js
| Feature | Use Case |
|---------|----------|
| State Graphs | Multi-step workflows |
| Nodes | Processing steps |
| Edges | Flow control |
| Conditional Edges | Dynamic routing based on state |
| Cycles | Iterative refinement loops |
| Human-in-Loop | Approval/review steps |
| Persistence | Resume workflows with checkpoints |
| Parallel Execution | Concurrent node processing |
| Subgraphs | Nested workflow composition |

### LlamaIndex.TS
| Feature | Use Case |
|---------|----------|
| Vector Store Index | Qdrant integration |
| Query Engine | Semantic search |
| Chat Engine | Conversational retrieval |
| Retrievers | Custom retrieval strategies |
| Node Parsers | Document chunking |
| Response Synthesizer | Combine retrieved chunks |
| Query Transformations | Rewrite/expand queries |
| Reranking | Score and reorder results |
| Router Query Engine | Route to multiple indexes |
| Sub Question Engine | Decompose complex queries |

### Vercel AI SDK
| Feature | Use Case |
|---------|----------|
| Streaming | Stream LLM responses |
| Structured Outputs | Type-safe responses with Zod |
| Tool Calling | Function calling support |
| AI & UI State | Manage conversation state |
| Route Handlers | Next.js API routes |
| Model Adapters | Multi-provider support |
| Embeddings | Generate vectors |
| Multi-modal | Images + text |

### Inngest
| Feature | Use Case |
|---------|----------|
| Durable Functions | Reliable background jobs |
| Step Functions | Multi-step with auto-retry |
| Sleep/Wait | Delayed execution |
| Parallel Steps | Concurrent task execution |
| Event Triggers | React to events |
| Scheduled Functions | Cron jobs |
| Retries | Exponential backoff |
| Cancellation | Stop running workflows |
| Webhooks | External triggers |

### Zep (Memory)
| Feature | Use Case |
|---------|----------|
| Session Memory | Store conversation history |
| Fact Extraction | Auto-extract key facts |
| Search Memory | Query past conversations |
| Summary Memory | Automatic summarization |
| User Scoping | Per-user memory isolation |
| Metadata | Tag memories with context |
| Vector Search | Semantic memory retrieval |
| Memory History | Track changes over time |

### Langfuse
| Feature | Use Case |
|---------|----------|
| Trace LLM Calls | Monitor all AI requests |
| Trace Chains | Full pipeline visibility |
| Cost Tracking | Token usage & costs |
| Latency Tracking | Performance monitoring |
| User Tracking | Per-user metrics |
| Session Tracking | Conversation analytics |
| Generations | Individual LLM calls |
| Spans | Custom operation tracking |
| Scores | Quality ratings |
| Tags | Categorize traces |
| Dashboards | Analytics UI |

### LiteLLM Proxy (Python)
| Feature | Use Case |
|---------|----------|
| Unified API | Single interface for all models |
| Streaming | Stream responses |
| Embeddings | Generate vectors |
| Fallbacks | Auto-fallback to backup models |
| Load Balancing | Distribute requests |
| Cost Tracking | Token usage monitoring |
| Caching | Redis-backed cache |
| Rate Limiting | Throttle requests |
| Virtual Keys | API key management |

### Docling Service (Python)
| Feature | Use Case |
|---------|----------|
| PDF Parsing | Extract text from PDFs |
| Table Extraction | Parse tables to structured data |
| Image Extraction | Extract embedded images |
| Markdown Export | Convert to markdown |
| Structure Recognition | Identify headings, sections |
| OCR | Process scanned documents |
| Batch Processing | Handle multiple files |
| Multi-format | DOCX, PPTX, HTML support |

---

## Infrastructure Services - Usage Scenarios

### PostgreSQL (Drizzle)
- User accounts & authentication
- Chat sessions & messages
- Document metadata
- API keys & access tokens
- Full-text search (tsvector)
- Complex relations

### MongoDB
- Document chunks (processed text)
- Raw extracted content
- User annotations
- Time-series collections
- GridFS for large files
- Flexible schema data

### Redis
- Session caching
- Rate limiting (token bucket)
- Query result cache
- Embedding cache
- Pub/Sub messaging
- Sorted sets (leaderboards)
- Bloom filters

### MinIO (S3)
- Uploaded files
- Processed documents
- Generated content
- Backups
- Object versioning
- Lifecycle policies

### Qdrant
- Document embeddings
- Query history embeddings
- Hybrid search (dense + sparse)
- Metadata filtering
- Scalar quantization
- Batch operations

### ClickHouse
- LLM call logs (tokens, costs)
- User event analytics
- Search query logs
- API request logs
- Performance metrics
- Materialized views
- TTL policies

### RabbitMQ
- Document processing queue
- Embedding generation queue
- Notification queue
- Dead letter queue
- Priority queues
- Delayed messages

### Kafka
- User action events
- Document lifecycle events
- LLM operation events
- Analytics pipeline
- Log compaction
- Consumer groups
- Partitioning

### Mosquitto (MQTT)
- Real-time chat updates
- Document processing status
- User presence
- Push notifications
- QoS levels (0, 1, 2)
- Retained messages
- Wildcard subscriptions

### Meilisearch
- Full-text document search
- Faceted search
- Typo tolerance
- Instant search
- Synonyms
- Custom ranking
- Geo search

---

## Development Phases

### Phase 0: Project Setup
**Goal**: Initialize monorepo and configure tooling

**Tasks**:
- Create monorepo structure (apps/backend, apps/frontend)
- Setup Bun workspace
- Initialize Next.js 15 app
- Initialize Hono API project
- Setup Drizzle with PostgreSQL
- Configure TypeScript
- Setup ESLint, Prettier
- Create Docker Compose for local services
- Test connections to all infrastructure
- Initialize Gitea repository

**Deliverable**: Clean project skeleton with working connections

---

### Phase 1: Database Layer
**Goal**: Setup schemas and test all database services

**Tasks**:
- Define Drizzle schemas (users, sessions, messages, documents)
- Create migrations
- Setup MongoDB collections
- Configure Redis clients (cache, pub/sub)
- Initialize Qdrant collections
- Setup MinIO buckets with policies
- Create ClickHouse tables with TTL
- Configure RabbitMQ queues
- Create Kafka topics
- Setup MQTT client
- Initialize Meilisearch indexes

**Test Endpoints**:
- `POST /test/postgres` - CRUD + full-text search
- `POST /test/mongodb` - Insert, GridFS, time-series
- `POST /test/redis` - Cache, pub/sub, bloom filter
- `POST /test/minio` - Upload, versioning
- `POST /test/qdrant` - Vector insert, search, filter
- `POST /test/clickhouse` - Insert event, query materialized view
- `POST /test/rabbitmq` - Publish, consume, DLQ
- `POST /test/kafka` - Produce, consume, compaction
- `POST /test/mqtt` - Publish with QoS levels
- `POST /test/meilisearch` - Index, search with typos

**Deliverable**: All databases connected with test endpoints working

---

### Phase 2: Python Microservices
**Goal**: Deploy supporting Python services

**Tasks**:
- Deploy LiteLLM Proxy (standalone server)
- Create Docling FastAPI service
- Create Mem0 FastAPI service (optional)
- Configure health checks
- Add to Traefik routing
- Test from Hono backend

**Test Endpoints**:
- `POST /test/litellm` - Completion, streaming, embeddings
- `POST /test/docling` - Parse PDF, extract tables/images
- `POST /test/mem0` - Add memory, search

**Deliverable**: Python services running and accessible from Hono

---

### Phase 3: AI Foundation - LiteLLM & Langfuse
**Goal**: Setup model gateway and observability

**Tasks**:
- Configure LiteLLM client in Hono
- Setup Langfuse SDK
- Test completions with tracing
- Test streaming responses
- Test embeddings generation
- Configure model fallbacks
- Setup Redis caching for LiteLLM
- Test cost tracking

**Test Endpoints**:
- `POST /ai/complete` - Basic completion
- `POST /ai/stream` - Streaming response
- `POST /ai/embed` - Generate embeddings
- `GET /ai/metrics` - View Langfuse traces

**Deliverable**: AI calls working with full observability

---

### Phase 4: Document Processing - Docling & Storage
**Goal**: Upload and process documents

**Tasks**:
- Create upload endpoint (Hono)
- Store files in MinIO
- Call Docling service for parsing
- Store results in MongoDB
- Save metadata in PostgreSQL (Drizzle)
- Publish events to Kafka
- Send MQTT status updates

**Endpoints**:
- `POST /upload` - Upload file
- `GET /documents` - List documents
- `GET /documents/:id` - Get document details

**Deliverable**: Document upload and processing pipeline

---

### Phase 5: Vector Search - Embeddings & Qdrant
**Goal**: Enable semantic search

**Tasks**:
- Chunk documents with LangChain.js
- Generate embeddings via LiteLLM
- Store in Qdrant with metadata
- Index in Meilisearch for keyword search
- Cache embeddings in Redis
- Implement hybrid search (semantic + keyword)

**Endpoints**:
- `POST /search/semantic` - Vector search
- `POST /search/keyword` - Full-text search
- `POST /search/hybrid` - Combined search

**Deliverable**: Semantic and hybrid search working

---

### Phase 6: RAG Pipeline - LangChain.js
**Goal**: Implement retrieval-augmented generation

**Tasks**:
- Create LangChain.js RAG chain
- Setup prompt templates
- Integrate Qdrant retriever
- Add conversation memory
- Implement streaming responses
- Create agents with tools
- Add output parsers

**Endpoints**:
- `POST /chat` - Chat with RAG
- `POST /chat/stream` - Streaming chat
- `GET /chat/history/:sessionId` - Chat history

**Deliverable**: Working RAG chat with memory

---

### Phase 7: Advanced Workflows - LangGraph.js
**Goal**: Multi-step AI workflows

**Tasks**:
- Build query classification workflow
- Create document analysis workflow
- Implement conditional routing
- Add human-in-loop approval
- Setup workflow persistence
- Create parallel execution examples
- Build nested subgraphs

**Endpoints**:
- `POST /analyze` - Run analysis workflow
- `POST /workflows/:id/approve` - Human approval
- `GET /workflows/:id/status` - Workflow status

**Deliverable**: Complex multi-step workflows

---

### Phase 8: Advanced Retrieval - LlamaIndex.TS
**Goal**: Enhanced retrieval strategies

**Tasks**:
- Setup LlamaIndex.TS with Qdrant
- Implement query engine
- Add chat engine
- Configure reranking
- Setup router query engine
- Implement sub-question engine
- Add metadata filtering

**Endpoints**:
- `POST /search/advanced` - Advanced retrieval
- `POST /search/rerank` - Reranked results
- `POST /search/route` - Multi-index routing

**Deliverable**: Advanced retrieval patterns

---

### Phase 9: Structured Outputs - Vercel AI SDK
**Goal**: Type-safe AI responses

**Tasks**:
- Setup Vercel AI SDK
- Create Zod schemas for outputs
- Implement structured chat responses
- Add tool calling
- Setup streaming with structure
- Integrate with Next.js RSC
- Create AI & UI state management

**Endpoints**:
- `POST /ai/structured` - Structured output
- `POST /ai/extract` - Data extraction
- `POST /ai/classify` - Query classification

**Deliverable**: Type-safe structured outputs

---

### Phase 10: Memory - Zep
**Goal**: Conversation memory management

**Tasks**:
- Setup Zep client
- Implement session memory
- Add fact extraction
- Enable memory search
- Integrate with RAG pipeline
- Add memory summaries
- Test user scoping

**Endpoints**:
- `POST /memory/add` - Store memory
- `GET /memory/search` - Search memories
- `GET /memory/session/:id` - Session memory

**Deliverable**: Persistent conversation memory

---

### Phase 11: Durable Workflows - Inngest
**Goal**: Background job processing

**Tasks**:
- Setup Inngest client
- Create document processing function
- Add scheduled jobs (cron)
- Implement retry logic
- Create parallel step execution
- Add event-driven triggers
- Setup cancellation
- Create fan-out pattern

**Endpoints**:
- `POST /jobs/trigger` - Trigger workflow
- `GET /jobs/:id/status` - Job status
- `POST /jobs/:id/cancel` - Cancel job

**Deliverable**: Durable background workflows

---

### Phase 12: Frontend - Next.js
**Goal**: Build user interface

**Tasks**:
- Create chat interface
- Add document upload UI
- Implement real-time updates (MQTT)
- Add streaming response display
- Create document library
- Build analytics dashboard
- Add admin test panel

**Pages**:
- `/` - Chat interface
- `/upload` - Document upload
- `/docs` - Document library
- `/analytics` - Usage dashboard
- `/admin` - Test all features

**Deliverable**: Full frontend with real-time features

---

### Phase 13: Observability & Analytics
**Goal**: Comprehensive monitoring

**Tasks**:
- Create Grafana dashboards
- Configure Loki for logs
- Setup Tempo for traces
- Create ClickHouse analytics queries
- Build Langfuse dashboards
- Setup alerts
- Create performance metrics

**Dashboards**:
- LLM metrics (cost, latency, tokens)
- System metrics (CPU, memory, requests)
- Business metrics (users, documents, queries)
- Error tracking

**Deliverable**: Full observability stack

---

### Phase 14: CI/CD - Gitea
**Goal**: Automated deployment

**Tasks**:
- Create Gitea Actions workflow
- Add test stage (Bun test)
- Add build stage (Docker images)
- Push to Gitea registry
- Deploy to dev VM
- Add health checks
- Setup rollback strategy

**Workflow**:
- Test → Build → Push → Deploy

**Deliverable**: Automated CI/CD pipeline

---

## Testing Checklist

### Infrastructure (10 services)
- [ ] PostgreSQL - All features tested
- [ ] MongoDB - All features tested
- [ ] Redis - All features tested
- [ ] MinIO - All features tested
- [ ] Qdrant - All features tested
- [ ] ClickHouse - All features tested
- [ ] RabbitMQ - All features tested
- [ ] Kafka - All features tested
- [ ] Mosquitto - All features tested
- [ ] Meilisearch - All features tested

### AI Libraries (9 libraries)
- [ ] LangChain.js - All patterns tested
- [ ] LangGraph.js - All patterns tested
- [ ] LlamaIndex.TS - All patterns tested
- [ ] Vercel AI SDK - All patterns tested
- [ ] Inngest - All patterns tested
- [ ] Zep - All patterns tested
- [ ] Langfuse - All traces working
- [ ] LiteLLM - All endpoints tested
- [ ] Docling - All formats tested

### Application
- [ ] Document upload working
- [ ] Chat with RAG working
- [ ] Streaming responses working
- [ ] Real-time updates (MQTT) working
- [ ] Memory persistence working
- [ ] Search (semantic + keyword) working
- [ ] Background jobs working
- [ ] Observability dashboards populated

---

## Project Structure

```
smartdocs/
├── apps/
│   ├── backend/              # Hono + Bun API
│   │   ├── src/
│   │   │   ├── routes/       # API routes
│   │   │   ├── ai/           # AI library integrations
│   │   │   │   ├── langchain.ts
│   │   │   │   ├── langgraph.ts
│   │   │   │   ├── llamaindex.ts
│   │   │   │   ├── vercel-ai.ts
│   │   │   │   ├── zep.ts
│   │   │   │   └── langfuse.ts
│   │   │   ├── db/           # Database clients
│   │   │   │   ├── drizzle/  # Drizzle schemas
│   │   │   │   ├── mongo.ts
│   │   │   │   ├── redis.ts
│   │   │   │   ├── qdrant.ts
│   │   │   │   └── ...
│   │   │   ├── services/     # Business logic
│   │   │   ├── inngest/      # Inngest functions
│   │   │   └── index.ts      # Entry point
│   │   ├── drizzle.config.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── frontend/             # Next.js 15
│       ├── app/              # App router
│       │   ├── page.tsx      # Chat interface
│       │   ├── upload/
│       │   ├── docs/
│       │   └── analytics/
│       ├── components/
│       ├── lib/
│       ├── package.json
│       └── tsconfig.json
│
├── services/                 # Python microservices
│   ├── docling/
│   │   ├── main.py           # FastAPI app
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── mem0/
│       ├── main.py
│       ├── Dockerfile
│       └── requirements.txt
│
├── docker-compose.yml        # Local development
├── .env                      # 1Password references
├── package.json              # Root workspace
├── bun.lockb
└── README.md
```

---

## Deployment Strategy

**Development**:
- Local: Bun run (backend) + Next.js dev server
- Docker Compose for Python services

**Production (dev VM)**:
- Deploy via Gitea Actions
- Build Docker images
- Push to Gitea registry
- Deploy with docker compose
- Traefik routing with private-default middleware

**Domains**:
- `smartdocs.onurx.com` → Frontend
- `api.smartdocs.onurx.com` → Hono API
- `docling.smartdocs.onurx.com` → Docling service
- `litellm.smartdocs.onurx.com` → LiteLLM proxy

---

## Summary

- **Modern Stack**: Bun + Hono + Drizzle + Next.js 15
- **9 AI Libraries**: All with TypeScript support
- **10 Infrastructure Services**: Complete testing coverage
- **14 Phases**: Incremental development
- **Hybrid Approach**: TypeScript primary, Python microservices where needed
- **Full Observability**: Langfuse + Grafana + Loki + Tempo
- **Automated CI/CD**: Gitea Actions

**Ready to start with Phase 0?**
