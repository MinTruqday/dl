var _a;
const configuredApiUrl = (_a = process.env.NEXT_PUBLIC_API_URL) === null || _a === void 0 ? void 0 : _a.trim();
export const API_URL = configuredApiUrl || "http://localhost:8000";
export function getToken() {
    if (typeof window === "undefined")
        return null;
    const token = localStorage.getItem("doclib_token");
    return token && token !== "null" && token !== "undefined" ? token : null;
}
export function getAuthHeaders() {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}
let refreshPromise = null;
function applyToken(token) {
    localStorage.setItem("doclib_token", token);
    document.cookie = `token=${token}; path=/; max-age=604800; SameSite=Lax`;
}
export async function refreshAccessToken() {
    if (typeof window === "undefined")
        return null;
    if (!refreshPromise) {
        refreshPromise = fetch(`${API_URL}/xac-thuc/lam-moi-phien`, {
            method: "POST",
            credentials: "include",
        })
            .then(async (response) => {
            var _a;
            if (!response.ok)
                return null;
            const body = await response.json();
            const token = (_a = body === null || body === void 0 ? void 0 : body.data) === null || _a === void 0 ? void 0 : _a.access_token;
            if (typeof token !== "string" || !token)
                return null;
            applyToken(token);
            return token;
        })
            .catch(() => null)
            .finally(() => {
            refreshPromise = null;
        });
    }
    return refreshPromise;
}
export async function authenticatedFetch(input, init = {}) {
    const headers = new Headers(init.headers);
    const token = getToken();
    if (token)
        headers.set("Authorization", `Bearer ${token}`);
    const request = Object.assign(Object.assign({}, init), { headers, credentials: init.credentials || "include" });
    const response = await fetch(input, request);
    if (response.status !== 401)
        return response;
    const replacement = await refreshAccessToken();
    if (!replacement)
        return response;
    headers.set("Authorization", `Bearer ${replacement}`);
    return fetch(input, Object.assign(Object.assign({}, request), { headers }));
}
