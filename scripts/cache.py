import json
import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")

TTL_CATALOG = 7 * 24 * 3600
TTL_RACE = 24 * 3600
TTL_YEAR = 24 * 3600

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

MAX_RETRIES_429 = 4


def cache_path(entity, key):
    return os.path.join(CACHE_DIR, entity, f"{key}.json")


def save_cache(entity, key, data):
    path = cache_path(entity, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {"timestamp": time.time(), "data": data}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        logger.debug("Cache guardado: %s/%s", entity, key)
    except OSError as e:
        logger.warning("Error guardando cache %s/%s: %s", entity, key, e)


def load_cache(entity, key):
    path = cache_path(entity, key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = json.load(f)
        if isinstance(content, dict) and "data" in content:
            return content["data"]
        return content
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Cache corrupto %s/%s: %s", entity, key, e)
        return None


def is_cache_fresh(entity, key, ttl=None):
    if ttl is None:
        ttl = TTL_RACE
    path = cache_path(entity, key)
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = json.load(f)
        ts = content.get("timestamp", 0) if isinstance(content, dict) else 0
        return (time.time() - ts) < ttl
    except (json.JSONDecodeError, OSError):
        return False


def clear_cache(entity=None):
    target = os.path.join(CACHE_DIR, entity) if entity else CACHE_DIR
    if os.path.exists(target):
        import shutil
        shutil.rmtree(target)
        logger.info("Cache eliminado: %s", target)


def fetch_with_retry(url, max_retries=MAX_RETRIES_429, extra_headers=None):
    headers = dict(DEFAULT_HEADERS)
    if extra_headers:
        headers.update(extra_headers)

    for intento in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=30)
        except requests.exceptions.RequestException as e:
            logger.warning("Error de red en intento %d/%d para %s: %s", intento, max_retries, url, e)
            if intento < max_retries:
                time.sleep(10)
            continue

        if response.status_code == 200:
            return response

        if response.status_code == 429:
            wait = min(30 * (2 ** (intento - 1)), 120)
            logger.warning("Bloqueo 429 intento %d/%d. Esperando %ds... (%s)", intento, max_retries, wait, url)
            time.sleep(wait)
            continue

        logger.warning("Error HTTP %d en intento %d/%d: %s", response.status_code, intento, max_retries, url)
        if intento < max_retries:
            time.sleep(10)

    logger.error("Agotados %d reintentos para %s", max_retries, url)
    return None


def fetch_or_cache(url, entity, key, ttl=None):
    if is_cache_fresh(entity, key, ttl):
        logger.debug("Cache hit: %s/%s", entity, key)
        return load_cache(entity, key)

    response = fetch_with_retry(url)
    if response is None:
        return load_cache(entity, key)

    try:
        data = response.json()
    except ValueError:
        logger.warning("JSON invalido de %s", url)
        return load_cache(entity, key)

    save_cache(entity, key, data)
    return data
