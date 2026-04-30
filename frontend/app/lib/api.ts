export const API_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_URL) {
    if (typeof window !== "undefined") {
        console.error("Lỗi nghiêm trọng: Biến môi trường NEXT_PUBLIC_API_URL chưa được thiết lập.");
    }
}

export async function login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString()
    });

    const json = await res.json();
    if (!res.ok) throw new Error(formatError(json.detail) || json.message || "Đăng nhập thất bại.");
    return json.data;
}

export async function register(email: string, password: string, full_name: string, slug: string, agreed_to_terms: boolean) {
    const res = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, full_name, slug, agreed_to_terms })
    });

    const json = await res.json();
    if (!res.ok) throw new Error(formatError(json.detail) || json.message || "Đăng ký thất bại.");
    return json.data;
}

export function getToken() {
    if (typeof window !== 'undefined') {
        return localStorage.getItem('doclib_token');
    }
    return null;
}

export function setToken(token: string) {
    if (typeof window !== 'undefined') {
        localStorage.setItem('doclib_token', token);
        userMePromise = null; // Clear cache
    }
}

export function removeToken() {
    if (typeof window !== 'undefined') {
        localStorage.removeItem('doclib_token');
        userMePromise = null; // Clear cache
    }
}

let userMePromise: Promise<any> | null = null;
export async function getUserMe() {
    const token = getToken();
    if (!token) return null;

    if (userMePromise) return userMePromise;

    userMePromise = (async () => {
        try {
            const res = await fetch(`${API_URL}/auth/me`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!res.ok) {
                removeToken(); 
                return null;
            }
            const json = await res.json();
            return json.data;
        } finally {
            userMePromise = null;
        }
    })();
    return userMePromise;
}

export async function uploadDocumentFile(file: File) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");

    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_URL}/storage/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Tải lên thất bại.");
    return data;
}

export async function getFileDownloadUrl(filePath: string) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");

    const res = await fetch(`${API_URL}/storage/${encodeURIComponent(filePath)}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Lấy đường dẫn thất bại.");
    return data.download_url;
}



export async function saveDocumentDraftAPI(documentId: string, content: string, format: string) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");

    const res = await fetch(`${API_URL}/documents/${documentId}/content`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            content: content,
            content_format: format
        })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Lưu bản nháp thất bại.");
    return data;
}

export async function publishDocumentAPI(documentId: string) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");

    const res = await fetch(`${API_URL}/documents/${documentId}/publish`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Xuất bản thất bại.");
    return data;
}

export async function getDocumentDraftAPI(documentId: string) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");

    const res = await fetch(`${API_URL}/documents/${documentId}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Tải bản nháp thất bại.");
    return data;
}

export async function compileDocumentAPI(documentId: string) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");

    const res = await fetch(`${API_URL}/documents/${documentId}/compile`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Biên dịch tài liệu thất bại.");
    return data;
}

export async function getDocumentsAPI(
    search?: string, 
    sortBy?: string, 
    category?: string, 
    tag?: string,
    folder_id?: string,
    is_starred?: boolean,
    fmt?: string
) {
    const token = getToken();
    let url = `${API_URL}/documents/`;
    const params = new URLSearchParams();
    if (search) params.append("q", search);
    if (sortBy) params.append("sort_by", sortBy);
    if (category) params.append("category", category);
    if (tag) params.append("tag", tag);
    if (folder_id) params.append("folder_id", folder_id);
    if (is_starred) params.append("is_starred", "true");
    if (fmt && fmt !== "all") params.append("fmt", fmt);
    
    if (params.toString()) url += `?${params.toString()}`;

    const res = await fetch(url, {
        method: 'GET',
        headers: token ? {
            'Authorization': `Bearer ${token}`
        } : {}
    });

    if (!res.ok) throw new Error("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.");
    return await res.json();
}

