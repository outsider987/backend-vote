from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Form
from app.controllers.event_controller import EventController
from app.controllers.ticket_controller import TicketController
from app.controllers.vote_controller import VoteController
from app.schemas.vote import EventCreate
from typing import List

router = APIRouter()

# Event routes
@router.post("/create-event")
async def create_event(
    data: EventCreate,
    controller: EventController = Depends()
):
    return await controller.create_event(data)

@router.post("/toggle-voting")
async def toggle_voting(
    event_id: str,
    start_voting: bool,
    controller: EventController = Depends()
):
    return await controller.toggle_voting(event_id, start_voting)

# Ticket routes
@router.post("/generate-ticket")
async def generate_ticket(
    event_id: str,
    controller: TicketController = Depends()
):
    return await controller.generate_ticket(event_id)

@router.get("/vote-info/{vote_code}")
async def get_vote_info(
    vote_code: str,
    controller: TicketController = Depends()
):
    return await controller.get_vote_info(vote_code)

# Vote routes
@router.post("/vote")
async def submit_vote(
    vote_code: str = Form(...),
    candidate_ids: str = Form(...),
    controller: VoteController = Depends()
):
    candidate_list = [cid.strip() for cid in candidate_ids.split(',')]
    return await controller.submit_vote(vote_code, candidate_list)

@router.websocket("/ws/vote-updates")
async def vote_updates(
    websocket: WebSocket,
    controller: VoteController = Depends()
):
    await controller.handle_websocket(websocket)

# Add other routes similarly... 