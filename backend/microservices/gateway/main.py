from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import logging

app = FastAPI(title="DocLib API Gateway")

SERVICES = {
    "auth": "http://localhost:8001",
    "profile": "http://localhost:8002",
    "wallet": "http://localhost:8003",
    "document": "http://localhost:8004",
    "social": "http://localhost:8005",
    "inference": "http://localhost:8006",
}

ROUTE_MAP = {
    "/xac-thuc": SERVICES["auth"],
    "/ho-so": SERVICES["profile"],
    "/vi-tien": SERVICES["wallet"],
    "/thanh-toan": SERVICES["wallet"],
    "/rut-tien": SERVICES["wallet"],
    "/tai-lieu": SERVICES["document"],
    "/soan-thao": SERVICES["document"],
    "/bien-dich": SERVICES["document"],
    "/ban-nhap": SERVICES["document"],
    "/cong-dong": SERVICES["social"],
    "/cau-chuyen": SERVICES["social"],
    "/suy-luan": SERVICES["inference"],
}

@app.middleware("http")
async def proxy_middleware(request: Request, call_next):
    path = request.url.path

    target_service = None
    for prefix, service_url in ROUTE_MAP.items():
        if path.startswith(prefix):
            target_service = service_url
            break
            
    if not target_service:
        return await call_next(request)
        
    async with httpx.AsyncClient() as client:
        url = f"{target_service}{path}"
        if request.query_params:
            url += f"?{request.query_params}"
            
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=dict(request.headers),
                content=await request.body(),
                timeout=60.0
            )
            
            content = resp.content
            try:
                json_content = resp.json()
                return JSONResponse(
                    status_code=resp.status_code,
                    content=json_content,
                    headers=dict(resp.headers)
                )
            except:
                return JSONResponse(
                    status_code=resp.status_code,
                    content=content.decode('utf-8') if content else "",
                    headers=dict(resp.headers)
                )
        except Exception as e:
            logging.error(f"Gateway Proxy Error: {str(e)}")
            return JSONResponse(
                status_code=502,
                content={"message": "Dịch vụ đích không phản hồi", "detail": str(e)}
            )

@app.get("/health")
async def health():
    return {"status": "gateway_running"}
