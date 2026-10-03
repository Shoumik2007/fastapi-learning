# Industrial Asset Management API

A FastAPI-based REST API for managing industrial assets, operational measurements, asset health, status, and maintenance records.

## Features

- Asset CRUD operations
- Operational measurement storage
- Measurement history
- Asset health assessment
- Asset status monitoring
- Maintenance records
- SQLite database with SQLAlchemy
- Python API client
- Swagger API documentation

## API Endpoints

### Assets

```text
POST   /assets
GET    /assets
GET    /assets/{asset_id}
PUT    /assets/{asset_id}
DELETE /assets/{asset_id}
```

### Measurements

```text
POST /measurements
GET  /assets/{asset_id}/measurements
```

### Health & Status

```text
GET /assets/{asset_id}/health
GET /assets/{asset_id}/status
```

### Maintenance

```text
POST /maintenance
GET  /assets/{asset_id}/maintenance
```

## Example Asset

```json
{
  "name": "Transformer-01",
  "asset_type": "Distribution Transformer",
  "rated_power": 400,
  "voltage": "11kV/433V",
  "location": "MGIT",
  "status": "Operational",
  "installation_year": 2005
}
```

## Technology Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Requests
- Uvicorn
- REST / JSON

## Project Structure

```text
fastapi-learning/
├── main.py
├── database.py
├── client.py
├── README.md
└── .gitignore
```

## Setup

```bash
pip install fastapi uvicorn sqlalchemy requests
```

Run the API:

```bash
uvicorn main:app --reload
```

API:

http://127.0.0.1:8000

Swagger documentation:

http://127.0.0.1:8000/docs

## Database Relationships

```text
Asset
 ├── Measurements
 └── Maintenance Records
```

One asset can have multiple measurements and maintenance records.

## Learning Outcomes

- REST API development
- FastAPI
- Pydantic validation
- SQLAlchemy ORM
- SQLite databases
- CRUD operations
- Database relationships
- Industrial asset modelling
- Operational data handling
- Basic asset health assessment
- Python API integration

## Future Development

- PostgreSQL
- Alembic migrations
- Authentication
- Real-time measurement ingestion
- Sensor integration
- Predictive maintenance
- Data visualization
- Digital twin integration

## Disclaimer

The health assessment is a simplified learning example and is not intended for real-world transformer diagnosis or safety-critical decisions.

## Author

**Shoumik Gunda**

Electrical and Electronics Engineering  
MGIT, Hyderabad
