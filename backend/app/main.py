import psycopg2
from fastapi import FastAPI, HTTPException
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from app.core.config import settings

app = FastAPI(title="EstimateIQ Health Check")


@app.get("/test-connections")
def test_database_connections():
    results = {
        "postgres_status": "Failed",
        "qdrant_status": "Failed",
        "details": {}
    }

    # 1. TEST POSTGRESQL CONNECTION
    try:
        conn = psycopg2.connect(
            host="postgres",
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            port=5432  # internal Docker network port
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        cursor.close()
        conn.close()

        results["postgres_status"] = "Success"
        results["details"]["postgres_version"] = db_version[0]
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
        collections_response = client.get_collections()

        results["qdrant_status"] = "Success"
        results["details"]["qdrant_collections_count"] = len(collections_response.collections)
    except UnexpectedResponse as ur:
        results["details"]["qdrant_error"] = f"Authentication/API Error: {ur.status_code} - {ur.reason_phrase}"
    except Exception as e:
        results["details"]["qdrant_error"] = str(e)

    # If either service fails, return a 500 error to indicate an unhealthy stack
    if results["postgres_status"] == "Failed" or results["qdrant_status"] == "Failed":
        raise HTTPException(status_code=500, detail=results)

    return {
        "status": "All systems operational!",
        "data": results
    }
