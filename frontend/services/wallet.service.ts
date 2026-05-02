import { API_URL, getAuthHeaders } from './auth.service';

export async function getWalletBalanceAPI() {
    const res = await fetch(`${API_URL}/wallet/balance`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error("Không thể tải số dư ví.");
    return await res.json();
}

export async function getWalletHistoryAPI() {
    const res = await fetch(`${API_URL}/wallet/history`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error("Không thể tải lịch sử giao dịch.");
    return await res.json();
}

export async function redeemVoucherAPI(code: string) {
    const res = await fetch(`${API_URL}/wallet/redeem?code=${code}`, {
        method: "POST",
        headers: getAuthHeaders()
    });
    if (!res.ok) {
        const json = await res.json();
        throw new Error(json.message || "Voucher không hợp lệ.");
    }
    return await res.json();
}

export async function depositDLAPI(amount: number) {
    const res = await fetch(`${API_URL}/wallet/deposit?amount=${amount}`, {
        method: "POST",
        headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error("Khởi tạo thanh toán thất bại.");
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
    const res = await fetch(`${API_URL}/wallet/revenue`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải thông số phân tích.");
    return await res.json();
}