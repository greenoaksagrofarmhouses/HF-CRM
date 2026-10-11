from django.conf import settings


def brand(request):
    return {
        "brand": {
            "name": settings.BRAND_NAME,
            "wordmark": settings.BRAND_WORDMARK,
            "subtitle": settings.BRAND_SUBTITLE,
        }
    }
