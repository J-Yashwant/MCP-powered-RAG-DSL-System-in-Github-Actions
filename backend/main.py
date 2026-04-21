from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(title="MCP DSL RAG System")

# Configure CORS for React frontend (Vite defaults to 5173, but can be 5174 etc)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from engines.rag_engine import rag_engine

@app.on_event("startup")
async def startup_event():
    print("Initializing document ingestion pipeline...")
    rag_engine.ingest_base_documents()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
