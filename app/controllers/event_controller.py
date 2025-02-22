from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.event_service import EventService
from app.schemas.vote import EventCreate, EventResponse
from fastapi.responses import JSONResponse

class EventController:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.service = EventService()

    async def create_event(self, data: EventCreate) -> JSONResponse:
        event = self.service.create_event(self.db, data)
        return JSONResponse({
            "event_id": event.id,
            "message": "活動建立成功"
        })

    async def toggle_voting(self, event_id: str, start_voting: bool) -> JSONResponse:
        event = self.service.toggle_voting(self.db, event_id, start_voting)
        status = "開始" if start_voting else "停止"
        return JSONResponse({"message": f"投票已{status}"}) 