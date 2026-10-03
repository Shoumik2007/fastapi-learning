from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from database import Base, engine, SessionLocal

app = FastAPI()

def compute_hotspot_temp(load, rated_power, ambient=30,
                          delta_oil_rated=45, delta_hs_rated=23,
                          R=5, x=0.8, y=1.6):
    K = load / rated_power
    delta_oil = delta_oil_rated * ((1 + R * K**2) / (1 + R)) ** x
    delta_hs = delta_hs_rated * K ** y
    return ambient + delta_oil + delta_hs


def ageing_rate(hotspot_temp, reference_temp=98):
    return 2 ** ((hotspot_temp - reference_temp) / 6)

def assess_health(load, rated_power):
    hst = compute_hotspot_temp(load, rated_power)
    rate = ageing_rate(hst)

    if hst < 98:
        label = "Normal"
    elif hst < 120:
        label = "Elevated"
    else:
        label = "Critical"

    return hst, rate, label

## pydantic model


    
class MeasurementCreate(BaseModel):
    asset_id: int
    voltage: int
    current: int
    temperature: int
    load: int

class AssetCreate(BaseModel):
    name: str
    asset_type: str
    rated_power: int
    voltage: str
    location: str
    status: str
    installation_year: int

class AssetResponse(BaseModel):
    id: int
    name: str
    asset_type: str
    rated_power: int
    voltage: str
    location: str
    status: str
    installation_year: int

    model_config = ConfigDict(from_attributes=True)
    
class MeasurementResponse(BaseModel):
    id: int
    asset_id: int
    voltage: int
    current: int
    temperature: int
    load: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AssetHealthResponse(BaseModel):
    asset_id: int
    asset_name: str
    measured_temperature: int
    computed_hotspot_temp: float
    ageing_rate: float
    health: str
    model_config = ConfigDict(from_attributes=True)

class MaintenanceCreate(BaseModel):
    asset_id: int
    description: str
    technician: str
    status: str

class MaintenanceResponse(BaseModel):
    id: int
    asset_id: int
    description: str
    technician: str
    status: str
    maintenance_date: datetime

    model_config = ConfigDict(from_attributes=True)

class AssetStatusResponse(BaseModel):
    asset_id: int
    asset_name: str
    status: str
    health: str
    latest_temperature: int
    computed_hotspot_temp: float
    ageing_rate: float
    latest_load: int
    last_measurement: datetime

    model_config = ConfigDict(from_attributes=True)

##SQAlchemy model


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    asset_type = Column(String)
    rated_power = Column(Integer)
    voltage = Column(String)
    location = Column(String)
    status = Column(String)
    installation_year = Column(Integer)
    measurements = relationship("Measurement", backref="asset")
    maintenance_records = relationship("Maintenance", backref="asset")

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer,ForeignKey("assets.id"))
    voltage = Column(Integer)
    current = Column(Integer)
    temperature = Column(Integer)
    load = Column(Integer)
    recorded_at = Column(DateTime, default=datetime.utcnow)

class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    description = Column(String)
    technician = Column(String)
    status = Column(String)
    maintenance_date = Column(DateTime, default=datetime.utcnow)
    
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.post("/assets",response_model=AssetResponse)
def create_asset(asset: AssetCreate, db=Depends(get_db)):
    db_asset = Asset(
        name=asset.name,
        asset_type=asset.asset_type,
        rated_power=asset.rated_power,
        voltage=asset.voltage,
        location=asset.location,
        status=asset.status,
        installation_year=asset.installation_year
    )

    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)

    return db_asset

@app.post("/measurements", response_model=MeasurementResponse)
def create_measurement(measurement: MeasurementCreate, db=Depends(get_db)):
    db_measurement = Measurement(
        asset_id=measurement.asset_id,
        voltage=measurement.voltage,
        current=measurement.current,
        temperature=measurement.temperature,
        load=measurement.load
    )

    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)

    return db_measurement

