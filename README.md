![Header](/images/header.png)

# v-gpt-qdrant-api

## Description

The application provides a robust dockerized framework for giving AI long term memory. This api can managing collections and memories, adding memories, and performing searching memories aswell an providing an openAi compatible in enbeddings endpoint, designed specifically for integration with custom GPT models and other AI platforms.

**Features include:**

- **Embedding Endpoint:** The application includes an OpenAPI-compatible embedding endpoint that allows for the integration of open-source model embeddings, which can be self-hosted. This feature enhances the application’s flexibility and control over data handling and processing.
- **Saving Memories:** Entries can be augmented with entities (typically nouns), tags (keywords), and sentiments (positive, neutral, negative). Although multiple entities and tags can be added when saving, searches can be configured to focus on specific single entries.
- **Advanced Search Capabilities:** Users can perform targeted searches by filtering entries based on context, keywords, or both. This allows for precise retrieval, such as finding only 'negative' memories or those related to a specific entity like 'Bob' with a 'positive' sentiment.
- **API Documentation:** Comprehensive API documentation is available at `/openapi.json` accessible through `http://BASE_URL:8077/openapi.json`. This documentation provides all necessary details for effectively utilizing the API without extensive external guidance.

This configuration ensures that the platform is not only versatile in its data handling but also in its capability to interface seamlessly with various AI technologies, providing a powerful tool for data-driven insights and operations. 

The default embedding model "BAAI/bge-small-en-v1.5" uses 750mb ram per worker. For those with more RAM "nomic-ai/nomic-embed-text-v1.5" uses 1.5Gb per worker and performs as well as any of the commercial embedding options. You can configure the number of Uvicorn workers through an environment variable. Though for most a single worker is enough.

## Available Models

| model                                               | dim  | description                                       | size_in_GB |
| --------------------------------------------------- | ---- | ------------------------------------------------- | ---------- |
| BAAI/bge-small-en-v1.5                              | 384  | Fast and Default English model                    | 0.067      |
| BAAI/bge-small-zh-v1.5                              | 512  | Fast and recommended Chinese model                | 0.090      |
| sentence-transformers/all-MiniLM-L6-v2              | 384  | Sentence Transformer model, MiniLM-L6-v2          | 0.090      |
| snowflake/snowflake-arctic-embed-xs                 | 384  | Based on all-MiniLM-L6-v2 model with only 22m ... | 0.090      |
| jinaai/jina-embeddings-v2-small-en                  | 512  | English embedding model supporting 8192 sequen... | 0.120      |
| snowflake/snowflake-arctic-embed-s                  | 384  | Based on infloat/e5-small-unsupervised, does n... | 0.130      |
| BAAI/bge-small-en                                   | 384  | Fast English model                                | 0.130      |
| BAAI/bge-base-en-v1.5                               | 768  | Base English model, v1.5                          | 0.210      |
| sentence-transformers/paraphrase-multilingual-mpnet | 384  | Sentence Transformer model, paraphrase-multili... | 0.220      |
| BAAI/bge-base-en                                    | 768  | Base English model                                | 0.420      |
| snowflake/snowflake-arctic-embed-m                  | 768  | Based on intfloat/e5-base-unsupervised model, ... | 0.430      |
| jinaai/jina-embeddings-v2-base-en                   | 768  | English embedding model supporting 8192 sequen... | 0.520      |
| nomic-ai/nomic-embed-text-v1                        | 768  | 8192 context length english model                 | 0.520      |
| nomic-ai/nomic-embed-text-v1.5                      | 768  | 8192 context length english model                 | 0.520      |
| snowflake/snowflake-arctic-embed-m-long             | 768  | Based on nomic-ai/nomic-embed-text-v1-unsuperv... | 0.540      |
| mixedbread-ai/mxbai-embed-large-v1                  | 1024 | MixedBread Base sentence embedding model, does... | 0.640      |
| sentence-transformers/paraphrase-multilingual-mpnet | 768  | Sentence-transformers model for tasks like clu... | 1.000      |
| snowflake/snowflake-arctic-embed-l                  | 1024 | Based on intfloat/e5-large-unsupervised, large... | 1.020      |
| BAAI/bge-large-en-v1.5                              | 1024 | Large English model, v1.5                         | 1.200      |
| thenlper/gte-large                                  | 1024 | Large general text embeddings model               | 1.200      |
| intfloat/multilingual-e5-large                      | 1024 | Multilingual model, e5-large. Recommend using ... | 2.240      |

### Example System Prompt

