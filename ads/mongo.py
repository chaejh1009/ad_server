from functools import lru_cache
from django.conf import settings
from pymongo import MongoClient


@lru_cache(maxsize=1)
def get_client():
    # 한 서버 프로세스 안에서 연결 풀을 재사용한다.
    return MongoClient(
        settings.MONGO_URI,
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
    )

def get_db():
    return get_client()[settings.MONGO_DB]