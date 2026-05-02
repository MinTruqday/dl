import { API_URL, getToken } from './auth.service';

export const saveReadingProgressAPI = async (documentId: string, scrollPercent: number) => {
    const token = getToken();
    if (!token) return null;
    const res = await fetch(`${API_URL}/read/progress`, {
        method: "POST",
        headers: {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ document_id: documentId, progress_percentage: scrollPercent })
    });
    if (!res.ok) return null;
    return await res.json();
};

export const getOldReadingHistoryAPI = async () => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/read/history`, {
        method: "GET",
        headers: {
            "Authorization": "Bearer " + token
        }
    });
    if (!res.ok) throw new Error("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.");
    return await res.json();
};

export const getRecommendationsAPI = async () => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/discovery/recommendations/ai`, {
        method: "GET",
        headers: {
            "Authorization": "Bearer " + token
        }
    });
    if (!res.ok) throw new Error("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.");
    return await res.json();
};

export async function getBookmarksAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/profile/bookmarks`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) return null;
    return await res.json();
}

export async function toggleBookmarkAPI(documentId: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/profile/bookmarks/${documentId}`, {
        method: "POST",
        headers: { "Authorization": "Bearer " + token }
    });
    return res.ok;
}

export async function togglePinDocumentAPI(documentId: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/profile/pin/${documentId}`, {
        method: "POST",
        headers: { "Authorization": "Bearer " + token }
    });
    return res.ok;
}

export async function updateReadingProgressAPI(documentId: string, progress: number, currentChapterSlug?: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/read/progress`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({ document_id: documentId, progress_percentage: progress, current_chapter_slug: currentChapterSlug })
    });
    return res.ok;
}

export async function getReadingHistoryAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/read/history`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải lịch sử đọc tài liệu.");
    return await res.json();
}

export async function clearReadingHistoryAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/read/history`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Xóa lịch sử thất bại.");
    return await res.json();
}

export async function deleteReadingHistoryItemAPI(documentId: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/read/history/${documentId}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Xóa mục lịch sử thất bại.");
    return await res.json();
}

export async function getBookmarkFoldersAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/library/bookmarks/folders`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách thư mục.");
    return await res.json();
}

export async function createBookmarkFolderAPI(name: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/library/bookmarks/folders`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token 
        },
        body: JSON.stringify({ name })
    });
    if (!res.ok) throw new Error("Không thể tạo thư mục mới.");
    return await res.json();
}

export async function getPinnedDocumentsAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/read/pinned`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách ghim.");
    return await res.json();
}

export async function getContinueReadingAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/read/continue`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách đang đọc.");
    return await res.json();
}

export async function getReadingListsAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/library/lists`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách bộ sưu tập.");
    return await res.json();
}

export async function createReadingListAPI(data: { name: string, description?: string, is_public?: boolean }) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/library/lists`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token 
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Không thể tạo bộ sưu tập mới.");
    return await res.json();
}

export async function getReadingListByIdAPI(listId: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/library/lists/${listId}`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải chi tiết bộ sưu tập.");
    return await res.json();
}
export async function getLibraryAPI() {
    const token = getToken();
    if (!token) return [];
    const res = await fetch(`${API_URL}/library/me`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) return [];
    return await res.json();
}

export async function addToLibraryAPI(documentId: string, status: string = "reading") {
    const token = getToken();
    const res = await fetch(`${API_URL}/library/me`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({ document_id: documentId, status })
    });
    return res.ok;
}

export async function removeFromLibraryAPI(documentId: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/library/me`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({ document_id: documentId })
    });
    return res.ok;
}

export const createHighlightAPI = async (documentId: string, text: string, color: string, note?: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/read/documents/${documentId}/highlights`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ text, color, note })
    });
    return await res.json();
};

export const getHighlightsAPI = async (documentId: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/read/documents/${documentId}/highlights`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    const json = await res.json();
    return json.data || json;
};

export async function deleteHighlightAPI(highlightId: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/read/highlights/${highlightId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Xóa điểm nhấn thất bại.");
    return await res.json();
}

export async function exportHighlightsMarkdownAPI(documentId: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/read/documents/${documentId}/highlights/export`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Xuất dữ liệu điểm nhấn thất bại.");
    return await res.json();
}