export async function getMyDocumentsAPI(skip: number = 0, limit: number = 50) {
    const token = getToken();
    const res = await fetch(`${API_URL}/author/documents?skip=${skip}&limit=${limit}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const json = await res.json();
    if (!res.ok) throw new Error(json.message || "Không thể lấy danh sách tài liệu của bạn.");
    return json.data || json;
}

export async function getTrendingDocumentsAPI(limit: number = 5) {
    const res = await fetch(`${API_URL}/documents/trending?limit=${limit}`);
    if (!res.ok) throw new Error("Không thể tải xu hướng.");
    return await res.json();
}
export async function getFeaturedAuthorsAPI(limit: number = 5) {
    const res = await fetch(`${API_URL}/guest/authors/featured?limit=${limit}`);
    if (!res.ok) throw new Error("Không thể tải danh sách tác giả.");
    return await res.json();
}

export async function getTagsCategoriesAPI() {
    const res = await fetch(`${API_URL}/documents/tags-and-categories`);
    if (!res.ok) throw new Error("Không thể tải danh mục.");
    return await res.json();
}

export async function getFeedMe(offset: number = 0, limit: number = 10) {
    const token = getToken();
    if (!token) return null;
    const res = await fetch(`${API_URL}/social/feed?skip=${offset}&limit=${limit}`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) return null;
    return await res.json();
}

export async function postQuoteAPI(documentId: string, quoteText: string, bgColor: string) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");

    const res = await fetch(`${API_URL}/social/quotes`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            document_id: documentId,
            quote_text: quoteText,
            background_color: bgColor
        })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Chia sẻ trích dẫn thất bại.");
    return data;
}

export const toggleReactionAPI = async (itemId: string, itemType: string, reactionType: string | null) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/${itemType}/${itemId}/reaction`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        },
        body: JSON.stringify({ reaction_type: reactionType })
    });
    if (!res.ok) throw new Error("Thả cảm xúc thất bại.");
    return res.json();
};

export const getFeedCommentsAPI = async (itemId: string, itemType: string) => {
    const token = getToken();
    const headers: any = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_URL}/social/${itemType}/${itemId}/comments`, { headers });
    if (!res.ok) throw new Error("Lấy danh sách bình luận thất bại.");
    return res.json();
};

export const createFeedCommentAPI = async (itemId: string, itemType: string, content: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/${itemType}/${itemId}/comment`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        },
        body: JSON.stringify({ content })
    });
    if (!res.ok) throw new Error("Tạo bình luận thất bại.");
    return res.json();
};

export const toggleFeedBookmarkAPI = async (itemId: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/feed/${itemId}/bookmark`, {
        method: "POST",
        headers: {
            "Authorization": "Bearer " + token,
        }
    });
    if (!res.ok) throw new Error("Tải dữ liệu thất bại.");
    return res.json();
};

export const saveReadingProgressAPI = async (documentId: string, scrollPercent: number) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("doclib_token") : null;
    if (!token) return null;
    const res = await fetch(`${API_URL}/reading/progress`, {
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
    const token = typeof window !== "undefined" ? localStorage.getItem("doclib_token") : null;
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/history`, {
        method: "GET",
        headers: {
            "Authorization": "Bearer " + token
        }
    });
    if (!res.ok) throw new Error("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.");
    return await res.json();
};

export const getRecommendationsAPI = async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("doclib_token") : null;
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reading/recommendations`, {
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
    const res = await fetch(`${API_URL}/reading/progress`, {
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
    const res = await fetch(`${API_URL}/reader/history`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải lịch sử đọc tài liệu.");
    return await res.json();
}

export async function uploadMediaAPI(formData: FormData) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/social/upload-media`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData,
    });
    if (!res.ok) throw new Error("Tải tệp tin lên thất bại.");
    return await res.json();
}

export async function clearReadingHistoryAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/history`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Xóa lịch sử thất bại.");
    return await res.json();
}

export async function deleteReadingHistoryItemAPI(documentId: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/history/${documentId}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Xóa mục lịch sử thất bại.");
    return await res.json();
}

export async function getBookmarkFoldersAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/bookmark-folders`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách thư mục.");
    return await res.json();
}

export async function createBookmarkFolderAPI(name: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/bookmark-folders`, {
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
    const res = await fetch(`${API_URL}/reader/pinned-documents`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách ghim.");
    return await res.json();
}

export async function getContinueReadingAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/continue-reading`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách đang đọc.");
    return await res.json();
}

export async function getReadingListsAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/lists`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách bộ sưu tập.");
    return await res.json();
}

export async function createReadingListAPI(data: { name: string, description?: string, is_public?: boolean }) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/lists`, {
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
    const res = await fetch(`${API_URL}/reader/lists/${listId}`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải chi tiết bộ sưu tập.");
    return await res.json();
}

export async function getDetailedHistoryAPI(skip?: number, limit?: number, txType?: string) {
    return getWalletHistoryAPI(skip, limit, txType);
}
export async function getDiscussionsAPI(documentId: string) {
    const res = await fetch(`${API_URL}/social/documents/${documentId}/discussions`);
    if (!res.ok) throw new Error("Không thể tải thảo luận.");
    return await res.json();
}
export async function createDiscussionAPI(documentId: string, title: string, content: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/documents/${documentId}/discussions`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify({ title, content })
    });
    if (!res.ok) throw new Error("Tạo thảo luận thất bại.");
    return await res.json();
}
export async function replyDiscussionAPI(discussionId: string, content: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/discussions/${discussionId}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify({ content })
    });
    if (!res.ok) throw new Error("Gửi trả lời thất bại.");
    return await res.json();
}
export async function getAuthorStatsAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/analytics/author/stats`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải thông số phân tích.");
    return await res.json();
}

export async function getRevenueAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/wallet/revenue`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải doanh thu.");
    return await res.json();
}

export async function createDocumentAPI(data: any) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/documents`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token 
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Không thể khởi tạo tài liệu mới.");
    return await res.json();
}

