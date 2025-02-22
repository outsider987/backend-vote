from fastapi import Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.vote_service import VoteService
from fastapi.responses import JSONResponse
from typing import List
import asyncio

class VoteController:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.service = VoteService()
        self.active_websockets: List[WebSocket] = []

    async def submit_vote(self, vote_code: str, candidate_ids: List[str]) -> JSONResponse:
        self.service.submit_vote(self.db, vote_code, candidate_ids)
        
        # Get updated vote counts and broadcast to websocket clients
        vote_counts = self.service.get_vote_counts(self.db, vote_code)
        for ws in self.active_websockets:
            await ws.send_json(vote_counts)
            
        return JSONResponse({"message": "投票成功"})

    async def handle_websocket(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.append(websocket)
        
        try:
            while True:
                vote_counts = self.service.get_vote_counts(self.db, None)  # Get all vote counts
                await websocket.send_json(vote_counts)
                await asyncio.sleep(2)
        except WebSocketDisconnect:
            self.active_websockets.remove(websocket) 