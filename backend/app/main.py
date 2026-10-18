import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import init_db, SessionLocal
from .seed import seed_database
from .bank_api import router as bank_router
from .store_api import router as store_router
from .core_api import router as core_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seed realistic mock records
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="EvidentAI — Chargeback Evidence Assistant",
    description="Agentic AI assistant orchestrating dispute evidence collection, deterministic financial checks, human approval, and independent verification for Ziro.Digital Hackathon 2026.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Vite frontend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized safe error handling without exposing internal stack traces
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred during request processing. Please contact system administrator."
        }
    )

# Include Routers
app.include_router(core_router)
app.include_router(bank_router)
app.include_router(store_router)

@app.get("/health", tags=["Health Check"])
def health_check():
    return {
        "status": "HEALTHY",
        "service": "EvidentAI Backend API",
        "version": "1.0.0"
    }
