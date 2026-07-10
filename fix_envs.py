import re

def fix_local_env():
    with open(".env", "r") as f:
        content = f.read()
    
    # Fix URLs
    urls = {
        "INTERNAL_API_URL": "http://traefik:8000",
        "AUTHENTICATION_URL": "http://authentication:8001",
        "HUMANITY_URL": "http://humanity:8002",
        "MANAGEMENT_URL": "http://management:8003",
        "CONTENT_URL": "http://content:8004",
        "COLLECTION_URL": "http://collection:8005",
        "FINANCE_URL": "http://finance:8006",
        "NOTIFICATION_URL": "http://notification:8007",
        "AGENTIC_AI_URL": "http://agentic_ai:8008",
        "MESSAGING_URL": "http://messaging:8009",
        "WEBSOCKET_URL": "ws://websocket:8010",
        "COMPILATION_URL": "http://compilation:8011",
        "CLOUD_URL": "http://cloud:8012",
        "DRM_URL": "http://drm:8013",
        "USAGE_URL": "http://usage:8014",
    }
    
    for key, val in urls.items():
        if f"{key}=" in content:
            content = re.sub(rf"{key}=.*", f"{key}={val}", content)
        else:
            # Append if not exists
            content += f"\n{key}={val}"
            
    with open(".env", "w") as f:
        f.write(content)

def fix_k8s_env():
    with open("k8s/.env", "r") as f:
        content = f.read()
    
    content = content.replace("PAYMENT_URL=", "FINANCE_URL=")
    content = content.replace("AGENTIC_REDIS_URI=", "INTELLIGENCE_REDIS_URI=")
    content = content.replace("PAYOS_API_URL=\n", "PAYOS_API_URL=https://api-merchant.payos.vn/v2/payment-requests\n")
    
    # K8s URLs don't need ports because they use the service default port 80
    urls = {
        "API_URL": "http://traefik",
        "SHARED_URL": "http://traefik",
        "AUTHENTICATION_URL": "http://authentication",
        "HUMANITY_URL": "http://humanity",
        "MANAGEMENT_URL": "http://management",
        "CONTENT_URL": "http://content",
        "COLLECTION_URL": "http://collection",
        "FINANCE_URL": "http://finance",
        "NOTIFICATION_URL": "http://notification",
        "AGENTIC_AI_URL": "http://agentic-ai",
        "MESSAGING_URL": "http://messaging",
        "WEBSOCKET_URL": "ws://websocket",
        "COMPILATION_URL": "http://compilation",
        "CLOUD_URL": "http://cloud",
        "DRM_URL": "http://drm",
        "USAGE_URL": "http://usage",
    }
    
    for key, val in urls.items():
        if f"{key}=" in content:
            content = re.sub(rf"{key}=.*", f"{key}={val}", content)
        else:
            content += f"\n{key}={val}"
            
    with open("k8s/.env", "w") as f:
        f.write(content)

fix_local_env()
fix_k8s_env()
