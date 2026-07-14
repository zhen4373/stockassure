import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Optional, List
from core.database import get_db
from core.models import CoreObject, Location
from core.plugin_loader import GLOBAL_TEMPLATES
import jsonschema

router = APIRouter(prefix="/api/objects", tags=["物資管理"])

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

# --- 智慧型 JSON Schema 校驗器（支援自動回填 default 值） ---
def get_validated_extra_data(template_type: str, raw_data: dict) -> str:
    if template_type not in GLOBAL_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"找不到指定的外掛模板: {template_type}")
    
    schema = GLOBAL_TEMPLATES[template_type].get("schema", {})
    
    # 建立一個能在校驗過程中自動補全預設值的 Validator
    def extend_with_default(validator_class):
        validate_properties = validator_class.VALIDATORS["properties"]

        def set_defaults(validator, properties, instance, schema):
            for property, subschema in properties.items():
                if "default" in subschema:
                    instance.setdefault(property, subschema["default"])
            for error in validate_properties(validator, properties, instance, schema):
                yield error

        return jsonschema.validators.extend(validator_class, {"properties": set_defaults})

    DefaultValidatingDraft7Validator = extend_with_default(jsonschema.Draft7Validator)
    
    data_copy = raw_data.copy()
    try:
        DefaultValidatingDraft7Validator(schema).validate(data_copy)
    except jsonschema.ValidationError as e:
        raise HTTPException(status_code=422, detail={"error": "外掛 Schema 校驗失敗", "message": e.message})
    
    # 🔴 Bug 1 修正：統一序列化為字串寫入資料庫
    return json.dumps(data_copy, ensure_ascii=False)


# --- 1. 新增物資 (POST) ---
@router.post("/")
def create_object(payload: ObjectCreateSchema, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == payload.location_id).first()
    if not loc:
        raise HTTPException(status_code=400, detail="指定的儲物空間不存在")

    # 🟠 Bug 3 修正：透過校驗器自動補全預設值並轉字串
    serialized_data = get_validated_extra_data(payload.template_type, payload.extra_data)

    db_obj = CoreObject(
        name=payload.name,
        location_id=payload.location_id,
        template_type=payload.template_type,
        extra_data=serialized_data
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
        # 🔴 Bug 2 修正：安全解碼 JSON 文字，若失敗則退回空字典
        parsed_extra_data = {}
        if obj.extra_data:
            try:
                parsed_extra_data = json.loads(obj.extra_data) if isinstance(obj.extra_data, str) else obj.extra_data
            except Exception:
                parsed_extra_data = {}

        result.append({
            "id": obj.id,
            "name": obj.name,
            "location_id": obj.location_id,
            "template_type": obj.template_type,
            "extra_data": parsed_extra_data
        })
        
    return {"location_id": location_id, "objects": result}


# --- 3. 修改/編輯物資 (PUT) ---
@router.put("/{object_id}")
def update_object(object_id: str, payload: ObjectUpdateSchema, db: Session = Depends(get_db)):
    obj = db.query(CoreObject).filter(CoreObject.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="找不到該物品")

    loc = db.query(Location).filter(Location.id == payload.location_id).first()
    if not loc:
        raise HTTPException(status_code=400, detail="指定的儲物空間不存在")

    # 🟠 Bug 3 修正：編輯時也採用相同的預設值回填與序列化邏輯
    serialized_data = get_validated_extra_data(payload.template_type, payload.extra_data)

    obj.name = payload.name
    obj.location_id = payload.location_id
    obj.template_type = payload.template_type
    obj.extra_data = serialized_data

    db.commit()
    db.refresh(obj)
    return {"status": "success", "message": "物品更新成功"}


# --- 4. 刪除物資 (DELETE) ---
@router.delete("/{object_id}")
def delete_object(object_id: str, db: Session = Depends(get_db)):
    obj = db.query(CoreObject).filter(CoreObject.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="找不到該物品")
    
    db.delete(obj)
    db.commit()
    return {"status": "success", "message": "物品已成功刪除"}