export async function updateDocumentAPI(id: string, data: any) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/documents/${id}`, {
        method: "PUT",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token 
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Không thể cập nhật tài liệu.");
    return await res.json();
}

export async function getAuthorCouponsAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/coupons`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách mã giảm giá.");
    return await res.json();
}

export async function createAuthorCouponAPI(data: any) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/coupons`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token 
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Không thể tạo mã giảm giá mới.");
    return await res.json();
}

export async function toggleCouponStatusAPI(couponId: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/coupons/${couponId}/toggle`, {
        method: "PATCH",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể cập nhật trạng thái mã giảm giá.");
    return await res.json();
}

export async function deleteCouponAPI(couponId: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/coupons/${couponId}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể xóa mã giảm giá.");
    return await res.json();
}

export async function getCollaborationInvitesAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/collaboration/invites`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách lời mời cộng tác.");
    return await res.json();
}

export async function inviteCollaboratorAPI(documentId: string, email: string, role: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/documents/${documentId}/coauthors`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token 
        },
        body: JSON.stringify({ email, role })
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.message || json.detail || "Không thể gửi lời mời cộng tác.");
    return json;
}

export async function respondToInviteAPI(inviteId: string, status: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/collaboration/respond/${inviteId}?status=${status}`, {
        method: "POST",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể phản hồi lời mời cộng tác.");
    return await res.json();
}

export async function getAuthorAssetsAPI(type: string = "all") {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/assets?asset_type=${type}`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách tài nguyên.");
    return await res.json();
}

export async function uploadAuthorAssetAPI(data: { filename: string, type: string, size_bytes: number, url: string }) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/assets`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token 
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Không thể đăng ký tài nguyên mới.");
    return await res.json();
}

export async function deleteAuthorAssetAPI(assetId: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/assets/${assetId}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể xóa tài nguyên.");
    return await res.json();
}

export async function uploadDocumentAPI(file: File) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_URL}/upload/document`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Lỗi tải tài liệu.");
    return data;
}

export async function deleteAuthorDocumentAPI(docId: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/documents/${docId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể xóa tài liệu.");
    return await res.json();
}

export async function deleteAdminDocumentAPI(docId: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/documents/${docId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể xóa tài liệu hệ thống.");
    return await res.json();
}
export async function getAuthorDemographicsAPI() {
    const token = getToken();
    const res = await fetch(`${API_URL}/analytics/authors/demographics`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải dữ liệu nhân khẩu học.");
    return await res.json();
}
export async function getDocumentReviewsAPI(documentId: string) {
    const res = await fetch(`${API_URL}/reading/${documentId}/reviews`);
    if (!res.ok) throw new Error("Không thể tải đánh giá.");
    return await res.json();
}

export async function getApprovalQueueAPI(skip: number = 0, limit: number = 30) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/moderator/approval-queue?skip=${skip}&limit=${limit}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải hàng chờ phê duyệt.");
    return await res.json();
}

export async function getReportsAPI(status: string = "pending", skip: number = 0, limit: number = 30) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/moderator/reports?status=${status}&skip=${skip}&limit=${limit}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách báo cáo.");
    return await res.json();
}

export async function moderateDocumentAPI(documentId: string, action: string, reason: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/moderator/documents/${documentId}/moderate`, {
        method: "POST",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ action, reason })
    });
    if (!res.ok) throw new Error("Thao tác phê duyệt thất bại.");
    return await res.json();
}

export async function getAdminReportsAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/reports`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách báo cáo.");
    return await res.json();
}

export async function resolveReportAPI(reportId: string, action: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/reports/${reportId}/resolve`, {
        method: "POST",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ action })
    });
    if (!res.ok) throw new Error("Thao tác xử lý báo cáo thất bại.");
    return await res.json();
}

export async function getModeratorActivityAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/moderator/activity`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải nhật ký hoạt động.");
    return await res.json();
}

export async function getAdminUsersAPI(limit: number = 50, offset: number = 0) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/users?limit=${limit}&offset=${offset}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách người dùng.");
    return await res.json();
}

