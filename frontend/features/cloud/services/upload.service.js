import { API_URL, authenticatedFetch, getAuthHeaders } from "@/shared/services/api-client";
async function doDirectUpload(file, isSystem, isMessageAttachment) {
  const reqRes = await authenticatedFetch(`${API_URL}/tai-len/presigned-url`, {
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
      is_message_attachment: isMessageAttachment,
    }),
  });
  const reqData = await reqRes.json();
  if (!reqRes.ok)
    throw new Error(
      reqData.detail || reqData.message || "Lỗi cấp phát chuỗi xác thực (Presigned URL)",
    );
  const { upload_url, file_path } = reqData.data;
  const putRes = await fetch(upload_url, {
    method: "PUT",
    headers: {
      "Content-Type": file.type || "application/octet-stream",
    },
    body: file,
  });
  if (!putRes.ok) throw new Error("Lỗi đẩy luồng dữ liệu (Stream) lên máy chủ lưu trữ");
  const confirmRes = await authenticatedFetch(`${API_URL}/tai-len/xac-nhan`, {
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
      is_message_attachment: isMessageAttachment,
    }),
  });
  const confirmData = await confirmRes.json();
  if (!confirmRes.ok)
    throw new Error(
      confirmData.detail || confirmData.message || "Không thể đồng bộ trạng thái lưu trữ cuối cùng",
    );
  return confirmData;
}
export async function uploadAssetAPI(file, type = "document") {
  return await doDirectUpload(file, false, false);
}
export async function uploadDocumentAPI(file) {
  return await doDirectUpload(file, true, false);
}
export async function uploadImageAPI(file) {
  return await doDirectUpload(file, true, false);
}
export async function uploadChatAttachmentAPI(file) {
  return await doDirectUpload(file, false, true);
}
export async function getChatAttachmentBlobUrlAPI(filePath) {
  if (!filePath || /^(https?:|blob:|data:)/.test(filePath)) return filePath;
  const response = await fetch(`${API_URL}/tai-len/noi-dung/${filePath.replace(/^\/+/, "")}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Không thể tải tệp tin nhắn");
  return URL.createObjectURL(await response.blob());
}
export async function getProtectedAssetBlobUrlAPI(filePath) {
  return getChatAttachmentBlobUrlAPI(filePath);
}
export async function downloadProtectedAssetAPI(filePath, filename) {
  const blobUrl = await getProtectedAssetBlobUrlAPI(filePath);
  const anchor = document.createElement("a");
  anchor.href = blobUrl;
  anchor.download = filename;
  anchor.click();
  if (blobUrl.startsWith("blob:")) URL.revokeObjectURL(blobUrl);
}
