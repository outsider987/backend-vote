# main.py
import uuid
import asyncio
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from db import get_db
from models import Event, Ticket, Vote
from app.api.endpoints import vote

app = FastAPI(title="Voting System API")

# 儲存連線中的 WebSocket 客戶端
active_websockets: List[WebSocket] = []


# 定義建立活動的資料模型
class CreateEventModel(BaseModel):
    event_date: str           # 活動日期 (YYYY-MM-DD)
    member_count: int         # 會員人數
    title: str                # 投票標題
    options: List[str]        # 候選人選項 (陣列格式)
    votes_per_user: int       # 每人可投票數
    show_count: int           # 結果顯示人數


@app.post("/api/create-event")
async def create_event(data: CreateEventModel, db: Session = Depends(get_db)):
    """
    建立投票事件：
    - 接收活動日期、會員人數、標題、候選人選項等資料
    - 產生唯一活動 ID，並初始化候選人得票數
    """
    event_id = str(uuid.uuid4())
    db_event = Event(
        id=event_id,
        event_date=data.event_date,
        member_count=data.member_count,
        title=data.title,
        options=data.options,
        votes_per_user=data.votes_per_user,
        show_count=data.show_count
    )
    db.add(db_event)
    db.commit()
    
    return JSONResponse({"event_id": event_id, "message": "活動建立成功"})


@app.post("/api/generate-ticket")
async def generate_ticket(event_id: str, db: Session = Depends(get_db)):
    """
    產生票券：
    - 產生唯一的 vote_code 作為票券
    - 可在資料庫中記錄票券狀態 (此處僅模擬存入全域變數)
    """
    # 檢查活動是否存在
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return JSONResponse({"message": "活動不存在"}, status_code=400)
    
    vote_code = str(uuid.uuid4())
    db_ticket = Ticket(vote_code=vote_code, event_id=event_id)
    db.add(db_ticket)
    db.commit()
    
    return JSONResponse({"vote_code": vote_code})


@app.post("/api/vote")
async def submit_vote(
    vote_code: str = Form(...),
    candidate_ids: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    接收投票資料：
    - vote_code: 票券編碼 (可用於驗證是否重複投票)
    - candidate_ids: 以逗號分隔的候選人選項 (例如 "候選人1,候選人2")
    
    此處僅模擬更新候選人得票數並回傳投票成功訊息，
    同時透過 WebSocket 傳送最新得票數給所有連線端。
    """
    # 檢查票券
    ticket = db.query(Ticket).filter(Ticket.vote_code == vote_code).first()
    if not ticket:
        return JSONResponse({"message": "票券無效"}, status_code=400)
    if ticket.used:
        return JSONResponse({"message": "票券已使用"}, status_code=400)

    # 更新票券狀態
    ticket.used = True
    
    # 記錄投票
    for cid in candidate_ids.split(','):
        cid = cid.strip()
        vote = Vote(
            id=str(uuid.uuid4()),
            event_id=ticket.event_id,
            vote_code=vote_code,
            candidate=cid
        )
        db.add(vote)
    
    db.commit()

    # 取得最新投票統計
    vote_counts = db.query(
        Vote.candidate,
        func.count(Vote.id).label('count')
    ).filter(
        Vote.event_id == ticket.event_id
    ).group_by(Vote.candidate).all()
    
    vote_results = {v.candidate: v.count for v in vote_counts}

    # 推送最新結果給所有 WebSocket 客戶端
    for ws in active_websockets:
        await ws.send_json(vote_results)

    return JSONResponse({"message": "投票成功"})

@app.get("/api/vote-info")
async def vote_info(vote_code: str, db: Session = Depends(get_db)):
    """
    查詢票券及投票活動相關資訊：
    - 若票券存在且未使用，回傳活動資訊 (以目前模擬的第一個建立之活動)
    - 回傳資料包含：活動 ID、標題、候選人選項、每人可投票數
    """
    ticket = db.query(Ticket).filter(Ticket.vote_code == vote_code).first()
    if not ticket:
        return JSONResponse({"message": "票券無效"}, status_code=400)
    
    event = db.query(Event).filter(Event.id == ticket.event_id).first()
    if not event:
        return JSONResponse({"message": "活動不存在"}, status_code=400)

    return JSONResponse({
        "event_id": event.id,
        "title": event.title,
        "options": event.options,
        "votes_per_user": event.votes_per_user
    })



@app.websocket("/ws/vote-updates")
async def vote_updates(websocket: WebSocket):
    """
    WebSocket 端點：
    - 接受前端連線
    - 定時（每 2 秒）推送最新的得票數 (實際上可改為事件驅動)
    """
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            # 每2秒更新一次投票結果
            with get_db() as db:
                # 取得所有活動的投票統計
                vote_counts = db.query(
                    Vote.candidate,
                    func.count(Vote.id).label('count')
                ).group_by(Vote.candidate).all()
                
                vote_results = {v.candidate: v.count for v in vote_counts}
                await websocket.send_json(vote_results)
            
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

app.include_router(vote.router, prefix="/api", tags=["voting"])