export async function updateUserRoleAPI(userId: string, role: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/users/${userId}/role`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ role })
    });
    if (!res.ok) throw new Error("Cập nhật quyền thất bại.");
    return await res.json();
}

export async function updateUserStatusAPI(userId: string, isActive: boolean) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/users/${userId}/status`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ is_active: isActive })
    });
    if (!res.ok) throw new Error("Cập nhật trạng thái tài khoản thất bại.");
    return await res.json();
}

export async function getAuthorApplicationsAPI(status: string = "PENDING") {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/applications/authors?status=${status}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách đơn ứng tuyển.");
    return await res.json();
}

export async function reviewAuthorApplicationAPI(applicationId: string, status: string, reason: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/applications/authors/${applicationId}/review`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ status, reason })
    });
    if (!res.ok) throw new Error("Thao tác xử lý hồ sơ thất bại.");
    return await res.json();
}

export async function getAdminConfigAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/config`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải cấu hình hệ thống.");
    return await res.json();
}

export async function updateAdminConfigAPI(config: any) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/config`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(config)
    });
    if (!res.ok) throw new Error("Cập nhật cấu hình thất bại.");
    return await res.json();
}

export async function getSystemHealthAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/sys-health`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể kiểm tra sức khỏe hệ thống.");
    return await res.json();
}

export async function getMaintenanceModeAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/maintenance`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải trạng thái bảo trì.");
    return await res.json();
}

export async function toggleMaintenanceModeAPI(enabled: boolean, message: string = "Hệ thống đang bảo trì.") {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/maintenance`, {
        method: "POST",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ enabled, message })
    });
    if (!res.ok) throw new Error("Thao tác chuyển đổi bảo trì thất bại.");
    return await res.json();
}

export async function triggerBackupAPI(action: string = "dump") {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/admin/backup`, {
        method: "POST",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ action })
    });
    if (!res.ok) throw new Error("Khởi tạo sao lưu thất bại.");
    return await res.json();
}

export async function getPrivacySettingsAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/settings/privacy`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải cài đặt riêng tư.");
    return await res.json();
}

export async function updatePrivacySettingsAPI(settings: any) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/settings/privacy`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(settings)
    });
    if (!res.ok) throw new Error("Cập nhật quyền riêng tư thất bại.");
    return await res.json();
}

export async function updateTypographyAPI(typography: any) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/settings/typography`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(typography)
    });
    if (!res.ok) throw new Error("Cập nhật hiển thị thất bại.");
    return await res.json();
}

export async function updateGeneralSettingsAPI(settings: any) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/settings`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ settings })
    });
    if (!res.ok) throw new Error("Cập nhật cài đặt chung thất bại.");
    return await res.json();
}

export async function getSocialFeedAPI(tab: string = "foryou", skip: number = 0, limit: number = 20) {
    const token = getToken();
    const headers: any = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_URL}/social/feed?tab=${tab}&skip=${skip}&limit=${limit}`, { headers });
    if (!res.ok) throw new Error("Không thể tải bảng tin.");
    return await res.json();
}

export async function getSocialStoriesAPI() {
    const token = getToken();
    const headers: any = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_URL}/social/stories`, { headers });
    if (!res.ok) throw new Error("Không thể tải tin tức.");
    return await res.json();
}

export async function getSocialRankingAPI(limit: number = 5) {
    const res = await fetch(`${API_URL}/social/ranking?limit=${limit}`);
    if (!res.ok) throw new Error("Không thể tải bảng xếp hạng.");
    return await res.json();
}

export async function createSocialPostAPI(data: any) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thực hiện.");
    const res = await fetch(`${API_URL}/social/posts`, {
        method: "POST",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Đăng bài viết thất bại.");
    return await res.json();
}

export async function reactToPostAPI(postId: string, reactionType: string = "like") {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thực hiện.");
    const res = await fetch(`${API_URL}/social/posts/${postId}/like?reaction_type=${reactionType}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Thao tác cảm xúc thất bại.");
    return await res.json();
}

