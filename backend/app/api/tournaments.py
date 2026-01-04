from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.models.tournament import Tournament, TournamentStatus, Stage, StageType, TournamentParticipant
from app.models.user import Player, User
from app.api.auth import get_current_user
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime, timezone
from uuid import UUID

router = APIRouter()

class TournamentCreate(BaseModel):
    name: str
    rules_config: Dict[str, Any] = {}
    prize_pool_config: Dict[str, Any] = {}
    start_time: Optional[datetime] = None
    rules_content: Optional[str] = None
    stages_config: List[Dict[str, Any]] = []

class TournamentUpdate(BaseModel):
    status: Optional[TournamentStatus] = None
    name: Optional[str] = None
    rules_config: Optional[Dict[str, Any]] = None
    prize_pool_config: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    rules_content: Optional[str] = None

@router.post("/", response_model=Tournament)
async def create_tournament(
    t_data: TournamentCreate,
    session: AsyncSession = Depends(get_session)
):
    # Handle timezone for start_time
    start_time = t_data.start_time
    if start_time and start_time.tzinfo:
        start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)

    tourney = Tournament(
        name=t_data.name,
        status=TournamentStatus.SETUP,
        rules_config=t_data.rules_config,
        prize_pool_config=t_data.prize_pool_config,
        start_time=start_time,
        rules_content=t_data.rules_content
    )
    session.add(tourney)
    await session.commit()
    await session.refresh(tourney)
    
    if t_data.stages_config:
        for i, s_cfg in enumerate(t_data.stages_config):
            stage = Stage(
                tournament_id=tourney.id,
                name=s_cfg.get("name", f"Stage {i+1}"),
                stage_type=s_cfg.get("stage_type", StageType.ROUND_ROBIN),
                sequence_order=i+1,
                rules_config=s_cfg.get("rules_config", {})
            )
            session.add(stage)
        await session.commit()

    return tourney

@router.get("/", response_model=List[Tournament])
async def list_tournaments(
    session: AsyncSession = Depends(get_session),
    status: Optional[TournamentStatus] = None
):
    if status:
        stmt = select(Tournament).where(Tournament.status == status).order_by(Tournament.created_at.desc())
    else:
        stmt = select(Tournament).order_by(Tournament.created_at.desc())
    result = await session.exec(stmt)
    return result.all()

@router.get("/current", response_model=Optional[Tournament])
async def get_current_tournament(session: AsyncSession = Depends(get_session)):
    stmt = select(Tournament).order_by(Tournament.created_at.desc())
    result = await session.exec(stmt)
    return result.first()

@router.patch("/{tournament_id}", response_model=Tournament)
async def update_tournament(
    tournament_id: UUID,
    update_data: TournamentUpdate,
    session: AsyncSession = Depends(get_session)
):
    tourney = await session.get(Tournament, tournament_id)
    if not tourney:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    if update_data.name is not None:
        tourney.name = update_data.name
    if update_data.status is not None:
        tourney.status = update_data.status
    if update_data.rules_config is not None:
        tourney.rules_config = update_data.rules_config
    if update_data.prize_pool_config is not None:
        tourney.prize_pool_config = update_data.prize_pool_config
    if update_data.start_time is not None:
        # Handle timezone for start_time
        start_time = update_data.start_time
        if start_time and start_time.tzinfo:
            start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
        tourney.start_time = start_time
    if update_data.rules_content is not None:
        tourney.rules_content = update_data.rules_content
        
    # Auto-generate rules content if we have prize pool and start time but no content or just updating params
    # This is a basic implementation of the requirement "automatically update this rules template"
    if update_data.prize_pool_config or update_data.start_time:
        if not tourney.rules_content or "Generated" in tourney.rules_content:
             tourney.rules_content = generate_rules_template(tourney)

    session.add(tourney)
    await session.commit()
    await session.refresh(tourney)
    return tourney

