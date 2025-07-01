from fastapi import APIRouter
from app.redis_client import redis_client
from elasticsearch import AsyncElasticsearch
import os

router = APIRouter()

# Redis test endpoint
@router.get("/health/redis")
async def check_redis():
    try:
        pong = await redis_client.ping()
        return {"status": "connected", "pong": pong}
    except Exception as e:
        return {"status": "error", "details": str(e)}

# Elasticsearch test endpoint
@router.get("/health/elasticsearch")
async def check_elasticsearch():
    es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
    es = AsyncElasticsearch(hosts=[es_url])
    try:
        health = await es.cluster.health()
        return {"status": "connected", "cluster_health": health["status"]}
    except Exception as e:
        return {"status": "error", "details": str(e)}
    finally:
        await es.close()