export async function deleteSocialPostAPI(postId: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thực hiện.");
    const res = await fetch(`${API_URL}/social/posts/${postId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Xóa bài viết thất bại.");
    return await res.json();
}

export async function uploadSocialMediaAPI(file: File) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thực hiện.");
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_URL}/social/upload-media`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
    });
    if (!res.ok) throw new Error("Tải phương tiện thất bại.");
    return await res.json();
}
export async function createDocumentReviewAPI(documentId: string, rating: number, text: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/reading/${documentId}/review`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({ rating, comment: text })
    });
    if (!res.ok) throw new Error("Đánh giá thất bại.");
    return await res.json();
}
export async function rateDocumentAPI(documentId: string, rating: number, reviewText?: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/reading/${documentId}/rate`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({ rating, review_text: reviewText })
    });
    if (!res.ok) throw new Error("Đánh giá thất bại.");
    return await res.json();
}
export async function uploadImageAPI(file: File) {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_URL}/upload/image`, {
        method: "POST",
        headers: { "Authorization": "Bearer " + token },
        body: formData
    });
    if (!res.ok) return null;
    return await res.json();
}
export async function updateProfileAPI(data: any) {
    const token = getToken();
    const res = await fetch(`${API_URL}/profile/me`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) return null;
    return await res.json();
}

export const postFeedCommentAPI = async (itemId: string, text: string): Promise<any> => {
    const token = getToken();
    const res = await fetch(`${API_URL}/comments`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        },
        body: JSON.stringify({ item_id: itemId, item_type: "post", content: text })
    });
    if (!res.ok) throw new Error("Gửi bình luận thất bại.");
    return res.json();
};

export const forgotPasswordAPI = async (email: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  if (!res.ok) throw new Error("Yêu cầu khôi phục mật khẩu thất bại.");
  return res.json();
};

export const resetPasswordAPI = async (token: string, newPassword: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Đặt lại mật khẩu thất bại.");
  return data.data || data;
};

export const verifyCodeAPI = async (token: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/verify-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Mã xác thực không hợp lệ.");
  return data.data || data;
};

export const shareFeedItemAPI = async (itemId: string, text?: string): Promise<any> => {
  const res = await fetch(`${API_URL}/social/share`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify({ item_id: itemId, text: text || "" })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Chia sẻ thất bại.");
  return data;
};

export const passkeyLoginBeginAPI = async (email: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/login/begin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Bắt đầu đăng nhập Passkey thất bại.");
  return data.data || data;
};

export const passkeyLoginFinishAPI = async (email: string, credential: any): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/login/finish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, credential })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Hoàn tất đăng nhập Passkey thất bại.");
  return data.data || data;
};

export const passkeyRegisterBeginAPI = async (email: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/register/begin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Bắt đầu đăng ký Passkey thất bại.");
  return data.data || data;
};

export const passkeyRegisterFinishAPI = async (email: string, credential: any): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/register/finish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, credential })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Hoàn tất đăng ký Passkey thất bại.");
  return data.data || data;
};
export async function createStatusAPI(text: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/status`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({ content_text: text })
    });
    if (!res.ok) throw new Error("Đăng bài thất bại.");
    return await res.json();
}

export async function createStatusRichAPI(payload: { 
    content: string, 
    poll_options?: string[], 
    media_urls?: string[], 
    tags?: string[],
    location?: string,
    feeling?: string,
    mentions?: string[],
    privacy?: string
}) {
    if (typeof window === "undefined") return;
    const token = getToken();
    const res = await fetch(`${API_URL}/social/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Đăng bài thất bại.");
    return await res.json();
}


export async function getStoriesAPI() {
    if (typeof window === "undefined") return [];
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const headers: any = {};
    headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_URL}/social/stories`, { headers });
    if (!res.ok) throw new Error("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.");
    return await res.json();
}

export async function createStoryAPI(payload: { 
    media_url?: string, 
    text_content?: string, 
    background_color?: string,
    text_color?: string,
    font_style?: string,
    music_url?: string,
    music_title?: string,
    privacy?: string,
    poll_options?: string[],
    quiz_options?: string[],
    correct_option?: number
}) {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/stories`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Không thể đăng tin tức.");
    return await res.json();
}

export async function getMyStoriesAPI() {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/stories/me`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải tin tức của bạn.");
    return await res.json();
}

export async function getArchivedStoriesAPI() {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/stories/me/archive`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải kho lưu trữ tin tức.");
    return await res.json();
}

export async function recordStoryViewAPI(storyId: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/stories/${storyId}/view`, {
        method: "POST",
        headers: { "Authorization": "Bearer " + token }
    });
    return res.ok;
}

