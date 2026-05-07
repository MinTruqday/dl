import uuid
from typing import List, Dict
from loguru import logger
import os

try:
    from chonkie import SemanticChunker, TokenChunker
    HAS_CHONKIE = True
except ImportError:
    HAS_CHONKIE = False


class AdvancedSemanticChunker:
    def __init__(self):
        logger.info("Initializing Chonkie Chunkers")
        self.chunker = None
        self.type = "fallback"
        
        if HAS_CHONKIE:
            try:
                model_name = os.environ.get("EMBEDDING_MODEL")
                self.chunker = SemanticChunker(
                    embedding_model=model_name,
                    chunk_size=512,
                    similarity_threshold=0.5
                )
                self.type = "chonkie_semantic"
                logger.info(f"Loaded Chonkie SemanticChunker with {model_name}")
            except Exception as e:
                logger.warning(f"Chonkie SemanticChunker failed to load: {e}. Falling back to TokenChunker.")
                try:
                    self.chunker = TokenChunker(chunk_size=512, chunk_overlap=64)
                    self.type = "chonkie_token"
                    logger.info("Loaded Chonkie TokenChunker")
                except Exception as e2:
                    logger.error(f"Chonkie TokenChunker failed: {e2}")

    def chunk_document(self, text: str, metadata: Dict) -> List[Dict]:
        logger.info(f"Chunking text of length {len(text)}")
        
        if not self.chunker:
            logger.warning("Using fallback Langchain CharSplit due to Chonkie initialization error")
            return self._fallback_chunking(text, metadata)

        try:
            chonkie_chunks = self.chunker.chunk(text)
            chunks = []
            
            for i, chunk_obj in enumerate(chonkie_chunks):
                chunk_text = chunk_obj.text.strip()
                if len(chunk_text) < 30: continue
                    
                chunk_id = str(uuid.uuid4())[:12]
                chunk_meta = {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "char_count": len(chunk_text),
                    "word_count": len(chunk_text.split()),
                    "chunk_type": self.type
                }
                
                chunks.append({
                    "id": f"{metadata.get('document_id', 'unknown')}_{chunk_id}",
                    "text": chunk_text,
                    "metadata": chunk_meta
                })
                
            logger.info(f"Chonkie chunking complete. Total chunks: {len(chunks)} ({self.type})")
            return chunks
            
        except Exception as e:
            logger.error(f"Error running Chonkie: {e}. Using fallback.")
            return self._fallback_chunking(text, metadata)

    def _fallback_chunking(self, text: str, metadata: Dict) -> List[Dict]:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
        
        texts = splitter.split_text(text)
        chunks = []
        for i, chunk_text in enumerate(texts):
            if len(chunk_text.strip()) < 30: continue
            chunk_id = str(uuid.uuid4())[:12]
            
            chunks.append({
                "id": f"{metadata.get('document_id', 'unknown')}_{chunk_id}",
                "text": chunk_text.strip(),
                "metadata": {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "chunk_type": "recursive_fallback"
                }
            })
            
        return chunks

chunker = AdvancedSemanticChunker()

