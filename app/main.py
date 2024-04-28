import os
import uuid
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Union

from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from starlette.responses import FileResponse

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition
from fastembed import TextEmbedding

# Load environment variables for model, host and API keys
qdrant_host = os.getenv("QDRANT_HOST")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
memories_api_key = os.getenv("MEMORIES_API_KEY")
base_url = os.getenv("BASE_URL")

# Initialize clients for database and AI
db_client = QdrantClient(url=qdrant_host, api_key=qdrant_api_key)
embeddings_model = TextEmbedding("nomic-ai/nomic-embed-text-v1.5")

# Setup the bearer token authentication scheme
bearer_scheme = HTTPBearer(auto_error=False)

# Function to get API key
async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    if memories_api_key and (not credentials or credentials.credentials != memories_api_key):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

# FastAPI application instance
app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application to remember and recall things",
    servers=[{"url": base_url, "description": "Base API server"}]
)

class MemoryParams(BaseModel):
    collection_name: str = Field(..., description="The name of the collection to be created.")
    memory: str = Field(..., description="The content of the memory to be stored.")
    sentiment: str = Field(..., description="The sentiment associated with the memory.")
    entities: List[str] = Field(..., description="A list of entities identified in the memory.")
    tags: List[str] = Field(..., description="A list of tags associated with the memory.")

    @validator("entities", "tags", pre=True)
    def split_str_values(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

class SearchParams(BaseModel):
    collection_name: str = Field(..., description="The name of the collection to search in.")
    query: str = Field(..., description="The search query used to retrieve similar memories.")
    top_k: int = Field(5, description="The number of most similar memories to return.")
    entity: Optional[str] = Field(None, description="An entity to filter the search.")
    tag: Optional[str] = Field(None, description="A tag to filter the search.")
    sentiment: Optional[str] = Field(None, description="The sentiment to filter the search.")

class CreateCollectionParams(BaseModel):
    collection_name: str = Field(..., description="The name of the collection to be created.")

class EmbeddingParams(BaseModel):
    input: Union[List[str], str]
    model: str
    user: Optional[str] = "unassigned"
    encoding_format: Optional[str] = "float"

@app.post("/save_memory", operation_id="save_memory")
async def save_memory(params: MemoryParams, api_key: str = Depends(get_api_key)):
    try:
        # Generate an embedding from the memory text
        embeddings_generator = embeddings_model.embed(params.memory)

        # Extract the single vector from the generator
        vector = next(embeddings_generator)  # This fetches the first item from the generator

        if isinstance(vector, np.ndarray):
            vector_list = vector.tolist()  # Convert numpy array to list
            print("Converted Vector List:", vector_list)
        else:
            raise ValueError("The embedding is not in the expected format (np.ndarray)")

        timestamp = datetime.utcnow().isoformat()
        unique_id = str(uuid.uuid4())

        # Upsert the memory into the Qdrant collection
        db_client.upsert(collection_name=params.collection_name, points=[{
            "id": unique_id,
            "vector": vector_list,
            "payload": {
                "memory": params.memory,
                "timestamp": timestamp,
                "sentiment": params.sentiment,
                "entities": params.entities,
                "tags": params.tags,
            },
        }])
    except Exception as e:
        # Provide more detailed error messaging
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
    print("Saved Memory: {params.memory}")
    return {"message": "Memory saved successfully"}

@app.post("/recall_memory", operation_id="recall_memory")
async def recall_memory(params: SearchParams, api_key: str = Depends(get_api_key)):
    try:
        embeddings_generator = embeddings_model.embed(params.query)
        # Extract the single vector from the generator
        vector = next(embeddings_generator)  # This fetches the first item from the generator

        if isinstance(vector, np.ndarray):
            vector_list = vector.tolist()  # Convert numpy array to list
            print("Converted Vector List:", vector_list)
        
        search_filter = []

        # Add entity filter if provided
        if params.entity:
            search_filter.append(FieldCondition(key="entities", match=MatchValue(value=params.entity)))

        # Add tag filter if provided
        if params.tag:
            search_filter.append(FieldCondition(key="tags", match=MatchValue(value=params.tag)))

        # Add sentiment filter if provided
        if params.sentiment:
            search_filter.append(FieldCondition(key="sentiment", match=MatchValue(value=params.sentiment)))

        # Construct the filter query with all specified conditions
        filter_query = Filter(must=search_filter) if search_filter else None

        # Perform the search with the specified filters
        hits = db_client.search(
            collection_name=params.collection_name,
            query_vector=vector_list,
            query_filter=filter_query,
            limit=params.top_k,
        )

        # Format the results
        results = [{
            "id": hit.id,
            "memory": hit.payload["memory"],
            "timestamp": hit.payload["timestamp"],
            "sentiment": hit.payload["sentiment"],
            "entities": hit.payload["entities"],
            "tags": hit.payload["tags"],
            "score": hit.score,
        } for hit in hits]

        print("Recalled Memories:", results)
        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/collections", operation_id="collection")
async def create_collection(params: CreateCollectionParams, api_key: str = Depends(get_api_key)):
    try:
        db_client.recreate_collection(
            collection_name=params.collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        
        db_client.create_payload_index(
            collection_name=params.collection_name,
            field_name="sentiment", field_schema="keyword",
            field_name="entities", field_schema="keyword",
            field_name="tags", field_schema="keyword"
        )
        
        print("Collection {params.collection_name} created successfully")
        return {"message": f"Collection '{params.collection_name}' created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating collection: {str(e)}")

@app.post("/v1/embeddings")
async def embedding_request(request: EmbeddingParams):
    try:
        # Normalize input to always be a list
        if isinstance(request.input, str):  # Fixed to request.input
            input_texts = [request.input]  # Convert single string to list
        else:
            input_texts = request.input  # It's already a list

        # Assuming embeddings_model is initialized and available globally or injected
        embeddings = [embeddings_model.embed(text) for text in input_texts]
        embeddings = []
        embedding_objects = []

        # Iterate over each set of embeddings
        for index, vectors in enumerate(embeddings):
            for vector in vectors:
                # Convert NumPy array to list for JSON serialization
                embedding_objects.append({
                    "object": "embedding",
                    "embedding": vector.tolist(),
                    "index": index
                })

        # Construct the response data
        response_data = {
            "object": "list",
            "data": embedding_objects,
            "model": request.model,
            "usage": {
                "prompt_tokens": sum(len(text.split()) for text in input_texts),
                "total_tokens": sum(len(text.split()) for text in input_texts)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating embedding: {str(e)}")
    print("Response data:", response_data)
    return response_data

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

app.mount("/static", StaticFiles(directory="/app/public"), name="static")