@app.post("/maintenance", response_model=MaintenanceResponse)
def create_maintenance(
    maintenance: MaintenanceCreate,
    db=Depends(get_db)
):
    db_maintenance = Maintenance(
        asset_id=maintenance.asset_id,
        description=maintenance.description,
        technician=maintenance.technician,
        status=maintenance.status
    )

    db.add(db_maintenance)
    db.commit()
    db.refresh(db_maintenance)

    return db_maintenance

 

@app.get("/assets", response_model=list[AssetResponse])
def get_assets(db=Depends(get_db)):
    return db.query(Asset).all()




@app.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db=Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    return asset

@app.get("/assets/{asset_id}/measurements", response_model=list[MeasurementResponse])
def get_asset_measurements(asset_id: int, db=Depends(get_db)):
    measurements = (
        db.query(Measurement)
        .filter(Measurement.asset_id == asset_id)
        .order_by(Measurement.recorded_at.desc())
        .all()
    )

    return measurements

@app.get("/assets/{asset_id}/health", response_model=AssetHealthResponse)
def get_asset_health(asset_id: int, db=Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    measurement = (
        db.query(Measurement)
        .filter(Measurement.asset_id == asset_id)
        .order_by(Measurement.id.desc())
        .first()
    )
    if measurement is None:
        raise HTTPException(status_code=404, detail="No measurements available")

    hst, rate, health = assess_health(measurement.load, asset.rated_power)

    return {
        "asset_id": asset_id,
        "asset_name": asset.name,
        "measured_temperature": measurement.temperature,
        "computed_hotspot_temp": round(hst, 2),
        "ageing_rate": round(rate, 3),
        "health": health
    }
 
@app.get("/assets/{asset_id}/maintenance",response_model=list[MaintenanceResponse])
def get_asset_maintenance(asset_id: int, db=Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    maintenance_records = (
        db.query(Maintenance)
        .filter(Maintenance.asset_id == asset_id)
        .order_by(Maintenance.maintenance_date.desc())
        .all()
    )

    return maintenance_records

@app.get("/assets/{asset_id}/status", response_model=AssetStatusResponse)
def get_asset_status(asset_id: int, db=Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    measurement = (
        db.query(Measurement)
        .filter(Measurement.asset_id == asset_id)
        .order_by(Measurement.recorded_at.desc())
        .first()
    )
    if measurement is None:
        raise HTTPException(status_code=404, detail="No measurements available")

    hst, rate, health = assess_health(measurement.load, asset.rated_power)

    return {
        "asset_id": asset.id,
        "asset_name": asset.name,
        "status": asset.status,
        "health": health,
        "latest_temperature": measurement.temperature,
        "computed_hotspot_temp": round(hst, 2),
        "ageing_rate": round(rate, 3),
        "latest_load": measurement.load,
        "last_measurement": measurement.recorded_at
    }


@app.put("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: int, asset: AssetCreate, db=Depends(get_db)):
    db_asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    db_asset.name = asset.name
    db_asset.asset_type = asset.asset_type
    db_asset.rated_power = asset.rated_power
    db_asset.voltage = asset.voltage
    db_asset.location = asset.location
    db_asset.status = asset.status
    db_asset.installation_year = asset.installation_year

    db.commit()
    db.refresh(db_asset)

    return db_asset

@app.get("/assets/{asset_id}/health-history")
def get_asset_health_history(asset_id: int, db=Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    measurements = (
        db.query(Measurement)
        .filter(Measurement.asset_id == asset_id)
        .order_by(Measurement.recorded_at.asc())
        .all()
    )

    results = []
    for m in measurements:
        hst, rate, health = assess_health(m.load, asset.rated_power)
        results.append({
            "recorded_at": m.recorded_at,
            "load": m.load,
            "computed_hotspot_temp": round(hst, 2),
            "ageing_rate": round(rate, 3),
            "health": health
        })
    return results




@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, db=Depends(get_db)):
    db_asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    db.delete(db_asset)
    db.commit()

    return {"message": "Asset deleted successfully"}