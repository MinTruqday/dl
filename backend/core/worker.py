from loguru import logger
import json
import asyncio
import os
from aio_pika.abc import AbstractIncomingMessage
from core.database import db_client

async def process_tectonic_compile(message: AbstractIncomingMessage):
    async with message.process():
        try:
            payload = json.loads(message.body.decode("utf-8"))
            document_id = payload.get("document_id")
            content_raw = payload.get("content_raw")
            author_id = payload.get("author_id", None)
            
            if not document_id or ".." in str(document_id):
                logger.error(f"Invalid or insecure document ID: {document_id}")
                return

            logger.info(f"Worker: Compiling document {document_id}")
            
            import tempfile
            with tempfile.TemporaryDirectory(prefix="doclib_build_") as work_dir:
                tex_file = os.path.join(work_dir, "main.tex")
                with open(tex_file, "w") as f:
                    f.write(content_raw)
                
                proc = await asyncio.create_subprocess_exec(
                    "tectonic", "main.tex",
                    cwd=work_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                db = db_client.mongodb.get_default_database()
                documents_collection = db["documents"]
                
                if proc.returncode == 0:
                    logger.info(f"Worker: Successfully compiled PDF for document {document_id}")
                    pdf_file_path = os.path.join(work_dir, "main.pdf")
                    
                    from core.storage import upload_file
                    import uuid
                    from uuid6 import uuid7
                    file_key = f"documents/{document_id}/tectonic_{uuid7().hex[:8]}.pdf"
                    
                    if os.path.exists(pdf_file_path):
                        with open(pdf_file_path, "rb") as bf:
                            await upload_file(bf.read(), file_key, "application/pdf")
                        logger.info(f"Worker: Uploaded {pdf_file_path} to MinIO successfully: {file_key}")
                    
                    await documents_collection.update_one(
                        {"_id": document_id},
                        {"$set": {"status": "published", "file_url": file_key}}
                    )
                    
                    if author_id:
                        try:
                            import httpx
                            from core.config import settings
                            if settings.SIGNAL_URL:
                                async with httpx.AsyncClient() as client:
                                    await client.post(
                                        f"{settings.SIGNAL_URL}/thong-bao/kich-hoat",
                                        json={
                                            "target_user_id": author_id,
                                            "title": "Biên dịch tài liệu thành công",
                                            "body": f"Bản in PDF chất lượng cao cho tài liệu {document_id} đã sẵn sàng.",
                                            "type": "SYSTEM"
                                        },
                                        timeout=3.0
                                    )
                        except Exception as e:
                            logger.error(f"Notification failed: {e}")
                else:
                    logger.error(f"Worker: PDF compilation failed for {document_id}: {stderr.decode()}")
                    await documents_collection.update_one(
                        {"_id": document_id},
                        {"$set": {"status": "error_compilation"}}
                    )
                    
                    if author_id:
                        try:
                            import httpx
                            from core.config import settings
                            if settings.SIGNAL_URL:
                                async with httpx.AsyncClient() as client:
                                    await client.post(
                                        f"{settings.SIGNAL_URL}/thong-bao/kich-hoat",
                                        json={
                                            "target_user_id": author_id,
                                            "title": "Lỗi biên dịch tài liệu",
                                            "body": f"Tệp nguồn của {document_id} gặp lỗi cú pháp. Không thể xuất bản tập tin PDF.",
                                            "type": "SYSTEM"
                                        },
                                        timeout=3.0
                                    )
                        except Exception as e:
                            logger.error(f"Notification failed: {e}")
                
        except Exception as e:
            logger.error(f"Worker: Queue error: {str(e)}")

async def start_tectonic_worker():
    if not db_client.rabbitmq:
        logger.info("Worker: RabbitMQ unreachable, waiting...")
        return
        
    try:
        channel = await db_client.rabbitmq.channel()
        await channel.set_qos(prefetch_count=2)
        queue = await channel.declare_queue("tectonic_queue", durable=True)
        
        await queue.consume(process_tectonic_compile)
        logger.info("Worker: Ready to process message queue.")
    except Exception as e:
        logger.error(f"Worker: Startup error: {str(e)}")

async def process_document_publish(message: AbstractIncomingMessage):
    async with message.process():
        try:
            payload = json.loads(message.body.decode("utf-8"))
            document_id = payload.get("document_id")
            author_id = payload.get("author_id")
            
            db = db_client.mongodb.get_default_database()
            docs_col = db["documents"]
            document = await docs_col.find_one({"_id": document_id})
            import httpx
            author = None
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"http://provision:8450/nguoi-dung/noi-bo/{author_id}", timeout=3.0)
                    if resp.status_code == 200:
                        author = resp.json().get('data')
            except Exception:
                pass
            
            if not document or not author:
                return
                
            total_words = len(document.get("content", "").split())
            base_price = max(10, total_words // 1000 * 5)
                       
            await docs_col.update_one(
                {"_id": document_id},
                {"$set": {
                    "status": "published", 
                    "total_words": total_words,
                    "suggested_price": base_price
                }}
            )
            
            followers = author.get("followers", [])
            try:
                import httpx
                from core.config import settings
                if settings.SIGNAL_URL:
                    async with httpx.AsyncClient() as client:
                        for follower_id in followers:
                            try:
                                await client.post(
                                    f"{settings.SIGNAL_URL}/thong-bao/kich-hoat",
                                    json={
                                        "target_user_id": follower_id,
                                        "title": "Tài liệu mới xuất bản",
                                        "body": f"Tác giả {author.get('full_name')} vừa ra mắt tài liệu {document.get('title')}",
                                        "type": "SYSTEM"
                                    },
                                    timeout=3.0
                                )
                            except Exception:
                                pass
            except Exception as e:
                logger.error(f"Notification failed: {e}")
                
            logger.info(f"Worker: Background publication complete for document {document_id}")
            
        except Exception as e:
            logger.error(f"Worker: Document Publish queue error: {str(e)}")

async def process_user_interaction(message: AbstractIncomingMessage):
    async with message.process():
        try:
            payload = json.loads(message.body.decode("utf-8"))
            user_id = payload.get("user_id")
            action = payload.get("action")
            document_id = payload.get("document_id")
            
            if not user_id or not document_id:
                return
                
            from core.config import settings
            import httpx
            rag_url = getattr(settings, "AGENTIC_AI_URL", None)
            
            if rag_url:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        f"{rag_url}/inference/cap-nhat-hanh-vi",
                        json={"user_id": user_id, "document_id": document_id, "action": action}
                    )
                    if resp.status_code == 200:
                        logger.info(f"Worker: Event-Driven AI successfully updated Vector DB for user {user_id}")
                    else:
                        logger.warning(f"Worker: AI Vector DB update failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"Worker: User Interaction queue error: {str(e)}")

async def start_workers():
    if not db_client.rabbitmq:
        logger.warning("Worker: RabbitMQ not active, waiting")
        return
        
    try:
        channel = await db_client.rabbitmq.channel()
        await channel.set_qos(prefetch_count=5)
        
        queue_tectonic = await channel.declare_queue("tectonic_queue", durable=True)
        await queue_tectonic.consume(process_tectonic_compile)
        
        queue_publish = await channel.declare_queue("document_publish_queue", durable=True)
        await queue_publish.consume(process_document_publish)
        
        queue_interaction = await channel.declare_queue("user_interaction_queue", durable=True)
        await queue_interaction.consume(process_user_interaction)
        
        logger.info("Worker: All background workers are active.")
    except Exception as e:
        logger.error(f"Worker: Startup error: {str(e)}")
