from src.services.session import SessionService


def set_refresh_cookie(response, request, token_data):
    refresh_token = token_data.pop("_refresh_token")
    response.set_cookie(
        key="veriq_refresh_token",
        value=refresh_token,
        max_age=SessionService.refresh_cookie_seconds(),
        httponly=True,
        secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https",
        samesite="lax",
        path="/",
    )
    return token_data
