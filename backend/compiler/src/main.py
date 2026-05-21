from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router import latex

app = FastAPI(title="DocLib Compiler Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(latex.router, prefix="/api/compile/latex", tags=["LaTeX"])

@app.on_event("startup")
async def startup_event():
    logger.info("Compiler Service started")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "compiler"}
