"use client";

import React, { useState, useEffect } from "react";
import {
  Plus,
  Database,
  Play,
  CheckCircle,
  Clock,
  X,
  FileText,
  Upload,
} from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import { useToast } from "../../../context/ToastContext";
import {
  listDatasetsAPI,
  listJobsAPI,
  createDatasetAPI,
  createJobAPI,
  startTrainingAPI,
  importFromFeedbackAPI,
} from "../../../services/finetune.service";

export default function FineTuningPage() {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [datasets, setDatasets] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [showNewDataset, setShowNewDataset] = useState(false);
  const [showNewJob, setShowNewJob] = useState(false);
  const [newDatasetName, setNewDatasetName] = useState("");
  const [newDatasetDesc, setNewDatasetDesc] = useState("");

  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [jobConfig, setJobConfig] = useState({
    base_model: "",
    epochs: 3,
    learning_rate: 0.0002,
    batch_size: 4,
    method: "lora",
    lora_rank: 16,
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [dsRes, jobsRes] = await Promise.all([
        listDatasetsAPI(),
        listJobsAPI(),
      ]);
      setDatasets(dsRes.data || []);
      setJobs(jobsRes.data || []);
    } catch (err: any) {
      showToast(err.message || "Không thể tải dữ liệu", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user]);

  useEffect(() => {
    const hasRunning = jobs.some((j) => j.status === "running");
    if (!hasRunning) return;
    const interval = setInterval(async () => {
      try {
        const res = await listJobsAPI();
        setJobs(res.data || []);
      } catch {}
    }, 3000);
    return () => clearInterval(interval);
  }, [jobs]);

  const handleCreateDataset = async () => {
    if (!newDatasetName.trim()) {
      showToast("Vui lòng nhập tên tập dữ liệu", "error");
      return;
    }
    try {
      await createDatasetAPI(newDatasetName, newDatasetDesc);
      showToast("Tạo tập dữ liệu thành công", "success");
      setShowNewDataset(false);
      setNewDatasetName("");
      setNewDatasetDesc("");
      loadData();
    } catch (err: any) {
      showToast(err.message || "Lỗi tạo tập dữ liệu", "error");
    }
  };

  const handleCreateJob = async () => {
    if (!selectedDatasetId) {
      showToast("Vui lòng chọn tập dữ liệu", "error");
      return;
    }
    try {
      const res = await createJobAPI({
        dataset_id: selectedDatasetId,
        ...jobConfig,
      });
      showToast("Tạo công việc thành công", "success");
      setShowNewJob(false);

      const jobId = res.data?._id;
      if (jobId) {
        await startTrainingAPI(jobId);
        showToast("Đã bắt đầu huấn luyện", "success");
      }
      loadData();
    } catch (err: any) {
      showToast(err.message || "Lỗi tạo công việc", "error");
    }
  };

  const handleImportFeedback = async () => {
    try {
      showToast("Đang thu thập phản hồi", "success");
      const res = await importFromFeedbackAPI();
      showToast(
        `Đã tạo tập dữ liệu với ${res.data?.imported || 0} mẫu`,
        "success",
      );
      loadData();
    } catch (err: any) {
      showToast(err.message || "Lỗi nhập dữ liệu", "error");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-green-600 bg-green-50";
      case "running":
        return "text-blue-600 bg-blue-50";
      case "failed":
        return "text-red-600 bg-red-50";
      case "deployed":
        return "text-purple-600 bg-purple-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed":
        return "Đã hoàn thành";
      case "running":
        return "Đang huấn luyện";
      case "failed":
        return "Thất bại";
      case "deployed":
        return "Đã triển khai";
      case "pending":
        return "Chờ xử lý";
      default:
        return status;
    }
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-300">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Tinh chỉnh Mô hình AI
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Huấn luyện trợ lý AI với dữ liệu cá nhân của bạn
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleImportFeedback}
            className="px-4 py-2 bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400 rounded-xl hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors flex items-center gap-2 font-medium"
          >
            <Upload className="w-4 h-4" />
            Nhập từ Phản hồi
          </button>
          <button
            onClick={() => setShowNewJob(true)}
            className="px-4 py-2 bg-black text-white dark:bg-white dark:text-black rounded-xl hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors flex items-center gap-2 font-medium"
          >
            <Play className="w-4 h-4" />
            Huấn luyện mới
          </button>
        </div>
      </div>

      <div
        className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-8 duration-300"
        style={{ animationDelay: "150ms", animationFillMode: "both" }}
      >
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
            <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-500" />
              Tập dữ liệu ({datasets.length})
            </h2>
            <button
              onClick={() => setShowNewDataset(true)}
              className="p-1.5 text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>

          <div className="p-4">
            {loading ? (
              <div className="flex justify-center p-8">
                <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : datasets.length === 0 ? (
              <div className="text-center p-8 text-gray-500 dark:text-gray-400">
                Chưa có tập dữ liệu nào. Vui lòng tạo mới hoặc nhập từ dữ liệu
                có sẵn.
              </div>
            ) : (
              <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                {datasets.map((ds) => (
                  <div
                    key={ds._id}
                    className="p-3 border border-gray-100 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-1">
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        {ds.name}
                      </h3>
                      <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-md text-gray-600 dark:text-gray-300">
                        {ds.sample_count} mẫu
                      </span>
                    </div>
                    {ds.description && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-1">
                        {ds.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="p-4 border-b border-gray-100 dark:border-gray-700">
            <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-green-500" />
              Tiến trình Huấn luyện ({jobs.length})
            </h2>
          </div>

          <div className="p-4">
            {loading ? (
              <div className="flex justify-center p-8">
                <div className="w-6 h-6 border-2 border-green-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-gray-500 dark:text-gray-400">
                Chưa có tiến trình huấn luyện nào.
              </div>
            ) : (
              <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                {jobs.map((job) => (
                  <div
                    key={job._id}
                    className="p-4 border border-gray-100 dark:border-gray-700 rounded-xl"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {job.job_name}
                        </h3>
                        <p className="text-xs text-gray-500 mt-1">
                          Mô hình gốc: {job.base_model}
                        </p>
                      </div>
                      <span
                        className={`text-xs px-2 py-1 rounded-md font-medium ${getStatusColor(job.status)}`}
                      >
                        {getStatusText(job.status)}
                      </span>
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                        <span>Tiến độ</span>
                        <span>{job.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full transition-all duration-500 ${job.status === "failed" ? "bg-red-500" : "bg-green-500"}`}
                          style={{ width: `${job.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    {job.current_loss !== undefined &&
                      job.current_loss !== null && (
                        <div className="mt-3 text-xs text-gray-500 dark:text-gray-400 flex items-center gap-4 flex-wrap">
                          <span>
                            Epoch: {job.current_epoch}/{job.epochs}
                          </span>
                          <span>
                            Loss:{" "}
                            {typeof job.current_loss === "number"
                              ? job.current_loss.toFixed(6)
                              : job.current_loss}
                          </span>
                          {job.best_loss !== undefined &&
                            job.best_loss !== null && (
                              <span>
                                Best:{" "}
                                {typeof job.best_loss === "number"
                                  ? job.best_loss.toFixed(6)
                                  : job.best_loss}
                              </span>
                            )}
                          {job.method && (
                            <span className="px-1.5 py-0.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded">
                              {job.method.toUpperCase()}
                              {job.lora_rank ? ` r${job.lora_rank}` : ""}
                            </span>
                          )}
                        </div>
                      )}
                    {job.merged_model_name && (
                      <div className="mt-2 text-xs text-green-600 dark:text-green-400 font-mono">
                        {job.merged_model_name}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {showNewDataset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md overflow-hidden shadow-xl animate-scale-in">
            <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <h3 className="font-semibold text-gray-900 dark:text-white">
                Tạo Tập Dữ Liệu
              </h3>
              <button
                onClick={() => setShowNewDataset(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tên tập dữ liệu
                </label>
                <input
                  type="text"
                  value={newDatasetName}
                  onChange={(e) => setNewDatasetName(e.target.value)}
                  className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-gray-900 dark:text-white"
                  placeholder="VD: Dữ liệu luật lao động"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Mô tả (Tùy chọn)
                </label>
                <textarea
                  value={newDatasetDesc}
                  onChange={(e) => setNewDatasetDesc(e.target.value)}
                  className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-gray-900 dark:text-white resize-none h-24"
                  placeholder="Mô tả ngắn gọn về tập dữ liệu"
                />
              </div>
            </div>
            <div className="p-4 border-t border-gray-100 dark:border-gray-700 flex justify-end gap-2">
              <button
                onClick={() => setShowNewDataset(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl font-medium"
              >
                Hủy
              </button>
              <button
                onClick={handleCreateDataset}
                className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium"
              >
                Tạo mới
              </button>
            </div>
          </div>
        </div>
      )}

      {showNewJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md overflow-hidden shadow-xl animate-scale-in">
            <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <h3 className="font-semibold text-gray-900 dark:text-white">
                Bắt đầu Huấn luyện
              </h3>
              <button
                onClick={() => setShowNewJob(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Chọn tập dữ liệu
                </label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-gray-900 dark:text-white"
                >
                  <option value="">-- Chọn tập dữ liệu --</option>
                  {datasets.map((ds) => (
                    <option key={ds._id} value={ds._id}>
                      {ds.name} ({ds.sample_count} mẫu)
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Số Epochs
                  </label>
                  <input
                    type="number"
                    value={jobConfig.epochs}
                    onChange={(e) =>
                      setJobConfig({
                        ...jobConfig,
                        epochs: parseInt(e.target.value),
                      })
                    }
                    className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl outline-none text-gray-900 dark:text-white"
                    min="1"
                    max="10"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Batch Size
                  </label>
                  <input
                    type="number"
                    value={jobConfig.batch_size}
                    onChange={(e) =>
                      setJobConfig({
                        ...jobConfig,
                        batch_size: parseInt(e.target.value),
                      })
                    }
                    className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl outline-none text-gray-900 dark:text-white"
                    min="1"
                    max="16"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Phương pháp
                  </label>
                  <select
                    value={jobConfig.method}
                    onChange={(e) =>
                      setJobConfig({ ...jobConfig, method: e.target.value })
                    }
                    className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-gray-900 dark:text-white"
                  >
                    <option value="lora">LoRA</option>
                    <option value="qlora">QLoRA</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    LoRA Rank (r)
                  </label>
                  <input
                    type="number"
                    value={jobConfig.lora_rank}
                    onChange={(e) =>
                      setJobConfig({
                        ...jobConfig,
                        lora_rank: parseInt(e.target.value),
                      })
                    }
                    className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl outline-none text-gray-900 dark:text-white"
                    min="4"
                    max="128"
                    step="4"
                  />
                </div>
              </div>
            </div>
            <div className="p-4 border-t border-gray-100 dark:border-gray-700 flex justify-end gap-2">
              <button
                onClick={() => setShowNewJob(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl font-medium"
              >
                Hủy
              </button>
              <button
                onClick={handleCreateJob}
                className="px-4 py-2 bg-green-600 text-white rounded-xl hover:bg-green-700 font-medium flex items-center gap-2"
              >
                <Play className="w-4 h-4" /> Bắt đầu
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Activity({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  );
}
