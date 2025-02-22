# main.py
import uuid
import asyncio
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.db.database import get_db, init_db, dispose_engine, SessionLocal
from app.models.models import Event, Ticket, Vote
from app.api.endpoints import vote
from fastapi.middleware.cors import CORSMiddleware
from app.errors.handlers import VotingError, voting_exception_handler, ErrorCodes
from app.core.config import settings
import logging
from app.api.routes import router

logger = logging.getLogger(__name__)
app = FastAPI(title="Voting System API")

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handler
app.add_exception_handler(VotingError, voting_exception_handler)

# 儲存連線中的 WebSocket 客戶端
active_websockets: List[WebSocket] = []





app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup database connections on shutdown"""
    dispose_engine()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
