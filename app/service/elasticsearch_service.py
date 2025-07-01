from elasticsearch import AsyncElasticsearch
import os

es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
es = AsyncElasticsearch(hosts=[es_url])

async def index_item(item):
    await es.index(index="items", id=item.id, document={
        "title": item.title,
        "description": item.description,
        "price": item.price,
        "owner_id": item.owner_id
    })

async def search_items(query: str):
    response = await es.search(index="items", query={
        "multi_match": {
            "query": query,
            "fields": ["title", "description"]
        }
    })
    return response["hits"]["hits"]
