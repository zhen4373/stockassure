from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import Location
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/v1/locations", tags=["Location 空間管理"])

# Pydantic 數據校驗模型
class LocationCreateSchema(BaseModel):
    name: str
    parent_id: Optional[int] = None

class LocationUpdateSchema(BaseModel):
    new_parent_id: Optional[int] = None


def check_cyclical_location(db: Session, current_location_id: int, target_parent_id: int) -> bool:
    """無限死循環防禦演算法"""
    if current_location_id == target_parent_id:
        return True
    loop_id = target_parent_id
    while loop_id is not None:
        parent_loc = db.query(Location).filter(Location.id == loop_id).first()
        if not parent_loc:
            break
        if parent_loc.parent_id == current_location_id:
            return True
        loop_id = parent_loc.parent_id
    return False


@router.post("/", response_model=dict)
def create_new_location(payload: LocationCreateSchema, db: Session = Depends(get_db)):
    """新增一個儲物空間（支援多層級子空間）"""
    if payload.parent_id:
        parent = db.query(Location).filter(Location.id == payload.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="指定的父空間不存在")
            
    loc = Location(name=payload.name, parent_id=payload.parent_id)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return {"status": "success", "id": loc.id, "name": loc.name, "parent_id": loc.parent_id}


@router.get("/", response_model=List[dict])
def list_all_locations(db: Session = Depends(get_db)):
    """列出全系統扁平化的空間列表"""
    locations = db.query(Location).all()
    return [{"id": l.id, "name": l.name, "parent_id": l.parent_id} for l in locations]


@router.patch("/{location_id}/move")
def move_location(location_id: int, payload: LocationUpdateSchema, db: Session = Depends(get_db)):
    """移動儲物空間（內建死循環安全防禦鎖）"""
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="找不到該空間")
        
    if payload.new_parent_id:
        target_parent = db.query(Location).filter(Location.id == payload.new_parent_id).first()
        if not target_parent:
            raise HTTPException(status_code=400, detail="目標父空間不存在")
            
        if check_cyclical_location(db, location_id, payload.new_parent_id):
            raise HTTPException(
                status_code=400, 
                detail="核心防禦：不能將空間移至自身或其子空間旗下，這會引發無限死循環！"
            )
            
    loc.parent_id = payload.new_parent_id
    db.commit()
    db.refresh(loc)
    return {"status": "moved_successfully", "id": loc.id, "new_parent_id": loc.parent_id}

@router.get("/tree-view")
def get_location_tree_with_objects(db: Session = Depends(get_db)):
    """
    【全景檢索】獲取完整的空間樹狀結構，並將每個空間底下的物資直接嵌套進去
    適合前端用來渲染完整的儲物樹狀圖目錄
    """
    import json
    from core.models import CoreObject

    # 1. 一口氣撈出所有空間與所有物件（降低資料庫 I/O 次數）
    all_locations = db.query(Location).all()
    all_objects = db.query(CoreObject).all()

    # 2. 將物件依照 location_id 進行分組
    objects_by_loc = {}
    for obj in all_objects:
        loc_id = obj.location_id
        if loc_id not in objects_by_loc:
            objects_by_loc[loc_id] = []
        objects_by_loc[loc_id].append({
            "id": obj.id,
            "name": obj.name,
            "template_type": obj.template_type,
            "extra_data": json.loads(obj.extra_data)
        })

    # 3. 建立空間節點對照表
    tree_nodes = {}
    for loc in all_locations:
        tree_nodes[loc.id] = {
            "id": loc.id,
            "name": loc.name,
            "parent_id": loc.parent_id,
            "sub_locations": [],
            "items": objects_by_loc.get(loc.id, [])  # 直接把物資塞進對應的空間
        }

    # 4. 根據 parent_id 組合樹狀圖
    root_nodes = []
    for loc_id, node in tree_nodes.items():
        p_id = node["parent_id"]
        if p_id is None:
            # 沒有父空間，代表是最頂層（如: Garage, Basement）
            root_nodes.append(node)
        else:
            # 塞進父空間的 sub_locations 陣列中
            if p_id in tree_nodes:
                tree_nodes[p_id]["sub_locations"].append(node)

    return {"tree": root_nodes}