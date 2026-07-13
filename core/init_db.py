from core.database import engine, Base, SessionLocal
from core.models import Location

def init_db():
    # 強迫建立所有繼承 Base 的資料表
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        if db.query(Location).count() == 0:
            print("🌱 StockAssure 偵測到全新資料庫，正在植入預設空間種子資料...")
            garage = Location(name="Garage (車庫)")
            basement = Location(name="Basement (地下室)")
            db.add(garage)
            db.add(basement)
            db.commit()
            print("✅ 種子資料植入成功！")
        else:
            print("🗄️ 資料庫已存在，跳過種子資料植入。")
    except Exception as e:
        print(f"❌ 初始化資料庫失敗: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()