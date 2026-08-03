import asyncio
from src.core.logic_logger import log_logic_execution
from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.database import database
from src.repositories.license import LicenseRepository

try:
    import fitz
except ImportError as e:
    logger.exception("Document rendering toolkit (PyMuPDF) import failed")
    REPORTLAB_AVAILABLE = False
else:
    REPORTLAB_AVAILABLE = True


class WatermarkService:

    @staticmethod
    def encode_uid_to_zws(user_id: str) -> str:
        binary = "".join(format(ord(c), "08b") for c in user_id)
        zero_width_payload = binary.replace("0", "\u200B").replace("1", "\u200C")
        return f"\u200D{zero_width_payload}\u200D"

    @staticmethod
    def inject_structural_watermark_editorjs(raw_json_content: str, user_id: str) -> str:
        import json
        try:
            content_dict = json.loads(raw_json_content)
            blocks = content_dict.get("blocks", [])
            stealth_payload = WatermarkService.encode_uid_to_zws(user_id)
            text_block_types = ["paragraph", "header", "quote", "warning"]
            for block in blocks:
                b_type = block.get("type")
                if b_type in text_block_types:
                    original_text = block.get("data", {}).get("text", "")
                    if original_text:
                        block["data"]["text"] = f"{original_text}{stealth_payload}"
                elif b_type == "list":
                    items = block.get("data", {}).get("items", [])
                    for i in range(len(items)):
                        items[i] = f"{items[i]}{stealth_payload}"
            return json.dumps(content_dict, ensure_ascii=False)
        except Exception as e:
            logger.error("Lỗi khi tiêm thủy vân vào EditorJS AST")
            return raw_json_content

    @staticmethod
    def inject_structural_watermark_latex(raw_latex: str, user_id: str) -> str:
        import re
        try:
            stealth_payload = WatermarkService.encode_uid_to_zws(user_id)
            if r"\end{document}" in raw_latex:
                raw_latex = raw_latex.replace(r"\end{document}", f"{stealth_payload}\n\\end{{document}}")
            else:
                raw_latex += stealth_payload

            blocks = raw_latex.split('\n\n')
            watermarked_blocks = []
            unsafe_markers = [r"\begin", r"\end", r"$$", r"\[", r"\]", r"\item", r"\section", r"\chapter"]
            
            for block in blocks:
                if any(marker in block for marker in unsafe_markers):
                    watermarked_blocks.append(block)
                    continue
                
                stripped_block = block.strip()
                if re.search(r'[a-zA-Z0-9]', stripped_block) and re.search(r'[.!?]$', stripped_block):
                    block = stripped_block + stealth_payload
                watermarked_blocks.append(block)

            return '\n\n'.join(watermarked_blocks)
            
        except Exception as e:
            logger.error("Lỗi khi tiêm thủy vân vào LaTeX")
            return raw_latex

    @staticmethod
    @log_logic_execution
    async def export_document_pdf_watermarked(document_id: str, current_user, client_ip: str = "127.0.0.1"):
        if not REPORTLAB_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="Tính năng kết xuất PDF tạm thời không khả dụng, vui lòng thử lại sau",
            )
        document = await LicenseRepository.get_document(str(document_id))
        if not document:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu kết xuất")
        user_email = (
            current_user.email
            if hasattr(current_user, "email") and current_user.email
            else str(current_user.id)
        )
        import httpx
        from src.core.infrastructure.configuration import settings

        user_id = str(current_user.id)
        user_tier = current_user.tier

        try:
            async with httpx.AsyncClient() as client:
                agent_res = await client.post(
                    f"{settings.INTERNAL_API_URL}/drm/danh-gia",
                    json={
                        "user_id": user_id,
                        "document_id": str(document["_id"]),
                        "client_ip": client_ip,
                        "user_tier": user_tier,
                        "document_type": "premium" if document.get("is_premium") else "standard"
                    },
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                    timeout=5.0
                )
                if agent_res.status_code == 200:
                    policy_data = agent_res.json().get("data", {})
                    decision = policy_data.get("decision", "LEVEL_2")
                    if decision == "BLOCKED":
                        raise HTTPException(status_code=403, detail="Hành vi truy cập bị từ chối bởi hệ thống bảo mật thông minh")
                    
                    enable_visual = policy_data.get("enable_visual_watermark", True)
                    enable_micro = policy_data.get("enable_micro_dots", True)
                    enable_aes = policy_data.get("enable_aes_encryption", True)
                else:
                    enable_visual, enable_micro, enable_aes = True, True, True
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("Failed to evaluate DRM policy via Agentic AI, falling back to LEVEL_2")
            enable_visual, enable_micro, enable_aes = True, True, True

        from src.core.dependency import Role
        if (
            document.get("is_premium")
            and document.get("creator_id") != user_id
            and (not hasattr(current_user, "role") or getattr(current_user.role, "value", current_user.role) != Role.ADMIN.value)
        ):
            purchase = await LicenseRepository.get_purchase(user_id, str(document["_id"]))
            if not purchase:
                raise HTTPException(
                    status_code=403,
                    detail="Tài liệu yêu cầu quyền truy cập đặc biệt hoặc xác nhận mua hàng",
                )

        content_format = document.get("content_format", "doclib")
        raw_content = str(document.get("content", ""))

        if content_format == "doclibx":
            watermarked_latex = raw_content
            try:
                from src.compilation.engines.latex import LatexEngine
                pdf_data_pre = await LatexEngine.compile_to_pdf(watermarked_latex)
            except ImportError:
                try:
                    async with httpx.AsyncClient() as client:
                        r = await client.post(
                            f"{settings.INTERNAL_API_URL}/soan-thao/latex/ket-xuat/pdf",
                            json={"content": watermarked_latex},
                            headers={"X-Internal-Token": settings.SECRET_KEY},
                            timeout=10.0
                        )
                        r.raise_for_status()
                        pdf_data_pre = r.content
                except Exception as e:
                    logger.exception("Failed to compile LaTeX content for DRM export")
                    raise HTTPException(status_code=500, detail="Đã xảy ra lỗi trong quá trình biên dịch tài liệu LaTeX")
        else:
            watermarked_raw_content = WatermarkService.inject_structural_watermark_editorjs(raw_content, user_id) if enable_micro else raw_content
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.post(
                        f"{settings.INTERNAL_API_URL}/soan-thao/editorjs/ket-xuat/pdf",
                        json={"content": watermarked_raw_content},
                        headers={"X-Internal-Token": settings.SECRET_KEY},
                        timeout=10.0
                    )
                    r.raise_for_status()
                    pdf_data_pre = r.content
            except Exception:
                try:
                    from src.compilation.engines.editorjs import EditorjsEngine
                    pdf_data_pre = await EditorjsEngine.compile_to_pdf(watermarked_raw_content)
                except Exception as e:
                    logger.exception("Failed to render EditorJS content for DRM export")
                    raise HTTPException(status_code=500, detail="Đã xảy ra lỗi trong quá trình kết xuất nội dung tài liệu")

        def apply_watermark_to_pdf(source_pdf_bytes: bytes) -> bytes:
            if not enable_visual and not enable_micro:
                return source_pdf_bytes

            try:
                import fitz
                import io
                
                doc = fitz.open("pdf", source_pdf_bytes)
                binary_id = ''.join(format(ord(c), '08b') for c in user_id)
                
                for page in doc:
                    rect = page.rect
                    width, height = rect.width, rect.height
                    
                    if enable_visual:
                        watermark_point = fitz.Point(width / 4, height / 2)
                        page.insert_text(
                            watermark_point,
                            user_email,
                            fontsize=60,
                            fontname="helv",
                            color=(0.7, 0.7, 0.7),
                            fill_opacity=0.2,
                            overlay=True
                        )
                        page.insert_text(
                            fitz.Point(10, height - 10),
                            f"DOCLIB_UID_{user_id}",
                            fontsize=1,
                            color=(1, 1, 1),
                            fill_opacity=0.01,
                            overlay=True
                        )

                    if enable_micro:
                        page.draw_circle(fitz.Point(20, 20), 2, color=(0.9, 0.9, 0.9), fill=(0.9, 0.9, 0.9), fill_opacity=0.5)
                        page.draw_circle(fitz.Point(width - 20, 20), 2, color=(0.9, 0.9, 0.9), fill=(0.9, 0.9, 0.9), fill_opacity=0.5)
                        page.draw_circle(fitz.Point(20, height - 20), 2, color=(0.9, 0.9, 0.9), fill=(0.9, 0.9, 0.9), fill_opacity=0.5)

                        dot_color = (0.95, 0.95, 0.9) 
                        x_start, y_start = 20, 20
                        dot_spacing = 12
                        
                        idx = 0
                        for i in range(len(binary_id)):
                            if binary_id[i] == '1':
                                x = x_start + (idx * dot_spacing) % (width - 40)
                                y = y_start + ((idx * dot_spacing) // int(width - 40)) * dot_spacing
                                
                                page.draw_circle(
                                    fitz.Point(x, y), 
                                    0.5, 
                                    color=dot_color, 
                                    fill=dot_color, 
                                    fill_opacity=0.4
                                )
                            idx += 1

                final_buffer = io.BytesIO()
                doc.save(final_buffer, garbage=4, deflate=True)
                return final_buffer.getvalue()
                
            except Exception as e:
                logger.exception("Watermarking process using PyMuPDF failed")
                return None

        pdf_data = await asyncio.to_thread(apply_watermark_to_pdf, pdf_data_pre)
        if pdf_data is None:
            raise HTTPException(
                status_code=500, detail="Đã xảy ra lỗi hệ thống trong quá trình kết xuất tài liệu bảo mật"
            )
            
        if not enable_aes:
            logger.info("Document exported without AES encryption (Dynamic DRM Policy)")
            return pdf_data, "pdf", "application/pdf"
            
        import os
        import hashlib
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from src.services.license import LicenseService
        import uuid
        
        try:
            file_id, aes_key = await LicenseService.create_license(str(document["_id"]), user_id)
        except Exception as e:
            logger.exception("Failed to initialize E-DRM license structure")
            raise HTTPException(status_code=500, detail="Đã xảy ra lỗi trong quá trình tạo khóa bảo vệ tài liệu E-DRM")
            
        try:
            aesgcm = AESGCM(aes_key)
            nonce = os.urandom(12)
            content_bytes = pdf_data
            ciphertext = aesgcm.encrypt(nonce, content_bytes, None)
            
            file_id_bytes = uuid.UUID(file_id).bytes 
            file_hash = hashlib.sha256(content_bytes).digest()
            final_doclib_data = file_id_bytes + file_hash + nonce + ciphertext
        except Exception as e:
            logger.exception("AES encryption failed for document content")
            raise HTTPException(status_code=500, detail="Đã xảy ra lỗi hệ thống trong quá trình mã hóa tài liệu")

        logger.info(f"Exported E-DRM document, file_id={file_id}")
        return final_doclib_data, "doclib", "application/octet-stream"

    @staticmethod
    @log_logic_execution
    async def verify_watermark(text: str) -> str:
        import re
        matches = re.findall(r'\u200D([\u200B\u200C]+)\u200D', text)
        if not matches:
            return None
        for match in matches:
            binary = match.replace('\u200B', '0').replace('\u200C', '1')
            try:
                bytes_list = [int(binary[i:i+8], 2) for i in range(0, len(binary), 8)]
                decoded = bytes(bytes_list).decode("utf-8")
                if decoded:
                    return decoded
            except Exception:
                continue
        return None
