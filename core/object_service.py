import json
from sqlalchemy.orm import Session
from fastapi import HTTPException
from jsonschema import Draft7Validator, validators
from core.models import CoreObject, Location
from core.plugin_loader import GLOBAL_TEMPLATES

def extend_with_default(validator_class):
    """
    黑科技擴充：讓 jsonschema 驗證器在驗證的同時，
    如果發現有欄位沒填但 Schema 有寫 'default'，就自動把預設值寫入資料中！
    """
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema and property not in instance:
                instance[property] = subschema["default"]
        for error in validate_properties(validator, properties, instance, schema):
            yield error

    return validators.extend(validator_class, {"properties": set_defaults})

# 建立一個會自動填補預設值的特殊驗證器
DefaultValidatingDraft7Validator = extend_with_default(Draft7Validator)


def create_object(db: Session, name: str, location_id: int, template_type: str, raw_extra_data: dict):
    # 1. 檢查目標空間是否存在
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=400, detail="指定的儲存空間不存在")

    # 2. 檢查外掛模板是否存在於記憶體中
    if template_type not in GLOBAL_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"系統未載入名為 [{template_type}] 的外掛模板")

    schema = GLOBAL_TEMPLATES[template_type]
    
    # 複製一份資料放入校驗器，避免污染原始輸入
    validated_extra_data = dict(raw_extra_data)

    # 3. 啟動強校驗與動態補全
    try:
        validator = DefaultValidatingDraft7Validator(schema)
        errors = sorted(validator.iter_errors(validated_extra_data), key=lambda e: e.path)
        
        if errors:
            error_messages = [f"[{'.'.join(str(v) for v in e.path)}]: {e.message}" for e in errors]
            raise HTTPException(status_code=400, detail={"error": "外掛 Schema 校驗失敗", "details": error_messages})
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"校驗引擎發生未知錯誤: {str(e)}")

    # 4. 校驗通過且預設值補全後，將 dict 轉為 JSON 字串存入 SQLite
    new_obj = CoreObject(
        name=name,
        location_id=location_id,
        template_type=template_type,
        extra_data=json.dumps(validated_extra_data, ensure_ascii=False)
    )
    
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj