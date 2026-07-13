from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Optional, List
from core.database import get_db
from core.models import CoreObject, Location
from core.plugin_loader import GLOBAL_TEMPLATES
import jsonschema

router = APIRouter(prefix="/api/v1/objects", tags=["物資管理"])

# --- Pydantic 請求模型 ---

class ObjectCreateSchema(BaseModel):
    name: str
    location_id: int
    template_type: str
    extra_data: dict

class ObjectUpdateSchema(BaseModel):
    name: str
    location_id: int
    template_type: str
    extra_data: dict


# --- 1. 新增物資 (POST) ---
@router.post("/")
def create_object(payload: ObjectCreateSchema, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == payload.location_id).first()
    if not loc:
        raise HTTPException(status_code=400, detail="指定的儲物空間不存在")

    if payload.template_type not in GLOBAL_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"找不到指定的外掛模板: {payload.template_type}")
    
    plugin_meta = GLOBAL_TEMPLATES[payload.template_type]
    json_schema = plugin_meta.get("schema", {})

    # JSON Schema 強校驗
    try:
        jsonschema.validate(instance=payload.extra_data, schema=json_schema)
    except jsonschema.ValidationError as e:
        raise HTTPException(status_code=422, detail={"error": "外掛 Schema 校驗失敗", "message": e.message})

    # 數據自動補全 (補齊 default 值)
    final_data = payload.extra_data.copy()
    properties = json_schema.get("properties", {})
    for prop_key, prop_val in properties.items():
        if prop_key not in final_data and "default" in prop_val:
            final_data[prop_key] = prop_val["default"]

    db_obj = CoreObject(
        name=payload.name,
        location_id=payload.location_id,
        template_type=payload.template_type,
        extra_data=final_data
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return {"status": "success", "id": db_obj.id, "name": db_obj.name}


# --- 2. 獲取特定空間下的物資清單 (GET) ---
@router.get("/by-location/{location_id}")
def get_objects_by_location(location_id: int, recursive: bool = True, db: Session = Depends(get_db)):
    target_loc = db.query(Location).filter(Location.id == location_id).first()
    if not target_loc:
        raise HTTPException(status_code=404, detail="找不到該儲物空間")

    location_ids = [location_id]

    if recursive:
        all_locations = db.query(Location).all()
        
        def get_sub_ids(parent_id):
            sub_ids = []
            for loc in all_locations:
                if loc.parent_id == parent_id:
                    sub_ids.append(loc.id)
                    sub_ids.extend(get_sub_ids(loc.id))
            return sub_ids
        
        location_ids.extend(get_sub_ids(location_id))

    objects = db.query(CoreObject).filter(CoreObject.location_id.in_(location_ids)).all()
    
    result = []
    for obj in objects:
        result.append({
            "id": obj.id,  # 這裡會正確輸出為 UUID 字串
            "name": obj.name,
            "location_id": obj.location_id,
            "template_type": obj.template_type,
            "extra_data": obj.extra_data if isinstance(obj.extra_data, dict) else {}
        })
        
    return {"location_id": location_id, "objects": result}


# --- 3. 修改/編輯物資 (PUT) 🌟 這裡將物件 ID 修正為 str 接收 UUID ---
@router.put("/{object_id}")
def update_object(object_id: str, payload: ObjectUpdateSchema, db: Session = Depends(get_db)):
    obj = db.query(CoreObject).filter(CoreObject.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="找不到該物品")

    loc = db.query(Location).filter(Location.id == payload.location_id).first()
    if not loc:
        raise HTTPException(status_code=400, detail="指定的儲物空間不存在")

    if payload.template_type not in GLOBAL_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"找不到指定的外掛模板: {payload.template_type}")
    
    plugin_meta = GLOBAL_TEMPLATES[payload.template_type]
    json_schema = plugin_meta.get("schema", {})

    try:
        jsonschema.validate(instance=payload.extra_data, schema=json_schema)
    except jsonschema.ValidationError as e:
        raise HTTPException(status_code=422, detail={"error": "外掛 Schema 校驗失敗", "message": e.message})

    # 更新資料
    obj.name = payload.name
    obj.location_id = payload.location_id
    obj.template_type = payload.template_type
    obj.extra_data = payload.extra_data

    db.commit()
    db.refresh(obj)
    return {"status": "success", "message": "物品更新成功"}


# --- 4. 刪除物資 (DELETE) 🌟 這裡將物件 ID 修正為 str 接收 UUID ---
@router.delete("/{object_id}")
def delete_object(object_id: str, db: Session = Depends(get_db)):
    obj = db.query(CoreObject).filter(CoreObject.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="找不到該物品")
    
    db.delete(obj)
    db.commit()
    return {"status": "success", "message": "物品已成功刪除"}