export async function reactToStoryAPI(storyId: string, reactionType: string = "heart") {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/stories/${storyId}/react?reaction_type=${reactionType}`, {
        method: "POST",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Thao tác cảm xúc thất bại.");
    return await res.json();
}

export async function archiveStoryAPI(storyId: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/stories/${storyId}/archive`, {
        method: "POST",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Giao thức lưu trữ thất bại.");
    return await res.json();
}

export async function deleteStoryAPI(storyId: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/stories/${storyId}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Xóa tin tức thất bại.");
    return await res.json();
}



export const getFoldersAPI = async (parent_id?: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const params = new URLSearchParams();
  if (parent_id) params.append("parent_id", parent_id);
  
  const res = await fetch(`${API_URL}/documents/folders?${params.toString()}`, {
    headers: { "Authorization": "Bearer " + token }
  });
  if (!res.ok) throw new Error("Failed to fetch folders");
  return res.json();
};

export const createFolderAPI = async (name: string, parent_id: string | null = null) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/folders`, {
    method: 'POST',
    headers: { 
      "Authorization": "Bearer " + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ name, parent_id })
  });
  if (!res.ok) throw new Error("Failed to create folder");
  return res.json();
};


export const deleteDocumentAPI = async (id: string, hard: boolean = false) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}?hard=${hard}`, {
    method: 'DELETE',
    headers: { "Authorization": "Bearer " + token }
  });
  if (!res.ok) throw new Error("Failed to delete document");
  return res.json();
};

export const deleteFolderAPI = async (id: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/folders/${id}`, {
    method: 'DELETE',
    headers: { "Authorization": "Bearer " + token }
  });
  if (!res.ok) throw new Error("Failed to delete folder");
  return res.json();
};


export const getStorageQuotaAPI = async () => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/quota`, { headers: { "Authorization": "Bearer " + token } });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Không thể tải hạn mức dung lượng.");
  return data;
};

export const toggleStarDocumentAPI = async (id: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}/toggle-star`, { method: 'PUT', headers: { "Authorization": "Bearer " + token } });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Thao tác thất bại.");
  return data;
};

export const lockDocumentAPI = async (id: string, password: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}/password`, { 
    method: 'POST', body: password, 
    headers: { "Authorization": "Bearer " + token, 'Content-Type': 'text/plain' } 
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Thiết lập mật khẩu thất bại.");
  return data;
};

export const unlockDocumentAPI = async (id: string, password: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}/unlock`, { 
    method: 'POST', body: password, 
    headers: { "Authorization": "Bearer " + token, 'Content-Type': 'text/plain' } 
  });
  if (!res.ok) throw new Error("Sai mật khẩu");
  return res.json();
};


export async function monetizeDocumentAPI(id: string, price: number) {
    const res = await fetch(`${API_URL}/documents/${id}/monetize?price=${price}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Thiết lập giá thất bại.");
    return data;
}

