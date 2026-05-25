from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from app.core.config import settings
from app.core.database import get_db

app = FastAPI(title="EstimateIQ")


@app.get("/test-connections")
def test_connections(db: Session = Depends(get_db)):
    results = {
        "postgres_status": "Failed",
        "qdrant_status": "Failed",
        "details": {}
    }

    # 1. TEST POSTGRESQL CONNECTION
    try:
        version = db.execute(text("SELECT version();")).scalar()
        results["postgres_status"] = "Success"
        results["details"]["postgres_version"] = version
    except Exception as e:
        results["details"]["postgres_error"] = str(e)

    # 2. TEST QDRANT CONNECTION
    try:
        client = QdrantClient(
            host="qdrant",
            port=settings.qdrant_port_http,
            api_key=settings.qdrant_api_key,
            https=False
        )
        collections = client.get_collections()
        results["qdrant_status"] = "Success"
        results["details"]["qdrant_collections_count"] = len(collections.collections)
    except UnexpectedResponse as ur:
        results["details"]["qdrant_error"] = f"Auth error: {ur.status_code} - {ur.reason_phrase}"
    except Exception as e:
        results["details"]["qdrant_error"] = str(e)

    if results["postgres_status"] == "Failed" or results["qdrant_status"] == "Failed":
        raise HTTPException(status_code=500, detail=results)

    return {
        "status": "All systems operational!",
        "data": results
    }
