"use client";

import React, { useState, useEffect } from "react";
import { Plus, Database, Play, CheckCircle, Clock, X, FileText, Upload, BrainCircuit, Activity } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { listDatasetsAPI, listJobsAPI, createDatasetAPI, createJobAPI, startTrainingAPI, importFromFeedbackAPI } from "@/features/ai/services/model_finetuning.service";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from "@/shared/components/ui/Modal";

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
  const [jobConfig, setJobConfig] = useState({ base_model: "", epochs: 3, learning_rate: 0.0002, batch_size: 4, method: "lora", lora_rank: 16 });

  const loadData = async () => {
    try {
      setLoading(true);
      const [dsRes, jobsRes] = await Promise.all([listDatasetsAPI(), listJobsAPI()]);
      setDatasets(dsRes.data || []); setJobs(jobsRes.data || []);
    } catch (err: any) { showToast(err.message || "Lỗi tải dữ liệu", "error"); } finally { setLoading(false); }
  };

  useEffect(() => { if (user) loadData(); }, [user]);

  useEffect(() => {
    const hasRunning = jobs.some(j => j.status === "running");
    if (!hasRunning) return;
    const interval = setInterval(async () => { try { const res = await listJobsAPI(); setJobs(res.data || []); } catch {} }, 3000);
    return () => clearInterval(interval);
  }, [jobs]);

  const handleCreateDataset = async () => {
    if (!newDatasetName.trim()) return showToast("Vui lòng nhập tên tập dữ liệu", "error");
    try { await createDatasetAPI(newDatasetName, newDatasetDesc); showToast("Tạo thành công", "success"); setShowNewDataset(false); setNewDatasetName(""); setNewDatasetDesc(""); loadData(); } catch (err: any) { showToast(err.message || "Lỗi tạo", "error"); }
  };

  const handleCreateJob = async () => {
    if (!selectedDatasetId) return showToast("Vui lòng chọn tập dữ liệu", "error");
    try {
      const res = await createJobAPI({ dataset_id: selectedDatasetId, ...jobConfig });
      showToast("Tạo công việc thành công", "success"); setShowNewJob(false);
      const jobId = res.data?._id; if (jobId) { await startTrainingAPI(jobId); showToast("Đã bắt đầu huấn luyện", "success"); }
      loadData();
    } catch (err: any) { showToast(err.message || "Lỗi tạo công việc", "error"); }
  };

  const handleImportFeedback = async () => {
    try { showToast("Đang thu thập phản hồi", "success"); const res = await importFromFeedbackAPI(); showToast(`Đã tạo tập dữ liệu với ${res.data?.imported || 0} mẫu`, "success"); loadData(); } catch (err: any) { showToast(err.message || "Lỗi nhập", "error"); }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "text-[#34C759] bg-[#34C759]/10";
      case "running": return "text-[#0071E3] bg-[#0071E3]/10";
      case "failed": return "text-[#FF3B30] bg-[#FF3B30]/10";
      case "deployed": return "text-[#AF52DE] bg-[#AF52DE]/10";
      default: return "text-[#6E6E73] bg-[#F5F5F7]";
    }
  };
  const getStatusText = (status: string) => {
    switch (status) {
      case "completed": return "Hoàn thành";
      case "running": return "Đang huấn luyện";
      case "failed": return "Thất bại";
      case "deployed": return "Đã triển khai";
      case "pending": return "Chờ xử lý";
      default: return status;
    }
  };

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] font-sans text-[#1D1D1F] flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-end gap-4">
        <div className="flex items-center gap-3">
          <button onClick={handleImportFeedback} className="pill-button bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] flex items-center gap-2"><Upload className="w-4 h-4" /> Nhập phản hồi</button>
          <button onClick={() => setShowNewJob(true)} className="pill-button bg-[#0071E3] text-white hover:bg-[#0077ED] flex items-center gap-2"><Play className="w-4 h-4" /> Huấn luyện mới</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        <div className="bg-[#F5F5F7] rounded-[24px] border-[#E8E8ED] flex flex-col overflow-hidden min-h-0">
          <div className="p-5 border-b border-[#E8E8ED] flex justify-between items-center bg-[#F5F5F7]/30">
            <h2 className="text-[16px] font-medium text-[#1D1D1F] flex items-center gap-2"><Database className="w-5 h-5 text-[#6E6E73]" /> Tập dữ liệu <span className="px-2 py-0.5 bg-[#F5F5F7] text-[#6E6E73] rounded-full text-[12px]">{datasets.length}</span></h2>
            <button onClick={() => setShowNewDataset(true)} className="w-8 h-8 flex items-center justify-center bg-[#F5F5F7] text-[#1D1D1F] rounded-full hover:bg-[#E8E8ED] transition-colors"><Plus className="w-4 h-4" /></button>
          </div>
          <div className="p-4 flex-1 overflow-y-auto no-scrollbar">
            {loading ? <div className="py-10 flex justify-center"><div className="w-6 h-6 border-2 border-[#0071E3] border-t-transparent rounded-full animate-spin"></div></div> : datasets.length === 0 ? <div className="text-center py-10 text-[#6E6E73] text-[14px]">Chưa có tập dữ liệu nào.</div> : (
              <div className="space-y-3">
                {datasets.map(ds => (
                  <div key={ds._id} className="p-4 bg-[#F5F5F7] border-transparent rounded-[18px] hover:border-[#E8E8ED] hover:bg-[#F5F5F7] transition-colors">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-[15px] font-medium text-[#1D1D1F]">{ds.name}</h3>
                      <span className="text-[12px] px-2.5 py-1 bg-[#E8E8ED] text-[#6E6E73] rounded-full font-medium">{ds.sample_count} mẫu</span>
                    </div>
                    {ds.description && <p className="text-[13px] text-[#6E6E73] line-clamp-1">{ds.description}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="bg-[#F5F5F7] rounded-[24px] border-[#E8E8ED] flex flex-col overflow-hidden min-h-0">
          <div className="p-5 border-b border-[#E8E8ED] bg-[#F5F5F7]/30">
            <h2 className="text-[16px] font-medium text-[#1D1D1F] flex items-center gap-2"><Activity className="w-5 h-5 text-[#6E6E73]" /> Tiến trình Huấn luyện <span className="px-2 py-0.5 bg-[#F5F5F7] text-[#6E6E73] rounded-full text-[12px]">{jobs.length}</span></h2>
          </div>
          <div className="p-4 flex-1 overflow-y-auto no-scrollbar">
            {loading ? <div className="py-10 flex justify-center"><div className="w-6 h-6 border-2 border-[#34C759] border-t-transparent rounded-full animate-spin"></div></div> : jobs.length === 0 ? <div className="text-center py-10 text-[#6E6E73] text-[14px]">Chưa có tiến trình huấn luyện nào.</div> : (
              <div className="space-y-4">
                {jobs.map(job => (
                  <div key={job._id} className="p-5 bg-[#F5F5F7] border-transparent rounded-[18px] hover:border-[#E8E8ED] hover:bg-[#F5F5F7] transition-colors">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-[15px] font-medium text-[#1D1D1F]">{job.job_name}</h3>
                        <p className="text-[12px] text-[#6E6E73] mt-0.5">Mô hình gốc: {job.base_model}</p>
                      </div>
                      <span className={`text-[12px] px-2.5 py-1 rounded-full font-medium ${getStatusColor(job.status)}`}>{getStatusText(job.status)}</span>
                    </div>
                    <div className="space-y-2 mb-3">
                      <div className="flex justify-between text-[12px] text-[#6E6E73] font-medium"><span>Tiến độ</span><span>{job.progress}%</span></div>
                      <div className="w-full bg-[#E8E8ED] rounded-full h-2"><div className={`h-2 rounded-full transition-all duration-500 ${job.status === "failed" ? "bg-[#FF3B30]" : "bg-[#34C759]"}`} style={{ width: `${job.progress}%` }}></div></div>
                    </div>
                    {job.current_loss !== undefined && job.current_loss !== null && (
                      <div className="flex flex-wrap gap-2 text-[12px] text-[#6E6E73]">
                        <span className="bg-[#E8E8ED] px-2 py-0.5 rounded-md">Epoch: {job.current_epoch}/{job.epochs}</span>
                        <span className="bg-[#E8E8ED] px-2 py-0.5 rounded-md">Loss: {typeof job.current_loss === "number" ? job.current_loss.toFixed(4) : job.current_loss}</span>
                        {job.best_loss !== undefined && job.best_loss !== null && <span className="bg-[#E8E8ED] px-2 py-0.5 rounded-md">Best: {typeof job.best_loss === "number" ? job.best_loss.toFixed(4) : job.best_loss}</span>}
                        {job.method && <span className="bg-[#0071E3]/10 text-[#0071E3] px-2 py-0.5 rounded-md font-medium">{job.method.toUpperCase()}{job.lora_rank ? ` r${job.lora_rank}` : ""}</span>}
                      </div>
                    )}
                    {job.merged_model_name && <div className="mt-3 text-[12px] text-[#34C759] font-mono bg-[#34C759]/10 px-2 py-1 rounded-md w-fit">{job.merged_model_name}</div>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <Modal isOpen={showNewDataset} onClose={() => setShowNewDataset(false)} className="max-w-md bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6 pb-2"><ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">Tạo Tập Dữ Liệu</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-2 space-y-4">
          <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Tên tập dữ liệu</label><input type="text" value={newDatasetName} onChange={e => setNewDatasetName(e.target.value)} className="apple-input w-full bg-white" placeholder="VD: Dữ liệu luật lao động" /></div>
          <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Mô tả (Tùy chọn)</label><textarea value={newDatasetDesc} onChange={e => setNewDatasetDesc(e.target.value)} className="apple-input w-full bg-white h-24 py-3" placeholder="Mô tả ngắn gọn về tập dữ liệu" /></div>
        </ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => setShowNewDataset(false)} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Hủy</button><button onClick={handleCreateDataset} className="pill-button">Tạo mới</button></ModalFooter>
      </Modal>

      <Modal isOpen={showNewJob} onClose={() => setShowNewJob(false)} className="max-w-md bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6 pb-2"><ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">Bắt đầu Huấn luyện</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-2 space-y-4">
          <div>
            <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Chọn tập dữ liệu</label>
            <select value={selectedDatasetId} onChange={e => setSelectedDatasetId(e.target.value)} className="apple-input w-full bg-white">
              <option value="">-- Chọn tập dữ liệu --</option>{datasets.map(ds => <option key={ds._id} value={ds._id}>{ds.name} ({ds.sample_count} mẫu)</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Số Epochs</label><input type="number" value={jobConfig.epochs} onChange={e => setJobConfig({...jobConfig, epochs: parseInt(e.target.value)})} className="apple-input w-full bg-white" min="1" max="10" /></div>
            <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Batch Size</label><input type="number" value={jobConfig.batch_size} onChange={e => setJobConfig({...jobConfig, batch_size: parseInt(e.target.value)})} className="apple-input w-full bg-white" min="1" max="16" /></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Phương pháp</label><select value={jobConfig.method} onChange={e => setJobConfig({...jobConfig, method: e.target.value})} className="apple-input w-full bg-white"><option value="lora">LoRA</option><option value="qlora">QLoRA</option></select></div>
            <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">LoRA Rank (r)</label><input type="number" value={jobConfig.lora_rank} onChange={e => setJobConfig({...jobConfig, lora_rank: parseInt(e.target.value)})} className="apple-input w-full bg-white" min="4" max="128" step="4" /></div>
          </div>
        </ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => setShowNewJob(false)} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Hủy</button><button onClick={handleCreateJob} className="pill-button bg-[#34C759] text-white hover:bg-[#32B357] flex items-center gap-2"><Play className="w-4 h-4" /> Bắt đầu</button></ModalFooter>
      </Modal>
    </div>
  );
}
