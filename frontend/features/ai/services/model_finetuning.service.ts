import { API_URL, getToken } from "@/features/auth/services/user_authentication.service";

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
  const res = await fetch(`${API_URL}/finetune/dataset`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ name, description, source }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const listDatasetsAPI = async () => {
  const res = await fetch(`${API_URL}/finetune/dataset`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const getDatasetAPI = async (datasetId: string) => {
  const res = await fetch(`${API_URL}/finetune/dataset/${datasetId}`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const deleteDatasetAPI = async (datasetId: string) => {
  const res = await fetch(`${API_URL}/finetune/dataset/${datasetId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const addSamplesAPI = async (datasetId: string, samples: any[]) => {
  const res = await fetch(`${API_URL}/finetune/dataset/${datasetId}/sample`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ samples }),
  });
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
    `${API_URL}/finetune/dataset/${datasetId}/sample?skip=${skip}&limit=${limit}`,
    { headers: authHeaders() },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const deleteSampleAPI = async (datasetId: string, sampleId: string) => {
  const res = await fetch(
    `${API_URL}/finetune/dataset/${datasetId}/sample/${sampleId}`,
    { method: "DELETE", headers: authHeaders() },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const importFromFeedbackAPI = async () => {
  const res = await fetch(`${API_URL}/finetune/input/phan-hoi`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const importFromDocumentsAPI = async (documentIds: string[]) => {
  const res = await fetch(`${API_URL}/finetune/input/tai-lieu`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ document_ids: documentIds }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const createJobAPI = async (config: any) => {
  const res = await fetch(`${API_URL}/finetune/jobs`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(config),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const startTrainingAPI = async (jobId: string) => {
  const res = await fetch(`${API_URL}/finetune/jobs/${jobId}/start`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const listJobsAPI = async () => {
  const res = await fetch(`${API_URL}/finetune/jobs`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const getJobAPI = async (jobId: string) => {
  const res = await fetch(`${API_URL}/finetune/jobs/${jobId}`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const cancelJobAPI = async (jobId: string) => {
  const res = await fetch(`${API_URL}/finetune/jobs/${jobId}/huy`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const deployModelAPI = async (jobId: string) => {
  const res = await fetch(`${API_URL}/finetune/jobs/${jobId}/deploy`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};

export const evaluateModelAPI = async (jobId: string, testSamples: any[]) => {
  const res = await fetch(`${API_URL}/finetune/jobs/${jobId}/danh-gia`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ test_samples: testSamples }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message);
  return data;
};