@router.post("/{tournament_id}/checkin")
async def check_in_tournament(
    tournament_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Find player
    stmt = select(Player).where(Player.user_id == current_user.id)
    result = await session.exec(stmt)
    player = result.first()
    
    if not player:
        raise HTTPException(status_code=400, detail="No player profile bound to account")
        
    tourney = await session.get(Tournament, tournament_id)
    if not tourney:
        raise HTTPException(404, "Tournament not found")
        
    participant = await session.get(TournamentParticipant, (tournament_id, player.id))
    if not participant:
        participant = TournamentParticipant(
            tournament_id=tournament_id,
            player_id=player.id,
            checked_in=True,
            checked_in_at=datetime.utcnow()
        )
        session.add(participant)
    else:
        if participant.checked_in:
             return {"message": "Already checked in"}
        participant.checked_in = True
        participant.checked_in_at = datetime.utcnow()
        session.add(participant)
        
    await session.commit()
    return {"message": "Check-in successful"}

@router.get("/{tournament_id}/participants")
async def get_participants(
    tournament_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(TournamentParticipant, Player).where(
        TournamentParticipant.tournament_id == tournament_id
    ).where(TournamentParticipant.checked_in == True).join(Player)
    
    results = await session.exec(stmt)
    data = []
    for tp, p in results:
        data.append({
            "tournament_id": tp.tournament_id,
            "player_id": tp.player_id,
            "checked_in": tp.checked_in,
            "checked_in_at": tp.checked_in_at,
            "player": {
                "in_game_name": p.in_game_name,
                "qq_id": p.qq_id
            }
        })
    return data

def generate_rules_template(tourney: Tournament) -> str:
    # Generate a Markdown-friendly template
    date_str = tourney.start_time.strftime("%Y年%m月%d日") if tourney.start_time else "待定"
    
    prizes = tourney.prize_pool_config or {}
    total = prizes.get("total", "1100 RMB")
    
    points_map = tourney.rules_config.get("points_map", {1:9, 2:5, 3:3, 4:2, 5:1})
    points_text = ", ".join([f"{k}名得{v}分" for k, v in sorted(points_map.items())])

    lines = [
        f"# {tourney.name} 赛事规则与赛程",
        f"**更新日期**: {datetime.now().strftime('%Y年%m月%d日')}\n",
        
        "## 1. 比赛时间安排",
        f"- **开赛时间**: {date_str}",
        "- **阶段划分**: 本次比赛将分为多个阶段，具体赛程如下（以最终通知为准）：",
        "  - **海选赛**: 详情待公布",
        "  - **小组赛**: 详情待公布",
        "  - **淘汰赛**: 详情待公布\n",
        
        "## 2. 报名与签到流程",
        "- 本届设有种子选手制度，具体报名方式请关注官方群公告。",
        "- 选手需在规定时间内完成线上签到，逾期可能影响参赛资格。\n",
        
        "## 3. 赛事阶段与晋级规则",
        "- **海选赛**: 选拔出晋级选手进入小组赛。",
        "- **小组赛**: 采用循环赛制，根据积分决定淘汰赛资格。",
        "- **淘汰赛**: 采用双败淘汰制，直至决出最终冠军。\n",
        
        "## 4. 比赛形式与积分规则",
        "- **对局形式**: 每人出三匹马，3人一组，进行9匹马的混战。",
        "- **积分细则**: 每场比赛，" + points_text + "。",
        "- **加分项**: 各阶段多场房间中“一位”数超过总房间数一半（向下取整）的，每多一场额外+2分。\n",
        
        "## 5. 奖金池",
        f"本届基础奖金池为: **{total}**",
        "**奖励分配如下**:\n"
    ]
    
    alloc = prizes.get("allocation", {})
    if isinstance(alloc, dict):
        for k, v in alloc.items():
            lines.append(f"- **第{k}名**: {v}")
    lines.append("\n")

    lines.append("## 6. 注意事项",)
    lines.append("- 比赛结果需自行记录表格，分数由表格自动计算；建议保存自己参加的所有对局截图。")
    lines.append("- 关于如何建房、填表等操作，请参照群内图文文件说明。\n")

    lines.append("## 7. 主办方声明")
    lines.append("喵喵杯由猫猫头的炼金工坊主办，是非盈利娱乐赛事。欢迎各位放松心情享受比赛。我们会尽量维持比赛公平，也希望大家多多包容、配合。群内有任何疑问或意见欢迎随时联系主办方。期待与你再续前缘喵！")
    
    return "\n".join(lines)