export async function transferDocumentAPI(id: string, newOwnerId: string) {
    const res = await fetch(`${API_URL}/documents/${id}/transfer?new_owner_id=${newOwnerId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Chuyển nhượng thất bại.");
    return data;
}

export async function getAuditLogsAPI(id: string) {
    const res = await fetch(`${API_URL}/documents/${id}/audit_logs`, {
         headers: { Authorization: `Bearer ${getToken()}` }
    });
    if(!res.ok) return [];
    return res.json();
}


export async function shareToFeedAPI(id: string) {
    const res = await fetch(`${API_URL}/documents/${id}/share-feed`, { method: 'POST', headers: { Authorization: `Bearer ${getToken()}` }});
    return res.json();
}
export async function getDocumentAnalyticsAPI(id: string) {
    const res = await fetch(`${API_URL}/documents/${id}/analytics`, { headers: { Authorization: `Bearer ${getToken()}` }});
    return res.ok ? res.json() : null;
}
export async function getAcademicMetricsAPI(id: string) {
    const res = await fetch(`${API_URL}/documents/${id}/metrics`);
    return res.ok ? res.json() : null;
}

export const createPaymentCheckoutAPI = async (documentId: string, paymentType: string): Promise<any> => {
  const res = await fetch(`${API_URL}/payment/checkout`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify({ document_id: documentId, payment_type: paymentType })
  });
  if (!res.ok) throw new Error("Thanh toán thất bại");
  return await res.json();
};

export async function getBannersAPI() {
    const res = await fetch(`${API_URL}/guest/banners`);
    if (!res.ok) throw new Error("Không thể tải danh sách tiêu điểm.");
    return await res.json();
}

export async function semanticSearchAPI(query: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để sử dụng tính năng này.");
    const res = await fetch(`${API_URL}/reader/search?q=${encodeURIComponent(query)}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Hệ thống AI đang bận, vui lòng thử lại sau.");
    return await res.json();
}

export async function getLibraryAPI() {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");
    const res = await fetch(`${API_URL}/reader/lists`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải thư viện cá nhân");
    return await res.json();
}

export async function exportHighlightsMarkdownAPI(documentId: string) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");
    const res = await fetch(`${API_URL}/reading/documents/${documentId}/highlights/export`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Xuất ghi chú thất bại.");
    return await res.json();
}

export async function getDocumentHighlightsAPI(documentId: string) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");
    const res = await fetch(`${API_URL}/reading/documents/${documentId}/highlights`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Tải ghi chú thất bại.");
    return await res.json();
}


export async function deleteHighlightAPI(highlightId: string) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");
    const res = await fetch(`${API_URL}/reading/highlights/${highlightId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Xóa ghi chú thất bại.");
    return await res.json();
}

export async function updateHighlightNoteAPI(highlightId: string, note: string) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");
    const res = await fetch(`${API_URL}/reading/highlights/${highlightId}/note`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ note })
    });
    if (!res.ok) throw new Error("Cập nhật ghi chú không thành công.");
    return await res.json();
}

export const getAuthorPublicProfileAPI = async (slug: string) => {
    const res = await fetch(`${API_URL}/social/users/${slug}`, {
        headers: { Authorization: `Bearer ${getToken()}` }
    });
    if (!res.ok) throw new Error("Không thể tải hồ sơ tác giả.");
    return await res.json();
};

export const getNotificationsAPI = async () => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải thông báo.");
    return await res.json();
};

export const markNotificationReadAPI = async (id: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/notifications/${id}/read`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể đánh dấu thông báo.");
    return await res.json();
};

export const markAllNotificationsReadAPI = async () => {
    const token = getToken();
    const res = await fetch(`${API_URL}/notifications/mark-all-read`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể đánh dấu tất cả thông báo.");
    return await res.json();
};

export const getNotificationSettingsAPI = async () => {
    const token = getToken();
    const res = await fetch(`${API_URL}/notifications/settings`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải cấu hình thông báo.");
    return await res.json();
};

export const updateNotificationSettingsAPI = async (settings: any) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/notifications/settings`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(settings)
    });
    if (!res.ok) throw new Error("Không thể cập nhật cấu hình thông báo.");
    return await res.json();
};

export const getAuthorRevenueAPI = async () => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/wallet/revenue`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải dữ liệu doanh thu.");
    return await res.json();
};

export const getWalletHistoryAPI = async (skip: number = 0, limit: number = 30, txType?: string) => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (txType) params.append("tx_type", txType);
    const res = await fetch(`${API_URL}/wallet/history/detailed?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải lịch sử giao dịch.");
    return await res.json();
};

export const requestPayoutAPI = async (amount: number) => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/wallet/payout?amount=${amount}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Yêu cầu rút tiền không thành công.");
    return await res.json();
};

export const getWalletBalanceAPI = async () => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/wallet/balance`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải số dư ví.");
    return await res.json();
};

export const redeemVoucherAPI = async (code: string) => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/wallet/redeem-voucher`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ code })
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || err.detail || "Không thể kích hoạt mã quà tặng.");
    }
    return await res.json();
};

export const inviteCoauthorAPI = async (documentId: string, targetUserId: string) => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/coauthor/invite/${documentId}?target_user_id=${targetUserId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể gửi lời mời đồng tác giả.");
    return await res.json();
};

export const searchUsersAPI = async (query: string, limit: number = 10) => {
    const res = await fetch(`${API_URL}/social/search-users?q=${encodeURIComponent(query)}&limit=${limit}`);
    if (!res.ok) throw new Error("Không thể tìm kiếm người dùng.");
    return await res.json();
};

export const getMySeriesAPI = async () => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/series`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách bộ sưu tập.");
    return await res.json();
};

export const createSeriesAPI = async (data: { title: string; description: string; document_ids: string[] }) => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/series`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Không thể tạo bộ sưu tập.");
    return await res.json();
};

export const linkDocumentToSeriesAPI = async (documentId: string, seriesId: string) => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/documents/${documentId}/series?series_id=${seriesId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Liên kết chuỗi tài liệu không thành công.");
    return await res.json();
};

export const getAuthorRevenueAnalyticsAPI = async () => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/author/revenue`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải phân tích doanh thu.");
    return await res.json();
};

export const getConversationsAPI = async () => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/chat/conversations`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách hội thoại.");
    return await res.json();
};

export const getMessagesAPI = async (otherUserId: string, limit: number = 50) => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/chat/messages/${otherUserId}?limit=${limit}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải lịch sử tin nhắn.");
    return await res.json();
};

export const sendMessageAPI = async (receiverId: string, content: string) => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/chat/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ receiver_id: receiverId, content })
    });
    if (!res.ok) throw new Error("Không thể gửi tin nhắn.");
    return await res.json();
};

export const purchaseDocumentAPI = async (documentId: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/wallet/purchase/document/${documentId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || "Không thể thực hiện giao dịch mua tài liệu.");
    }
    return await res.json();
};

export const purchaseChapterAPI = async (documentId: string, chapterId: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/wallet/purchase/chapter/${documentId}/${chapterId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || "Không thể thực hiện giao dịch mua chương.");
    }
    return await res.json();
};

export const depositDLAPI = async (amountVnd: number) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/payment/deposit`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ amount_vnd: amountVnd })
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || "Không thể khởi tạo giao dịch nạp tiền.");
    }
    return await res.json();
};

