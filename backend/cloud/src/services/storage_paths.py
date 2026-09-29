def object_prefixes(owner_id: str) -> tuple[str, ...]:
    return (f"users/{owner_id}/", f"client/{owner_id}/")
