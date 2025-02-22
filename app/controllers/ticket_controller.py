from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.ticket_service import TicketService
from fastapi.responses import JSONResponse

class TicketController:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.service = TicketService()

    async def generate_ticket(self, event_id: str) -> JSONResponse:
        ticket = self.service.generate_ticket(self.db, event_id)
        return JSONResponse({"vote_code": ticket.vote_code})

    async def get_vote_info(self, vote_code: str) -> JSONResponse:
        ticket = self.service.get_vote_info(self.db, vote_code)
        return JSONResponse({
            "event_id": ticket.event.id,
            "title": ticket.event.title,
            "options": ticket.event.options,
            "votes_per_user": ticket.event.votes_per_user
        }) 