FUNCTION_IDS = {
    "get_announcements": ["NTF-01"],
    "mark_as_read": ["NTF-02"],
    "mark_all_as_read": ["NTF-02"],
    "get_settings": ["NTF-03"],
    "update_settings": ["NTF-03"],
}


def apply_function_ids(app):
    for route in app.routes:
        endpoint = getattr(route, "endpoint", None)
        function_ids = FUNCTION_IDS.get(getattr(endpoint, "__name__", ""))
        if not function_ids:
            continue
        route.openapi_extra = {
            **(getattr(route, "openapi_extra", None) or {}),
            "x-function-ids": function_ids,
        }
