import uuid
try:
    import uuid6
    print("uuid6 dir:", dir(uuid6))
except ImportError:
    print("uuid6 not found")
