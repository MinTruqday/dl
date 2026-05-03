import { API_URL, getAuthHeaders, getToken } from './auth.service';

export const getWalletBalanceAPI = async () => {
    const res = await fetch(`${API_URL}/wallet/balance`, {
        headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error("Không thể tải số dư ví.");
    return await res.json();
};

export const depositDLAPI = async (amountVnd: number) => {
    const res = await fetch(`${API_URL}/payment/deposit`, {
        method: "POST",
        headers: { 
            ...getAuthHeaders(),
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ amount_vnd: amountVnd })
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || "Không thể khởi tạo giao dịch nạp tiền.");
    }
    return await res.json();
};

export const redeemVoucherAPI = async (code: string) => {
    const res = await fetch(`${API_URL}/wallet/redeem-voucher`, {
        method: "POST",
        headers: { 
            ...getAuthHeaders(),
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ code })
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || err.detail || "Không thể kích hoạt mã quà tặng.");
    }
    return await res.json();
};

export const purchaseChapterAPI = async (documentId: string, chapterId: string) => {
    const res = await fetch(`${API_URL}/wallet/purchase/chapter/${documentId}/${chapterId}`, {
        method: "POST",
        headers: getAuthHeaders()
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || "Không thể thực hiện giao dịch mua chương.");
    }
    return await res.json();
}

export async function getWalletHistoryAPI() {
    const res = await fetch(`${API_URL}/wallet/history`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error("Không thể tải lịch sử giao dịch.");
    return await res.json();
}

export async function voteItemAPI(itemId: string, itemType: string, amount: number) {
    const res = await fetch(`${API_URL}/wallet/vote`, {
        method: "POST",
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId, item_type: itemType, amount })
    });
    if (!res.ok) throw new Error("Bình chọn/Tặng thưởng thất bại.");
    return await res.json();
}


export async function getAuthorStatsAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/wallet/revenue/`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải thông số phân tích.");
    return await res.json();
}

export async function requestPayoutAPI(amount: number, note: string = "") {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/wallet/payout/`, {
        method: "POST",
        headers: { 
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ amount, note })
    });
    if (!res.ok) throw new Error("Yêu cầu tất toán thất bại.");
    return await res.json();
}

export async function getDetailedHistoryAPI() {
    const res = await fetch(`${API_URL}/wallet/history/`, { 
        headers: getAuthHeaders() 
    });
    if (!res.ok) throw new Error("Không thể tải lịch sử chi tiết.");
    return await res.json();
}