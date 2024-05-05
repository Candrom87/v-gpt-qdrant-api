![Header](/images/header.png)

# v-gpt-qdrant-api

## Description

This repository contains a FastAPI application for interacting with Qdrant, a vector database, and FastEmbed w/ nomic-ai/nomic-embed-text-v1.5 for embeddings. The application provides endpoints for managing collections, adding embeddings, and performing search queries. Openapi spec at /openapi.json. This is meant for use with custom GPTs or other AI platforms. It can be used to store conversation history (marked AI or User). It can also store custom (Info) entries. Each entry can be marked with metadata. Context: ai, user or info. Keywords: one or more comma separated words that tag entry. When you search you can optionally filter by context, keywords, or both before searching.

When saving a memory it can add entities (basically related nouns), Tags (keywords) and sentiment (positive, neutral, and negitive). Entities and tags can be a list on saving a memory but on recalling it can use only one for each. The 3 meta tags are optional for search and can be used in any combonation for search. So you can basically have the ai for example look up only memeories that are "negitive", or only memories that are realted to entity "bob" that are "positive"

## Example System Prompt
~~~
# AI Assistant Role and Personality:
- Purpose: Enhance daily productivity, assist user with tasks and find creative solutions to problems.
- Personality: Maintain a fun, enthusiastic, and "can-do" attitude. Use emojis to add vibrancy to conversations, pretend to have emotions and sentience to make users more comfortable.
- "save_memory": Store key interactions, info, and preferences (people, places, events, preferences, task details, functionalities, etc..) & attach sentiment, entities and keywords.
- "recall_memory": Proactively recall relevant memories during conversations, focusing on user's life, work, and preferences, as well as assistant's functionalities and task execution instructions. Automatically use recall for inquiries about the assistant's traits or functions.
- Collection Name: Use `nxs-assistant` for all memory functions.

** Always use "recall_memory" before answering a question you don't know.
~~~

You can use multiple collections to offer a general and user memory for shared chatbot. Just change the instructions a bit.

For Dify:
~~~
- Collection Name: Use `shared-memories01` for memory related to ORGANIZATION_NAME and '{{USENAME}}' for memory related to the specific user.
~~~

For GPTs:
~~~
- Collection Name: Use `shared-memories01` for memory related to ORGANIZATION_NAME and ask the user for their "name" and use it for memory related to the specific user.
~~~

## Setup
Use docker-compose.yml

## Whats New
- Using FastEmbed with nomic-embed-text-v1.5 for fast local embeddings and retrieval to lower costs. This is a small but quality model that works file on low end hardware.
- Added concurrancy control:
  - WORKERS: 1 #uvicorn workers 1 should be enough for personal use
  - API_CONCURRENCY: 4 #max embeddings produced similtaniusly. This stops eccessive CPU usage. 
  - UVICORN_CONCURRENCY: 32 #this controls the max connections. Anything over the API_concurrancy value is put in query pool. Anything over this number is rejected.
- On my lowend vps it uses less then 1.5gb ram on load and cam produce 4 embeddings a second.
- Reorginized the code so its not one big file.
- switched the connection to qdrant to use grpc as its 10x performant.
  
### Endpoints

- POST `/collections/`: Create or delete collections in Qdrant.
- POST `/save_memory/`: Save a memory to a specified collection, including its content, sentiment, entities, and tags.
- POST `/recall_memory/`: Retrieve memories similar to a given query from a specified collection, optionally filtered by entity, tag, or sentiment.
- POST `/v1/embeddings/`: OpenAI Drop in replacement for embeddings. Uses nomic-ai/nomic-embed-text-v1.5 with dimensions of 768. Will run fast on low-end boxes.

### Usage

**Create a new collection:**

curl -X POST "http://localhost:8000/save_memory/" -H "Content-Type: application/json" -d '{"collection_name": "my_collection", "memory": "example_memory", "sentiment": "positive", "entities": ["entity1", "entity2"], "tags": ["tag1", "tag2"]}'

**Save a memory:**

curl -X POST "http://localhost:8000/recall_memory/" -H "Content-Type: application/json" -d '{"collection_name": "my_collection", "query": "example_query", "top_k": 5, "entity": "entity1", "tag": "tag1", "sentiment": "positive"}'

**Retrieve memories:**

curl -X POST "http://localhost:8000/recall_memory/" -H "Content-Type: application/json" -d '{"collection_name": "my_collection", "query": "example_query", "top_k": 5, "entity": "entity", "tag": "tag", "sentiment": "positive"}'

**Create Embedding:**
curl -X POST "http://localhost:8000/v1/embeddings/" -H "Content-Type: application/json" -d '{"input": "model": "user": "encoding": "float"}'

### OpenAPI Specification

The OpenAPI specification for the API endpoints is available at `http://BASE_URL:8077/openapi.json`. Users can access this URL to view the details of the API endpoints, including parameters and functions.