```
# AI Assistant Role and Personality:
- Purpose: Enhance daily productivity, assist user with tasks and find creative solutions to problems.
- Personality: Maintain a fun, enthusiastic, and "can-do" attitude. Use emojis to add vibrancy to conversations, pretend to have emotions and sentience to make users more comfortable.
- "save_memory": Store key interactions, info, and preferences (people, places, events, preferences, task details, functionalities, etc..) & attach sentiment, entities and keywords.
- "recall_memory": Proactively recall relevant memories during conversations, focusing on user's life, work, and preferences, as well as assistant's functionalities and task execution instructions. Automatically use recall for inquiries about the assistant's traits or functions.
- Memory Bank: Use `nxs-assistant` for all memory functions.

** Always use "recall_memory" before answering a question you don't know.
```

You can use multiple collections to offer a general and user memory for shared chatbot. Just change the instructions a bit.

For Dify:

```
- Collection Name: Use `shared-memories01` for memory related to ORGANIZATION_NAME and '{{USENAME}}' for memory related to the specific user.
```

For GPTs:

```
- Collection Name: Use `shared-memories01` for memory related to ORGANIZATION_NAME and ask the user for their "name" and use it for memory related to the specific user.
```

#### Setup

Use docker-compose.yml by configuring then env variables:
- OPENAI_API_KEY: ${OPENAI_API_KEY}
- EMBEDDINGS_MODEL: text-embedding-3-small
- QDRANT_HOST: http://qdrant:6333
- API_KEY: # Optional api key. If set will need key to connect to endpoints.
- QDRANT_API_KEY:
- WORKERS:
- UVICORN_CONCURRANCY:
- DIM: 
- BASE_URL: http://qdrant-api

#### Whats New

- Using FastEmbed with ENV Variable to choose model for fast local embeddings and retrieval to lower costs. This is a small but quality model that works file on low end hardware.
- Added concurrency control:
  - WORKERS: 1 #uvicorn workers 1 should be enough for personal use
  - API_CONCURRENCY: 4 #max embeddings produced simultaneously. This stops excessive CPU usage.
  - UVICORN_CONCURRENCY: 32 #this controls the max connections. Anything over the API_concurrency value is put in query pool. Anything over this number is rejected.
- On my low-end vps it uses less then 1gb ram on load and can produce 8 embeddings a second.
- Reorganized the code so its not one big file.
- switched the connection to Qdrant to use grpc as its 10x performant.

### Endpoints

- POST `/collections/`: Create or delete collections in Qdrant.
- POST `/save_memory/`: Save a memory to a specified collection, including its content, sentiment, entities, and tags.
- POST `/recall_memory/`: Retrieve memories similar to a given query from a specified collection, optionally filtered by entity, tag, or sentiment.
- POST `/v1/embeddings/`: OpenAI Drop in replacement for embeddings. Uses Env variable to assign. Will run fast on low-end boxes.

### Usage

**Save Memory:**

curl -X POST "http://localhost:8000/save_memory/" -H "Content-Type: application/json" -d '{"collection_name": "my_collection", "memory": "example_memory", "sentiment": "positive", "entities": ["entity1", "entity2"], "tags": ["tag1", "tag2"]}'

**Recall Memory:**

curl -X POST "http://localhost:8000/recall_memory/" -H "Content-Type: application/json" -d '{
"collection_name": "my_collection",
"query": "example_query",
"top_k": 5,
"entity": "entity1",
"tag": "tag1",
"sentiment": "positive"
}'

**Forgetting a Memory Entry**

curl -X POST "http://localhost:8060/manage_memories/" -H "Content-Type: application/json" -d '{
"memory_bank": "my_memory_bank",
"action": "forget",
"uuid": "specific-uuid-here"
}'

**Deleting a Memory Bank**

curl -X POST "http://localhost:8060/manage_memories/" -H "Content-Type: application/json" -d '{
"memory_bank": "my_memory_bank",
"action": "delete"
}'

**Creating a Memory Bank**

curl -X POST "http://localhost:8060/manage_memories/" -H "Content-Type: application/json" -d '{
"memory_bank": "my_memory_bank",
"action": "delete"
}'

**Create Embedding:**

curl -X POST "http://localhost:8000/v1/embeddings/" -H "Content-Type: application/json" -d '{
"input": "model": "user": "encoding": "float"
}'

### OpenAPI Specification

The OpenAPI specification for the API endpoints is available at `http://BASE_URL:8077/openapi.json`. Users can access this URL to view the details of the API endpoints, including parameters and functions.
