# main.py
import uuid
import asyncio
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

# 模擬儲存：活動資料、候選人得票數以及票券資料
events = {}         # event_id => 活動資料
vote_counts = {}    # candidate_option => 得票數
tickets = {}        # vote_code => 是否已使用 (False: 尚未使用)

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
async def create_event(data: CreateEventModel):
    """
    建立投票事件：
    - 接收活動日期、會員人數、標題、候選人選項等資料
    - 產生唯一活動 ID，並初始化候選人得票數
    """
    event_id = str(uuid.uuid4())
    events[event_id] = data.dict()

    # 初始化候選人得票數
    for option in data.options:
        vote_counts[option] = 0

    return JSONResponse({"event_id": event_id, "message": "活動建立成功"})


@app.post("/api/generate-ticket")
async def generate_ticket():
    """
    產生票券：
    - 產生唯一的 vote_code 作為票券
    - 可在資料庫中記錄票券狀態 (此處僅模擬存入全域變數)
    """
    vote_code = str(uuid.uuid4())
    tickets[vote_code] = False  # 尚未使用
    return JSONResponse({"vote_code": vote_code})


@app.post("/api/vote")
async def submit_vote(vote_code: str = Form(...), candidate_ids: str = Form(...)):
    """
    接收投票資料：
    - vote_code: 票券編碼 (可用於驗證是否重複投票)
    - candidate_ids: 以逗號分隔的候選人選項 (例如 "候選人1,候選人2")
    
    此處僅模擬更新候選人得票數並回傳投票成功訊息，
    同時透過 WebSocket 傳送最新得票數給所有連線端。
    """
    # 檢查票券是否存在且未使用
    if vote_code not in tickets:
        return JSONResponse({"message": "票券無效"}, status_code=400)
    if tickets[vote_code]:
        return JSONResponse({"message": "票券已使用"}, status_code=400)
    # 標記票券已使用
    tickets[vote_code] = True

    # 更新每位候選人的票數 (假設 candidate_ids 為以逗號分隔的候選人名稱)
    for cid in candidate_ids.split(','):
        cid = cid.strip()
        if cid in vote_counts:
            vote_counts[cid] += 1
        else:
            # 若候選人不存在，可回傳錯誤或忽略 (此處選擇忽略)
            pass

    # 將更新結果推送給所有已連線的 WebSocket 客戶端
    for ws in active_websockets:
        await ws.send_json(vote_counts)

    return JSONResponse({"message": "投票成功"})

@app.get("/api/vote-info")
async def vote_info(vote_code: str):
    """
    查詢票券及投票活動相關資訊：
    - 若票券存在且未使用，回傳活動資訊 (以目前模擬的第一個建立之活動)
    - 回傳資料包含：活動 ID、標題、候選人選項、每人可投票數
    """
    if vote_code not in tickets:
        return JSONResponse({"message": "票券無效"}, status_code=400)
    if not events:
        return JSONResponse({"message": "尚未建立活動"}, status_code=400)
    # 此處取第一個活動作為範例（實際應依票券與活動關聯來查詢）
    event_id, event = list(events.items())[0]
    return JSONResponse({
        "event_id": event_id,
        "title": event["title"],
        "options": event["options"],
        "votes_per_user": event["votes_per_user"]
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
            # 主動推送最新得票數，間隔 2 秒
            await websocket.send_json(vote_counts)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
