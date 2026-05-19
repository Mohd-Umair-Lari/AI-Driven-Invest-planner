import os
import hashlib
import json
from typing import List, Optional

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

try:
    from loguru import logger
except ImportError:
    import logging as _l; logger = _l.getLogger("embedder")

HF_API_URL  = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
HF_TOKEN    = os.getenv("HF_API_TOKEN", os.getenv("HF_TOKEN", ""))
EMBED_DIM   = 384

_CACHE: dict = {}

def _cache_key(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]

def embed_text(text: str) -> Optional[List[float]]:

    if not text or not text.strip():
        return None
    if not _HAS_REQUESTS:
        logger.warning("requests not installed — embedding disabled")
        return None
    if not HF_TOKEN:
        logger.warning("HF_API_TOKEN not set — embedding disabled")
        return None

    key = _cache_key(text)
    if key in _CACHE:
        return _CACHE[key]

    try:
        response = _requests.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": text[:512], "options": {"wait_for_model": True}},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and isinstance(data[0], list):
            embedding = data[0]
        elif isinstance(data, list) and isinstance(data[0], float):
            embedding = data
        else:
            logger.warning(f"Unexpected embedding shape: {type(data)}")
            return None

        _CACHE[key] = embedding
        return embedding

    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return None

def embed_batch(texts: List[str]) -> List[Optional[List[float]]]:

    results = []
    BATCH = 32
    for i in range(0, len(texts), BATCH):
        chunk = texts[i:i + BATCH]
        batch_results = [embed_text(t) for t in chunk]
        results.extend(batch_results)
    return results

def is_available() -> bool:

    return bool(HF_TOKEN and _HAS_REQUESTS)
