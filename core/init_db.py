from core.database import engine, Base, SessionLocal
from core.models import Location

def init_db():
    # 強迫建立所有繼承 Base 的資料表
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        if db.query(Location).count() == 0:
            print("🌱 StockAssure A new database has been detected \n  example data for a pre-defined space is being implanted...")
            garage = Location(name="Garage")
            basement = Location(name="Basement")
            db.add(garage)
            db.add(basement)
            db.commit()
            print("✅ Example data implanted successfully !")
        else:
            print("🗄️ database already exists \n skip the seed data implantation...")
    except Exception as e:
        print(f"❌ Fale to Initialise Data Base: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
