from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.db.database import get_db
from app.models.models import Event, Ticket, Vote
from app.schemas.vote import (
    EventCreate, EventResponse, TicketCreate, TicketResponse,
    VoteCreate, VoteResponse, VoteCount, VoteInfo
)

router = APIRouter()
active_websockets: List[WebSocket] = []

@router.post("/events", response_model=EventResponse)
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    db_event = Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.post("/tickets", response_model=TicketResponse)
async def generate_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == str(ticket.event_id)).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db_ticket = Ticket(event_id=str(ticket.event_id))
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.post("/votes")
async def submit_vote(vote: VoteCreate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.vote_code == str(vote.vote_code)).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.used:
        raise HTTPException(status_code=400, detail="Ticket already used")

    ticket.used = True
    
    for candidate_id in vote.candidate_ids:
        vote = Vote(
            event_id=ticket.event_id,
            vote_code=str(ticket.vote_code),
            candidate=candidate_id
        )
        db.add(vote)
    
    db.commit()

    vote_counts = get_vote_counts(db, ticket.event_id)
    
    for ws in active_websockets:
        await ws.send_json([count.model_dump() for count in vote_counts])

    return {"message": "Vote submitted successfully"}

@router.get("/vote-info/{vote_code}", response_model=VoteInfo)
async def get_vote_info(vote_code: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.vote_code == vote_code).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    event = db.query(Event).filter(Event.id == ticket.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return VoteInfo(
        event_id=event.id,
        title=event.title,
        options=event.options,
        votes_per_user=event.votes_per_user
    )

def get_vote_counts(db: Session, event_id: str) -> List[VoteCount]:
    results = db.query(
        Vote.candidate,
        func.count(Vote.id).label('count')
    ).filter(
        Vote.event_id == event_id
    ).group_by(Vote.candidate).all()
    
    return [VoteCount(candidate=r.candidate, count=r.count) for r in results]

@router.websocket("/ws/vote-updates")
async def vote_updates(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            with get_db() as db:
                vote_counts = []
                for event in db.query(Event).all():
                    vote_counts.extend(get_vote_counts(db, event.id))
                await websocket.send_json([count.model_dump() for count in vote_counts])
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        active_websockets.remove(websocket) 