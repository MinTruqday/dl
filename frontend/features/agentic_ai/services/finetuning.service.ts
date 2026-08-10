import {
  API_URL,
  getToken,
} from "@/features/authentication/services/session.service";

const authHeaders = () => {
  const token = getToken();
  if (!token)
    throw new Error(
      "Phiên đăng nhập đã hết hạn",
    );
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
};

export const createDatasetAPI = async (
  name: string,
  description: string,
  source: string = "manual",
) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tap-du-lieu`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ name, description, source }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tạo tập dữ liệu",
    );
  return data;
};

export const listDatasetsAPI = async () => {
  const res = await fetch(`${API_URL}/tinh-chinh/tap-du-lieu`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải danh sách tập dữ liệu",
    );
  return data;
};

export const getDatasetAPI = async (datasetId: string) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tap-du-lieu/${datasetId}`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải chi tiết tập dữ liệu",
    );
  return data;
};

export const deleteDatasetAPI = async (datasetId: string) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tap-du-lieu/${datasetId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể xóa tập dữ liệu",
    );
  return data;
};

export const addSamplesAPI = async (datasetId: string, samples: any[]) => {
  const res = await fetch(
    `${API_URL}/tinh-chinh/tap-du-lieu/${datasetId}/mau-thu`,
    {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ samples }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể thêm mẫu vào tập dữ liệu",
    );
  return data;
};

export const getSamplesAPI = async (
  datasetId: string,
  skip: number = 0,
  limit: number = 50,
) => {
  const res = await fetch(
    `${API_URL}/tinh-chinh/tap-du-lieu/${datasetId}/mau-thu?skip=${skip}&limit=${limit}`,
    { headers: authHeaders() },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải các mẫu dữ liệu",
    );
  return data;
};

export const deleteSampleAPI = async (datasetId: string, sampleId: string) => {
  const res = await fetch(
    `${API_URL}/tinh-chinh/tap-du-lieu/${datasetId}/mau-thu/${sampleId}`,
    { method: "DELETE", headers: authHeaders() },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể xóa mẫu dữ liệu",
    );
  return data;
};

export const importFromFeedbackAPI = async () => {
  const res = await fetch(`${API_URL}/tinh-chinh/ket-nhap/phan-hoi`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message ||
        "Không thể nhập mẫu từ phản hồi",
    );
  return data;
};

export const importFromDocumentsAPI = async (documentIds: string[]) => {
  const res = await fetch(`${API_URL}/tinh-chinh/ket-nhap/tai-lieu`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ document_ids: documentIds }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message ||
        "Không thể nhập mẫu từ tài liệu",
    );
  return data;
};

export const createJobAPI = async (config: any) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tien-trinh`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(config),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tạo tiến trình tinh chỉnh",
    );
  return data;
};

export const startTrainingAPI = async (jobId: string) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tien-trinh/${jobId}/bat-dau`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể bắt đầu tinh chỉnh",
    );
  return data;
};

export const listJobsAPI = async () => {
  const res = await fetch(`${API_URL}/tinh-chinh/tien-trinh`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải các tiến trình tinh chỉnh",
    );
  return data;
};

export const getJobAPI = async (jobId: string) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tien-trinh/${jobId}`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải chi tiết tiến trình",
    );
  return data;
};

export const cancelJobAPI = async (jobId: string) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tien-trinh/${jobId}/huy-bo`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể hủy tiến trình");
  return data;
};

export const deployModelAPI = async (jobId: string) => {
  const res = await fetch(
    `${API_URL}/tinh-chinh/tien-trinh/${jobId}/trien-khai`,
    {
      method: "POST",
      headers: authHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể triển khai mô hình",
    );
  return data;
};

export const evaluateModelAPI = async (jobId: string, testSamples: any[]) => {
  const res = await fetch(
    `${API_URL}/tinh-chinh/tien-trinh/${jobId}/danh-gia`,
    {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ test_samples: testSamples }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể đánh giá mô hình",
    );
  return data;
};