export const queryRagAPI = async (documentId: string, question: string, usePro: boolean = false) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/rag/chat`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ document_id: documentId, question, usePro })
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || "Không thể nhận phản hồi từ AI.");
    }
    return await res.json();
};

export const ingestDocumentAPI = async (documentId: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/rag/ingest/${documentId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || "Không thể đồng bộ tri thức AI.");
    }
    return await res.json();
};





export const createHighlightAPI = async (documentId: string, text: string, color: string, note?: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/reading/documents/${documentId}/highlights`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ text, color, note })
    });
    return await res.json();
};

export const getHighlightsAPI = async (documentId: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/reading/documents/${documentId}/highlights`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return (await res.json()).data;
};

export const getDocumentVersionsAPI = async (documentId: string) => {
    const res = await fetch(`${API_URL}/author/documents/${documentId}/versions`, {
        headers: { Authorization: `Bearer ${getToken()}` }
    });
    if (!res.ok) throw new Error("Không thể tải lịch sử phiên bản.");
    return (await res.json()).data;
};

export const generateAICoverAPI = async (documentId: string) => {
    const res = await fetch(`${API_URL}/documents/${documentId}/ai-cover`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` }
    });
    if (!res.ok) throw new Error("Không thể khởi tạo ảnh bìa AI.");
    return (await res.json()).data;
};

export const restoreVersionAPI = async (versionId: string) => {
    const res = await fetch(`${API_URL}/author/versions/${versionId}/restore`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` }
    });
    if (!res.ok) throw new Error("Khôi phục phiên bản thất bại.");
    return await res.json();
};

export const getTrashAPI = async () => {
    const res = await fetch(`${API_URL}/author/trash`, {
        headers: { Authorization: `Bearer ${getToken()}` }
    });
    if (!res.ok) throw new Error("Không thể tải thùng rác.");
    return (await res.json()).data;
};

export const restoreDocumentAPI = async (documentId: string) => {
    const res = await fetch(`${API_URL}/author/documents/${documentId}/restore`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` }
    });
    if (!res.ok) throw new Error("Khôi phục tài liệu thất bại.");
    return await res.json();
};

export const softDeleteDocumentAPI = async (documentId: string) => {
    const res = await fetch(`${API_URL}/author/documents/${documentId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` }
    });
    if (!res.ok) throw new Error("Xóa tài liệu thất bại.");
    return await res.json();
};

export const requestPayoutDetailedAPI = async (amount: number, bankInfo: any) => {
    const res = await fetch(`${API_URL}/author/payout`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            Authorization: `Bearer ${getToken()}` 
        },
        body: JSON.stringify({ amount, bank_info: bankInfo })
    });
    if (!res.ok) throw new Error("Yêu cầu rút tiền thất bại.");
    return await res.json();
};

export const applyAuthorAPI = async (motivation: string) => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/reader/apply-author`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ motivation })
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Không thể gửi đơn ứng tuyển.");
    }
    return await res.json();
};

export async function getAIRecommendationsAPI(limit: number = 10) {
    const token = getToken();
    const headers: any = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_URL}/documents/recommendations/ai?limit=${limit}`, { headers });
    if (!res.ok) throw new Error("Không thể tải gợi ý từ AI.");
    return await res.json();
}

export function formatError(detail: any): string {
    if (!detail) return "Đã có lỗi xảy ra. Vui lòng thử lại.";
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        return detail.map(d => d.msg || d.message || JSON.stringify(d)).join(', ');
    }
    if (typeof detail === 'object') {
        return detail.msg || detail.message || detail.detail || JSON.stringify(detail);
    }
    return String(detail);
}
