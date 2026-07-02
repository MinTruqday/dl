import {
  API_URL,
  getToken,
} from "@/features/auth/services/user_authentication.service";

const authHeaders = () => {
  const token = getToken();
  if (!token) throw new Error("Vui lòng đăng nhập");
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
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const listDatasetsAPI = async () => {
  const res = await fetch(`${API_URL}/tinh-chinh/tap-du-lieu`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const getDatasetAPI = async (datasetId: string) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tap-du-lieu/${datasetId}`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const deleteDatasetAPI = async (datasetId: string) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tap-du-lieu/${datasetId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const addSamplesAPI = async (datasetId: string, samples: any[]) => {
  const res = await fetch(
    `${API_URL}/tinh-chinh/tap-du-lieu/${datasetId}/sample`,
    {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ samples }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const getSamplesAPI = async (
  datasetId: string,
  skip: number = 0,
  limit: number = 50,
) => {
  const res = await fetch(
    `${API_URL}/tinh-chinh/tap-du-lieu/${datasetId}/sample?skip=${skip}&limit=${limit}`,
    { headers: authHeaders() },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const deleteSampleAPI = async (datasetId: string, sampleId: string) => {
  const res = await fetch(
    `${API_URL}/tinh-chinh/tap-du-lieu/${datasetId}/sample/${sampleId}`,
    { method: "DELETE", headers: authHeaders() },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const importFromFeedbackAPI = async () => {
  const res = await fetch(`${API_URL}/tinh-chinh/dau-vao/phan-hoi`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const importFromDocumentsAPI = async (documentIds: string[]) => {
  const res = await fetch(`${API_URL}/tinh-chinh/dau-vao/tai-lieu`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ document_ids: documentIds }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const createJobAPI = async (config: any) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tien-trinh`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(config),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const startTrainingAPI = async (jobId: string) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tien-trinh/${jobId}/start`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const listJobsAPI = async () => {
  const res = await fetch(`${API_URL}/tinh-chinh/tien-trinh`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const getJobAPI = async (jobId: string) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tien-trinh/${jobId}`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const cancelJobAPI = async (jobId: string) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tien-trinh/${jobId}/huy`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const deployModelAPI = async (jobId: string) => {
  const res = await fetch(`${API_URL}/tinh-chinh/tien-trinh/${jobId}/deploy`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
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
  if (!res.ok) throw new Error(data.message);
  return data;
};
