from fastapi import APIRouter, Depends
from src.knowledge.core.dependency import verify_internal_token
from src.knowledge.core.response import APIResponse
from src.knowledge.schemas.embedding import (
    EmbedQueryRequest,
    EmbedBatchRequest,
    EmbeddingResponse,
    BatchEmbeddingResponse,
)
from src.knowledge.services.embedding import embedder

router = APIRouter(dependencies=[Depends(verify_internal_token)])


@router.post("/query", response_model=APIResponse[EmbeddingResponse], description="Tạo embedding cho một truy vấn knowledge")
async def embed_single_query(req: EmbedQueryRequest):
    emb = await embedder.embed_query(req.text)
    return APIResponse(
        data=EmbeddingResponse(embedding=emb), message="Trích xuất vector embedding thành công"
    )


@router.post("/batch", response_model=APIResponse[BatchEmbeddingResponse], description="Tạo embedding theo lô cho knowledge")
async def embed_batch_texts(req: EmbedBatchRequest):
    embs = await embedder.embed_batch(req.texts)
    return APIResponse(
        data=BatchEmbeddingResponse(embeddings=embs, count=len(embs)),
        message="Trích xuất hàng loạt vector embedding thành công",
    )
