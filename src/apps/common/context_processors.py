from django.conf import settings


def global_flags(_request):
    return {
        "APP_PUBLIC_URL": settings.APP_PUBLIC_URL,
        "PROJECT_NAME": settings.PROJECT_NAME,
        "SEARCH_STEP_TIMEOUT_SECONDS": settings.SEARCH_STEP_TIMEOUT_SECONDS,
        "PROFILE_VIEW_WINDOW_SECONDS": settings.PROFILE_VIEW_WINDOW_SECONDS,
    }
