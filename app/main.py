import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from qdrant_client import QdrantClient

# Configuration for vector size, distance, and HNSW
VECTOR_SIZE = 1536  # Adjust based on your embedding dimensionality
DISTANCE = "cosine"
HNSW_CONFIG = {
    "M": 16,
    "ef_construct": 100,
}

# Loading environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
embeddings_model = os.getenv("EMBEDDINGS_MODEL")  # e.g., "text-embedding-ada-002"
qdrant_host = os.getenv("QDRANT_HOST")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
base_url = os.getenv("BASE_URL")

# Initialize Qdrant client
client = QdrantClient(host=qdrant_host, api_key=qdrant_api_key)

# FastAPI application instance
app = FastAPI(
    title="PDF Generation API",
    version="0.1.0",
    description="A FastAPI application to remember and recall things",
    servers=[{"url": "{base_url}", "description": "Base API server"}]
)

# The MemoryData class is a Pydantic model that represents the data structure of a memory.
# It includes fields for the content of the memory, its associated sentiment, identified entities, and associated tags.
class MemoryData(BaseModel):
    # The content of the memory to be stored.
    memory: str = Field(..., description="The content of the memory to be stored.")

    # The sentiment associated with the memory (e.g., positive, negative, neutral).
    sentiment: str = Field(..., description="The sentiment associated with the memory (e.g., positive, negative, neutral).")

    # A list of entities identified in the memory.
    entities: List[str] = Field(..., description="A list of entities identified in the memory.")

    # A list of tags associated with the memory.
    tags: List[str] = Field(..., description="A list of tags associated with the memory.")

    # Validator for "entities" and "tags" fields. If the value is a string, it splits it into a list of strings.
    @validator("entities", "tags", pre=True)
    def split_str_values(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

# The SearchParams class is a Pydantic model representing the search parameters.
# It includes fields for the search query and the number of most similar memories to return.
class SearchParams(BaseModel):
    # The search query used to retrieve similar memories.
    query: str = Field(..., description="The search query used to retrieve similar memories.")

    # The number of most similar memories to return.
    top_k: int = Field(..., description="The number of most similar memories to return.")

# The CreateCollectionParams class is a Pydantic model representing the parameters for creating a collection.
# It includes a field for the name of the collection to be created.
class CreateCollectionParams(BaseModel):
    # The name of the collection to be created.
    collection_name: str = Field(..., description="The name of the collection to be created.")


@app.post("/save_memory")
async def save_memory(data: MemoryData):
    # Generate embedding vector
    response = openai.Embedding.create(
        input=data.memory, engine=embeddings_model
    )
    vector = response['data'][0]['embedding']

    # Create timestamp
    timestamp = datetime.utcnow().isoformat()

    # Create UUID
    unique_id = str(uuid.uuid4())

    # Create Qdrant point
    point = {
        "id": unique_id,  # Use the generated UUID as the ID
        "vector": vector,
        "payload": {
            "memory": data.memory,
            "timestamp": timestamp,
            "sentiment": data.sentiment,
            "entities": data.entities,
            "tags": data.tags,
        },
    }

    # Upsert point to Qdrant collection (replace if exists)
    try:
        client.upsert(collection_name=data.collection_name, points=[point])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving to Qdrant: {e}")

    return {"message": "Memory saved successfully"}

class SearchParams(BaseModel):
    query: str
    entities: List[str]
    tags: List[str]
    sentiment: str
    collection_name: str

    @validator("entities", "tags", pre=True)
    def split_str_values(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

@app.post("/retrieve_memory")
async def retrieve_memory(params: SearchParams):
    # Generate embedding vector for the query
    response = openai.Embedding.create(input=params.query, engine=embeddings_model)
    query_vector = response['data'][0]['embedding']

    # Build search filter based on optional parameters
    search_filter = {}
    if params.entities:
        search_filter["must"] = [
            {"key": "entities", "match": {"value": entity}} for entity in params.entities
        ]
    if params.tags:
        if "must" in search_filter:
            search_filter["must"].extend(
                [{"key": "tags", "match": {"value": tag}} for tag in params.tags]
            )
        else:
            search_filter["must"] = [
                {"key": "tags", "match": {"value": tag}} for tag in params.tags
            ]
    if params.sentiment:
        if "must" in search_filter:
            search_filter["must"].append(
                {"key": "sentiment", "match": {"value": params.sentiment}}
            )
        else:
            search_filter["must"] = [
                {"key": "sentiment", "match": {"value": params.sentiment}}
            ]

    # Search Qdrant for similar vectors
    search_result = client.search(
        collection_name=params.collection_name,
        query_vector=query_vector,
        limit=5,
        filter=search_filter if search_filter else None,
    )

    # Extract results and return (including ID)
    results = [
        {
            "id": hit.id,  # Include the ID in the results
            "memory": hit.payload["memory"],
            "timestamp": hit.payload["timestamp"],
            "sentiment": hit.payload["sentiment"],
            "entities": hit.payload["entities"],
            "tags": hit.payload["tags"],
            "score": hit.score,
        }
        for hit in search_result
    ]
    return {"results": results}

class CreateCollectionParams(BaseModel):
    collection_name: str

@app.post("/collections")
async def create_collection(params: CreateCollectionParams):
    try:
        # Define payload schema
        payload_schema = {
            "memory": {"type": "text"},
            "timestamp": {"type": "date"},
            "sentiment": {"type": "keyword"},
            "entities": {"type": "keyword"},
            "tags": {"type": "keyword"},
        }

        client.recreate_collection(
            collection_name=params.collection_name,
            vector_size=VECTOR_SIZE,
            distance=DISTANCE,
            hnsw_config=HNSW_CONFIG,
            payload_schema=payload_schema,
        )
        return {"message": f"Collection '{params.collection_name}' created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating collection: {e}")
