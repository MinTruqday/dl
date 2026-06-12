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
            
            if not document_id or "" in str(document_id):
                logger.error(f"Mã tài liệu không hợp lệ hoặc không an toàn: {document_id}")
                return

            logger.info(f"Đang biên dịch tài liệu {document_id}")
            
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
                    logger.info(f"Quá trình biên dịch tệp PDF cho tài liệu {document_id} đã hoàn tất")
                    pdf_file_path = os.path.join(work_dir, "main.pdf")
                    
                    from core.storage import upload_file
                    import uuid
                    from uuid6 import uuid7
                    file_key = f"tài liệu/{document_id}/tectonic_{uuid7().hex[:8]}.pdf"
                    
                    if os.path.exists(pdf_file_path):
                        with open(pdf_file_path, "rb") as bf:
                            await upload_file(bf.read(), file_key, "application/pdf")
                        logger.info(f"Tải lên tài liệu {pdf_file_path} lên hệ thống lưu trữ thành công: {file_key}")
                    
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
                                        f"{settings.SIGNAL_URL}/thong-bao/noi-bo/kich-hoat",
                                        json={
                                            "target_user_id": author_id,
                                            "title": "Biên dịch tài liệu thành công",
                                            "body": f"Bản in PDF chất lượng cao cho tài liệu {document_id} đã sẵn sàng",
                                            "type": "SYSTEM"
                                        },
                                        timeout=3.0
                                    )
                        except Exception as e:
                            logger.error(f"Không thể gửi thông báo: {e}")
                else:
                    logger.error(f"Biên dịch tệp PDF thất bại cho tài liệu {document_id}: {stderr.decode()}")
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
                                        f"{settings.SIGNAL_URL}/thong-bao/noi-bo/kich-hoat",
                                        json={
                                            "target_user_id": author_id,
                                            "title": "Lỗi biên dịch tài liệu",
                                            "body": f"Tệp nguồn của {document_id} gặp lỗi cú pháp. Không thể xuất bản tập tin PDF",
                                            "type": "SYSTEM"
                                        },
                                        timeout=3.0
                                    )
                        except Exception as e:
                            logger.error(f"Không thể gửi thông báo: {e}")
                
        except Exception as e:
            logger.error(f"Hàng đợi thất bại: {str(e)}")

async def start_tectonic_worker():
    if not db_client.rabbitmq:
        logger.info("Không thể kết nối hệ thống hàng đợi, đang thử lại")
        return
        
    try:
        channel = await db_client.rabbitmq.channel()
        await channel.set_qos(prefetch_count=2)
        queue = await channel.declare_queue("tectonic_queue", durable=True)
        
        await queue.consume(process_tectonic_compile)
        logger.info("Hệ thống đã sẵn sàng xử lý hàng đợi tin nhắn")
    except Exception as e:
        logger.error(f"Lỗi khởi động dịch vụ nền: {str(e)}")

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
                    resp = await client.get(f"{settings.PROVISION_URL}/nguoi-dung/noi-bo/{author_id}", timeout=3.0)
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
                                    f"{settings.SIGNAL_URL}/thong-bao/noi-bo/kich-hoat",
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
                logger.error(f"Không thể gửi thông báo: {e}")
                
            logger.info(f"Quá trình xuất bản nền cho tài liệu {document_id} đã hoàn tất")
            
        except Exception as e:
            logger.error(f"Hàng đợi xuất bản tài liệu thất bại: {str(e)}")

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
                        logger.info(f"AI đã cập nhật cơ sở dữ liệu vector cho người dùng {user_id}")
                    else:
                        logger.warning(f"Không thể cập nhật cơ sở dữ liệu vector AI: {resp.status_code}")
        except Exception as e:
            logger.error(f"Hàng đợi tương tác người dùng thất bại: {str(e)}")

async def start_workers():
    if not db_client.rabbitmq:
        logger.warning("Hệ thống hàng đợi chưa sẵn sàng, đang chờ kết nối")
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
        
        logger.info("Tất cả các dịch vụ nền đang hoạt động ổn định")
    except Exception as e:
        logger.error(f"Lỗi khởi động dịch vụ nền: {str(e)}")
