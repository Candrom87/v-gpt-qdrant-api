# main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

# Third-Party Library Imports
from dependencies import limit_concurrency
from routes.embeddings import embeddings_router
from routes.memory import memory_router

# FastAPI Application Initialization
app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application that allows users to save memories ...",
    servers=[{"url": os.getenv("BASE_URL"), "description": "Base API server"}]
)

# Applying the concurrency limit middleware (assuming it's a middleware factory)
app.middleware('http')(limit_concurrency)

# Including Routers
app.include_router(memory_router)
app.include_router(embeddings_router)

# Mounting static files directory
app.mount("/static", StaticFiles(directory="/app/public"), name="static")

# Root endpoint - Serves the index.html file
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

# v1 endpoint - Serves the index.html file
@app.get("/v1", include_in_schema=False)
async def v1():
    return FileResponse("/app/public/index.html")
