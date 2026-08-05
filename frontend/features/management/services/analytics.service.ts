import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export interface AuthorOverviewData {
  total_revenue: number;
  total_views: number;
  total_purchases: number;
  conversion_rate: number;
  unique_buyers: number;
  total_documents: number;
  available_balance: number;
  reward_points: number;
}

export interface TimeseriesItem {
  date: string;
  revenue: number;
  purchases: number;
}

export interface DocumentAnalyticsItem {
  id: string;
  slug: string;
  title: string;
  views: number;
  price: number;
  purchases: number;
  revenue: number;
  conversion_rate: number;
  revenue_percentage: number;
  is_drm: boolean;
  last_purchased_at?: string;
  created_at?: string;
}

export interface DocumentsAnalyticsResponse {
  items: DocumentAnalyticsItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SystemAnalyticsData {
  total_revenue: number;
  total_purchases: number;
  total_views: number;
  total_documents: number;
  total_users: number;
  total_authors: number;
  top_authors: Array<{
    author_id: string;
    author_name: string;
    revenue: number;
    purchases: number;
  }>;
  top_documents: Array<{
    document_id: string;
    title: string;
    revenue: number;
    purchases: number;
  }>;
}

export interface DocumentQueryParams {
  search?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
  from_date?: string;
  to_date?: string;
}

export async function getAuthorOverviewAPI(fromDate?: string, toDate?: string) {
  const searchParams = new URLSearchParams();
  if (fromDate) searchParams.append("from_date", fromDate);
  if (toDate) searchParams.append("to_date", toDate);
  const queryStr = searchParams.toString();
  const url = `${API_URL}/phan-tich/tong-quan${queryStr ? `?${queryStr}` : ""}`;
  const res = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.message || "Không thể tải tổng quan phân tích");
  }
  return data;
}

export async function getAuthorTrendsAPI(days: number = 30, fromDate?: string, toDate?: string) {
  const searchParams = new URLSearchParams();
  searchParams.append("days", String(days));
  if (fromDate) searchParams.append("from_date", fromDate);
  if (toDate) searchParams.append("to_date", toDate);
  const queryStr = searchParams.toString();
  const url = `${API_URL}/phan-tich/xu-huong?${queryStr}`;
  const res = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.message || "Không thể tải số liệu xu hướng");
  }
  return data;
}

export async function getAuthorDocumentsAnalyticsAPI(params: DocumentQueryParams = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.append(key, String(value));
    }
  });
  const queryStr = searchParams.toString();
  const url = `${API_URL}/phan-tich/tai-lieu${queryStr ? `?${queryStr}` : ""}`;
  const res = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.message || "Không thể tải số liệu tài liệu");
  }
  return data;
}

export async function getSystemAnalyticsAPI(fromDate?: string, toDate?: string) {
  const searchParams = new URLSearchParams();
  if (fromDate) searchParams.append("from_date", fromDate);
  if (toDate) searchParams.append("to_date", toDate);
  const queryStr = searchParams.toString();
  const url = `${API_URL}/phan-tich/he-thong${queryStr ? `?${queryStr}` : ""}`;
  const res = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.message || "Không thể tải phân tích toàn hệ thống");
  }
  return data;
}

export async function exportAnalyticsAPI(params: {
  format?: string;
  scope?: string;
  from_date?: string;
  to_date?: string;
}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.append(key, String(value));
    }
  });
  const queryStr = searchParams.toString();
  const url = `${API_URL}/phan-tich/ket-xuat${queryStr ? `?${queryStr}` : ""}`;
  const res = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.message || "Không thể kết xuất báo cáo phân tích");
  }
  return data;
}
