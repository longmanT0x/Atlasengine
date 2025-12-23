"""
ATLAS - Decision Intelligence for Market Viability

Main FastAPI application entry point.

ATLAS evaluates startup market viability under uncertainty by:
- Researching market data from traceable sources
- Extracting structured information
- Modeling market dynamics with uncertainty
- Making evidence-based decisions
- Storing all evidence and assumptions

Core Principles:
- Never invent market numbers
- Always expose assumptions
- Always output ranges, not single values
- Every factual claim must be traceable to a source
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api import router as api_router
from app.storage.database import init_db

# Load environment variables
load_dotenv()

# Initialize FastAPI application
app = FastAPI(
    title="ATLAS - Decision Intelligence Engine",
    description="Evaluates startup market viability under uncertainty",
    version="0.1.0",
)

# Configure CORS
# Get allowed origins from environment or default to allow all for development
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    # Development mode - allow all origins
    allow_origins = ["*"]
else:
    # Production mode - use configured origins
    allow_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization had issues: {e}")
        # Continue anyway - database will be created on first use


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "ATLAS",
        "description": "Decision Intelligence for Market Viability",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

