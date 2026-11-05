from cachetools import TTLCache

admin_cache = TTLCache(maxsize=1024, ttl=300)
total_switch_cache = TTLCache(maxsize=1, ttl=300)
group_cache = TTLCache(maxsize=1024, ttl=300)
block_cache = TTLCache(maxsize=1024, ttl=300)
min_price_cache = TTLCache(maxsize=1024, ttl=300)
random_reply_cache = TTLCache(maxsize=1024, ttl=300)
delay_cache = TTLCache(maxsize=1024, ttl=300)
goods_cache = TTLCache(maxsize=2048, ttl=300)


def invalidate_admin_cache(bot_qq: str, admin_qq: str) -> None:
    admin_cache.pop(f"{bot_qq}:{admin_qq}", None)


def invalidate_total_switch_cache() -> None:
    total_switch_cache.clear()


def invalidate_group_cache(bot_qq: str, group_id: str) -> None:
    group_cache.pop(f"{bot_qq}:{group_id}", None)


def invalidate_block_cache(bot_qq: str, user_qq: str) -> None:
    block_cache.pop(f"{bot_qq}:{user_qq}", None)


def invalidate_min_price_cache(bot_qq: str, group_id: str) -> None:
    min_price_cache.pop(f"{bot_qq}:{group_id}", None)


def invalidate_random_reply_cache(bot_qq: str, group_id: str) -> None:
    random_reply_cache.pop(f"{bot_qq}:{group_id}", None)


def invalidate_delay_cache(bot_qq: str, group_id: str) -> None:
    delay_cache.pop(f"{bot_qq}:{group_id}", None)


def invalidate_goods_cache(bot_qq: str, goods_type: str, normalized_code: str) -> None:
    goods_cache.pop(f"{bot_qq}:{goods_type}:{normalized_code}", None)


def invalidate_all_goods_cache(bot_qq: str) -> None:
    prefix = f"{bot_qq}:"
    for key in [k for k in goods_cache.keys() if k.startswith(prefix)]:
        goods_cache.pop(key, None)
