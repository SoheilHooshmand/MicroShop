from django.core.cache import cache


PRODUCT_CACHE_TTL = 60 * 10
CATEGORY_CACHE_TTL = 60 * 10


def product_cache_key(product_id):
    return f"catalog:product:{product_id}"


def category_cache_key(category_id):
    return f"catalog:category:{category_id}"


def product_list_cache_key(query_string=""):
    return f"catalog:products:list:{query_string}"


def category_list_cache_key(query_string=""):
    return f"catalog:categories:list:{query_string}"


def invalidate_product_cache(product_id=None):
    if product_id is not None:
        cache.delete(product_cache_key(product_id))

    cache.delete_pattern("catalog:products:list:*")


def invalidate_category_cache(category_id=None):
    if category_id is not None:
        cache.delete(category_cache_key(category_id))

    cache.delete_pattern("catalog:categories:list:*")


def invalidate_all_catalog_cache():
    cache.delete_pattern("catalog:*")