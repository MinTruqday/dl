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

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Đăng nhập thất bại.");
    return data;
}

export async function register(email: string, password: string, full_name: string, slug: string, agreed_to_terms: boolean) {
    const res = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, full_name, slug, agreed_to_terms })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Đăng ký thất bại.");
    return data;
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
    }
}

export function removeToken() {
    if (typeof window !== 'undefined') {
        localStorage.removeItem('doclib_token');
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
            return await res.json();
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

export async function createDocumentAPI(title: string, slug: string, description: string) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");

    const res = await fetch(`${API_URL}/documents/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title,
            slug,
            description,
            content_type: "latex",
            status: "draft",
            tags: [],
            content: ""
        })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Tạo tài liệu thất bại.");
    return data;
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

export async function getDocumentsAPI(search?: string, sortBy?: string, category?: string, tag?: string) {
    const token = getToken();
    let url = `${API_URL}/documents/`;
    const params = new URLSearchParams();
    if (search) params.append("q", search);
    if (sortBy) params.append("sort_by", sortBy);
    if (category) params.append("category", category);
    if (tag) params.append("tag", tag);
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
export async function getTrendingDocumentsAPI(limit: number = 5) {
    const res = await fetch(`${API_URL}/documents/trending?limit=${limit}`);
    if (!res.ok) throw new Error("Không thể tải xu hướng.");
    return await res.json();
}
export async function getFeaturedAuthorsAPI(limit: number = 5) {
    const res = await fetch(`${API_URL}/auth/authors/featured?limit=${limit}`);
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
    const res = await fetch(`${API_URL}/reading/history`, {
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
    const res = await fetch(`${API_URL}/reading/history`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.");
    return await res.json();
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
    const res = await fetch(`${API_URL}/analytics/author/stats`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải thông số phân tích.");
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
  if (!res.ok) throw new Error("Đặt lại mật khẩu thất bại.");
  return res.json();
};

export const shareFeedItemAPI = async (itemId: string, text?: string): Promise<any> => {
  const res = await fetch(`${API_URL}/social/share`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify({ item_id: itemId, text: text || "" })
  });
  return res.json();
};

export const passkeyLoginBeginAPI = async (email: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/login/begin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  if (!res.ok) throw new Error("Bắt đầu đăng nhập Passkey thất bại.");
  return res.json();
};

export const passkeyLoginFinishAPI = async (email: string, credential_id: string, client_data: any, authenticator_data: any, signature: string, user_handle: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/login/finish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, credential_id, client_data, authenticator_data, signature, user_handle })
  });
  if (!res.ok) throw new Error("Hoàn tất đăng nhập Passkey thất bại.");
  return res.json();
};

export const passkeyRegisterBeginAPI = async (email: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/register/begin`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify({ email })
  });
  if (!res.ok) throw new Error("Bắt đầu đăng ký Passkey thất bại.");
  return res.json();
};

export const passkeyRegisterFinishAPI = async (email: string, credential_id: string, credential_public_key: string, client_data: any, attestation_object: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/register/finish`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify({ email, credential_id, credential_public_key, client_data, attestation_object })
  });
  if (!res.ok) throw new Error("Hoàn tất đăng ký Passkey thất bại.");
  return res.json();
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

export async function votePollAPI(statusId: string, optionIndex: number) {
    if (typeof window === "undefined") return;
    const token = getToken();
    const res = await fetch(`${API_URL}/social/status/${statusId}/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify({ option_index: optionIndex })
    });
    if (!res.ok) throw new Error("Vote failed");
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
    privacy?: string
}) {
    if (typeof window === "undefined") return;
    const token = getToken();
    const res = await fetch(`${API_URL}/social/story`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Story failed");
    return await res.json();
}

export const getDocumentsAPI = async (folder_id?: string, search?: string, is_starred?: boolean, fmt?: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const params = new URLSearchParams();
  if (folder_id) params.append("folder_id", folder_id);
  if (search) params.append("search", search);
  if (is_starred) params.append("is_starred", "true");
  if (fmt && fmt !== "all") params.append("fmt", fmt);
  
  const res = await fetch(`${API_URL}/documents/?${params.toString()}`, {
    headers: { "Authorization": "Bearer " + token }
  });
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
};

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

export const uploadDocumentAPI = async (file: File, title: string, folder_id: string | null = null, tags: string[] = []) => {
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", title);
  if (folder_id) formData.append("folder_id", folder_id);
  if (tags.length > 0) formData.append("tags", tags.join(','));

  const res = await fetch(`${API_URL}/documents/upload`, {
    method: 'POST',
    headers: { "Authorization": "Bearer " + token },
    body: formData
  });
  if (!res.ok) throw new Error("Failed to upload document");
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
  return res.json();
};

export const toggleStarDocumentAPI = async (id: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}/toggle-star`, { method: 'PUT', headers: { "Authorization": "Bearer " + token } });
  return res.json();
};

export const lockDocumentAPI = async (id: string, password: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}/password`, { 
    method: 'POST', body: password, 
    headers: { "Authorization": "Bearer " + token, 'Content-Type': 'text/plain' } 
  });
  return res.json();
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
    return res.json();
}

export async function transferDocumentAPI(id: string, newOwnerId: string) {
    const res = await fetch(`${API_URL}/documents/${id}/transfer?new_owner_id=${newOwnerId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` }
    });
    return res.json();
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
  return res.json();
};

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
    if (!res.ok) throw new Error("Không thể tải kệ sách");
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

export async function createHighlightAPI(documentId: string, data: { text: string; color: string; chapter_slug?: string; start_offset?: number; end_offset?: number; note?: string }) {
    const token = getToken();
    if (!token) throw new Error("Không có quyền truy cập.");
    const res = await fetch(`${API_URL}/reading/documents/${documentId}/highlights`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Tạo ghi chú thất bại.");
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
    if (!res.ok) throw new Error("Cập nhật ghi chú thất bại.");
    return await res.json();
}

export const getAuthorPublicProfileAPI = async (slug: string) => ({});
export const getNotificationsAPI = async () => [];
export const markNotificationReadAPI = async (id: string) => ({});
export const getAuthorRevenueAPI = async () => ({});
export const getMySeriesAPI = async () => [];
export const getMyDocumentsAPI = async () => [];
export const createSeriesAPI = async (data: any) => ({});
