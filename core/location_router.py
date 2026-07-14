from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from core.database import get_db
from core.models import Location, CoreObject

router = APIRouter(prefix="/api/locations", tags=["Locations"])

class LocationCreateSchema(BaseModel):
    name: str
    parent_id: Optional[int] = None

class LocationUpdateSchema(BaseModel):
    name: str
    parent_id: Optional[int] = None

@router.post("/")
def create_location(payload: LocationCreateSchema, db: Session = Depends(get_db)):
    if payload.parent_id is not None:
        parent = db.query(Location).filter(Location.id == payload.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="指定的父級空間不存在")
            
    new_loc = Location(name=payload.name, parent_id=payload.parent_id)
    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)
    return {"status": "success", "id": new_loc.id, "name": new_loc.name}

# 🌟 新增：更新儲物空間接口 (支援改名、遷移樹狀分支，防循環掛載)
@router.put("/{location_id}")
def update_location(location_id: int, payload: LocationUpdateSchema, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="找不到該儲物空間")
    
    if payload.parent_id is not None:
        # 防禦機制 1：不能把自己設為自己的父空間
        if payload.parent_id == location_id:
            raise HTTPException(status_code=400, detail="儲物空間不能將自己設為父級空間")
        
        # 防禦機制 2：不能把父空間移到自己的子空間結構內 (防止孤兒環狀鏈)
        all_locations = db.query(Location).all()
        def is_descendant(parent_id, child_id):
            # 檢查 child_id 是否為 parent_id 的子孫
            current = next((l for l in all_locations if l.id == child_id), None)
            while current and current.parent_id is not None:
                if current.parent_id == parent_id:
                    return True
                current = next((l for l in all_locations if l.id == current.parent_id), None)
            return False
        
        if is_descendant(location_id, payload.parent_id):
            raise HTTPException(status_code=400, detail="不能將空間移動到它自己的子空間底下")
            
        parent = db.query(Location).filter(Location.id == payload.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="指定的父級空間不存在")

    loc.name = payload.name
    loc.parent_id = payload.parent_id
    db.commit()
    return {"status": "success", "message": "空間更新成功"}

@router.get("/tree-view")
def get_location_tree(db: Session = Depends(get_db)):
    all_locs = db.query(Location).all()
    
    # 建立節點物件，前端期待的欄位包含 `children` 與 `object_count`
    loc_dict = {loc.id: {
        "id": loc.id,
        "name": loc.name,
        "parent_id": loc.parent_id,
        "children": [],
        "object_count": len(loc.objects or [])
    } for loc in all_locs}
    
    root_locations = []
    for loc_id, loc_node in loc_dict.items():
        p_id = loc_node["parent_id"]
        if p_id is None:
            root_locations.append(loc_node)
        else:
            if p_id in loc_dict:
                loc_dict[p_id]["children"].append(loc_node)
                
    # 直接回傳陣列以符合前端預期的 JSON 結構（前端以 array 操作）
    return root_locations


@router.delete("/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="找不到該儲物空間")

    # 若已有子空間或底下有物品，不允許刪除
    child_count = db.query(Location).filter(Location.parent_id == location_id).count()
    if child_count > 0:
        raise HTTPException(status_code=400, detail="此空間底下仍有子空間，請先移除或轉移子空間")

    obj_count = db.query(CoreObject).filter(CoreObject.location_id == location_id).count()
    if obj_count > 0:
        raise HTTPException(status_code=400, detail="此空間底下仍有物資，請先刪除或移動物資")

    db.delete(loc)
    db.commit()
    return {"status": "success", "message": "儲物空間已刪除"}