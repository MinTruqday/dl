import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

async function doDirectUpload(file: File, isSystem: boolean, isMessageAttachment: boolean) {
  // 1. Request Presigned URL
  const reqRes = await fetch(`${API_URL}/tai-len/yeu-cau-presigned-url`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      filename: file.name,
      size: file.size,
      content_type: file.type || "application/octet-stream",
      is_system: isSystem,
      is_message_attachment: isMessageAttachment
    }),
  });
  
  const reqData = await reqRes.json();
  if (!reqRes.ok) throw new Error(reqData.detail || reqData.message || "Lỗi cấp phát chuỗi xác thực (Presigned URL)");
  
  const { upload_url, file_path } = reqData.data;

  // 2. Upload file directly to MinIO using PUT
  const putRes = await fetch(upload_url, {
    method: "PUT",
    headers: {
      "Content-Type": file.type || "application/octet-stream",
    },
    body: file,
  });
  
  if (!putRes.ok) throw new Error("Lỗi đẩy luồng dữ liệu (Stream) lên máy chủ lưu trữ");

  // 3. Confirm upload
  const confirmRes = await fetch(`${API_URL}/tai-len/xac-nhan`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      file_path,
      filename: file.name,
      size: file.size,
      content_type: file.type || "application/octet-stream",
      is_system: isSystem,
      is_message_attachment: isMessageAttachment
    }),
  });
  
  const confirmData = await confirmRes.json();
  if (!confirmRes.ok) throw new Error(confirmData.detail || confirmData.message || "Lỗi đồng bộ trạng thái lưu trữ cuối cùng");
  
  return confirmData;
}

export async function uploadAssetAPI(file: File, type: string = "document") {
  return await doDirectUpload(file, false, false);
}

export async function uploadDocumentAPI(file: File) {
  return await doDirectUpload(file, true, false);
}

export async function uploadImageAPI(file: File) {
  return await doDirectUpload(file, true, false);
}

export async function uploadChatAttachmentAPI(file: File) {
  return await doDirectUpload(file, false, true);
}
