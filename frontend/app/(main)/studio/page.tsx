"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  compileDocumentAPI,
  getDocumentDraftAPI,
  getDocumentsAPI,
  publishDocumentAPI,
  saveDocumentDraftAPI,
  getToken,
} from "@/app/lib/api";
import { 
  FileText, 
  Settings, 
  BarChart3, 
  Wallet, 
  Save, 
  Eye, 
  Code, 
  ChevronLeft, 
  BookOpen,
  ArrowUpRight,
  TrendingUp,
  DollarSign,
  Clock,
  Plus,
  Users,
  Trash2,
  RefreshCcw
} from "lucide-react";
import { Button } from "@/components/ui/button";
import TiptapEditor from "@/app/components/editor/TiptapEditor";

type StudioDocument = {
  _id: string;
  title: string;
  slug: string;
  status?: string;
  content?: string;
  price?: number;
  visibility?: string;
  chapters?: any[];
};

type ViewMode = "edit" | "stats" | "config" | "versions" | "trash";
type EditorMode = "edit" | "preview" | "raw";

export default function AuthorStudioPage() {
  const [documents, setDocuments] = useState<StudioDocument[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("edit");
  const [editorMode, setEditorMode] = useState<EditorMode>("edit");
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  
  const [stats, setStats] = useState<any>(null);
  const [revenue, setRevenue] = useState<any>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [trashDocuments, setTrashDocuments] = useState<any[]>([]);
  const [isRestoring, setIsRestoring] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  const selectedDocument = useMemo(
    () => documents.find((d) => d._id === selectedDocumentId) || null,
    [documents, selectedDocumentId]
  );

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    if (selectedDocumentId) {
      loadDraft();
      if (viewMode === "stats") fetchStats();
      if (viewMode === "versions") fetchVersions();
    } else {
      setContent("");
    }
    if (viewMode === "trash") fetchTrash();
  }, [selectedDocumentId, viewMode]);

  const fetchDocuments = async () => {
    setIsLoading(true);
    setStatusMsg("");
    try {
      const data = await getDocumentsAPI();
      setDocuments(data || []);
      if (data?.length > 0 && !selectedDocumentId) {
        setSelectedDocumentId(data[0]._id);
      }
    } catch {
      setStatusMsg("Không thể tải danh sách tài liệu.");
    } finally {
      setIsLoading(false);
    }
  };

  const loadDraft = async () => {
    if (!selectedDocumentId) return;
    try {
      const draft = await getDocumentDraftAPI(selectedDocumentId);
      setContent(draft?.content || "");
      setStatusMsg("Đã tải bản nháp.");
    } catch {
      setStatusMsg("Không thể tải bản nháp.");
    }
  };

  const fetchStats = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${getToken()}` };
      const [sRes, rRes] = await Promise.all([
        fetch(`${API_URL}/analytics/author/stats`, { headers }),
        fetch(`${API_URL}/wallet/revenue`, { headers })
      ]);
      if (sRes.ok) setStats(await sRes.json());
      if (rRes.ok) setRevenue(await rRes.json());
    } catch (e) { console.error(e); }
  };

  const fetchVersions = async () => {
    try {
      const res = await fetch(`${API_URL}/author/documents/${selectedDocumentId}/versions`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      if (res.ok) setVersions(await res.json());
    } catch (e) { console.error(e); }
  };

  const fetchTrash = async () => {
    try {
      const res = await fetch(`${API_URL}/api/trash`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      if (res.ok) setTrashDocuments(await res.json());
    } catch (e) { console.error(e); }
  };

  const handleRestoreTrash = async (id: string) => {
    try {
      const res = await fetch(`${API_URL}/api/documents/${id}/restore`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      if (res.ok) {
        setStatusMsg("Đã khôi phục.");
        fetchTrash();
        fetchDocuments();
      }
    } catch (e) { console.error(e); }
  };

  const handleDeleteDocument = async () => {
    if (!selectedDocumentId) return;
    if (!confirm("Bạn có chắc chắn muốn chuyển tài liệu này vào thùng rác?")) return;
    try {
      const res = await fetch(`${API_URL}/api/documents/${selectedDocumentId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      if (res.ok) {
        setStatusMsg("Đã chuyển vào thùng rác.");
        setSelectedDocumentId("");
        fetchDocuments();
      }
    } catch (e) { console.error(e); }
  };

  const saveVersion = async (note: string) => {
    try {
      const res = await fetch(`${API_URL}/author/documents/${selectedDocumentId}/versions`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ note })
      });
      if (res.ok) {
        setStatusMsg("Đã lưu phiên bản.");
        fetchVersions();
      }
    } catch (e) { console.error(e); }
  };

  const restoreVersion = async (versionId: string) => {
    if (!confirm("Bạn có chắc chắn muốn khôi phục phiên bản này? Nội dung hiện tại sẽ bị thay thế.")) return;
    setIsRestoring(true);
    try {
      const res = await fetch(`${API_URL}/author/versions/${versionId}/restore`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      if (res.ok) {
        setStatusMsg("Đã khôi phục.");
        loadDraft();
      }
    } catch (e) { console.error(e); } finally { setIsRestoring(false); }
  };

  const handleSave = async () => {
    if (!selectedDocumentId) return;
    setIsSaving(true);
    setStatusMsg("Đang lưu");
    try {
      await saveDocumentDraftAPI(selectedDocumentId, content, "html");
      setStatusMsg("Đã lưu.");
    } catch {
      setStatusMsg("Lưu thất bại.");
    } finally {
      setIsSaving(false);
    }
  };

  const handlePublish = async () => {
    if (!selectedDocumentId) return;
    setStatusMsg("Đang xuất bản");
    try {
      await compileDocumentAPI(selectedDocumentId);
      await publishDocumentAPI(selectedDocumentId);
      setStatusMsg("Đã xuất bản.");
      fetchDocuments();
    } catch {
      setStatusMsg("Xuất bản thất bại.");
    }
  };

  const updateDocumentConfig = async (updates: any) => {
    try {
      const res = await fetch(`${API_URL}/documents/${selectedDocumentId}`, {
        method: "PUT",
        headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (res.ok) {
        setStatusMsg("Đã cập nhật cấu hình.");
        fetchDocuments();
      }
    } catch (e) { console.error(e); }
  };

  const requestPayout = async () => {
    if (!revenue?.available_balance || revenue.available_balance < 1000) {
      alert("Số dư tối thiểu để rút là 1000 Coin");
      return;
    }
    try {
      const res = await fetch(`${API_URL}/wallet/payout?amount=${revenue.available_balance}`, {
        method: "POST",
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (res.ok) {
        alert("Yêu cầu rút tiền đã được gửi.");
        fetchStats();
      }
    } catch (e) { console.error(e); }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col font-sans text-foreground">
      <header className="h-14 border-b border-border bg-white flex items-center justify-between px-6 sticky top-0 z-10">
        <div className="flex items-center gap-6">
          <Link href="/" className="text-lg font-bold tracking-tighter">DOCLIB<span className="text-muted-foreground ml-1 font-normal text-[10px] tracking-widest">Tác giả</span></Link>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-2 text-sm font-medium">
            <span className="text-muted-foreground">Tài liệu</span>
            <span className="truncate max-w-[200px] font-bold">{selectedDocument?.title || "Chưa chọn tài liệu"}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-muted-foreground mr-2 font-bold tracking-widest uppercase">{statusMsg}</span>
          <Button variant="outline" size="sm" onClick={handleSave} disabled={!selectedDocumentId || isSaving} className="h-8 text-xs font-bold border-border">
            <Save className="w-3.5 h-3.5 mr-2" /> LƯU BẢN NHÁP
          </Button>
          <Button variant="default" size="sm" onClick={handlePublish} disabled={!selectedDocumentId} className="h-8 text-xs font-bold">
            XUẤT BẢN
          </Button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-16 border-r border-border bg-white flex flex-col items-center py-4 gap-4 flex-shrink-0">
          <button onClick={() => setViewMode("edit")} className={`p-2  transition-colors ${viewMode === "edit" ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted"}`} title="Soạn thảo"><FileText className="w-5 h-5" /></button>
          <button onClick={() => setViewMode("stats")} className={`p-2  transition-colors ${viewMode === "stats" ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted"}`} title="Thống kê"><BarChart3 className="w-5 h-5" /></button>
          <button onClick={() => setViewMode("config")} className={`p-2  transition-colors ${viewMode === "config" ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted"}`} title="Cấu hình"><Settings className="w-5 h-5" /></button>
          <button onClick={() => setViewMode("versions")} className={`p-2  transition-colors ${viewMode === "versions" ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted"}`} title="Phiên bản"><Clock className="w-5 h-5" /></button>
          <button onClick={() => setViewMode("trash")} className={`p-2  transition-colors ${viewMode === "trash" ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted"}`} title="Thùng rác"><Trash2 className="w-5 h-5" /></button>
        </aside>

        <aside className="w-64 border-r border-border bg-white flex flex-col flex-shrink-0">
          <div className="p-4 border-b border-border">
             <h3 className="text-[10px] font-bold text-muted-foreground tracking-widest mb-4 uppercase">Danh sách chương</h3>
             <div className="space-y-1">
                {(selectedDocument?.chapters || []).map((ch: any, idx: number) => (
                  <div key={ch.id} className="group flex items-center gap-2 p-2  border border-transparent hover:border-border hover:bg-muted/30 cursor-pointer">
                    <span className="text-[10px] font-bold text-muted-foreground w-4">{idx + 1}</span>
                    <span className="text-xs font-bold truncate flex-1">{ch.title}</span>
                  </div>
                ))}
                <button className="w-full mt-4 p-2 border border-dashed border-border text-[10px] font-bold tracking-widest text-muted-foreground hover:text-foreground hover:border-foreground transition-all flex items-center justify-center gap-2">
                  <Plus className="w-3.5 h-3.5" /> THÊM CHƯƠNG MỚI
                </button>
             </div>
          </div>

          <div className="mt-4 flex-1 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-[10px] font-bold text-muted-foreground tracking-widest mb-4 uppercase">Tài liệu của bạn</h3>
              <div className="space-y-1">
                {isLoading ? (
                  <div className="py-4 text-center text-xs text-muted-foreground uppercase tracking-widest font-bold">Đang tải dữ liệu</div>
                ) : documents.map((doc) => (
                  <button
                    key={doc._id}
                    onClick={() => setSelectedDocumentId(doc._id)}
                    className={`w-full text-left p-3  border transition-all ${selectedDocumentId === doc._id ? "bg-muted border-border" : "bg-transparent border-transparent hover:bg-muted/30"}`}
                  >
                    <p className="font-bold text-xs truncate">{doc.title}</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5 truncate tracking-tighter uppercase font-bold">{doc.status === "published" ? "Đã xuất bản" : doc.status === "draft" ? "Bản thảo" : doc.status}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>

        <main className="flex-1 flex flex-col bg-muted/10 overflow-hidden">
          {viewMode === "edit" && (
            <div className="flex-1 flex flex-col overflow-hidden animate-in fade-in duration-300">
              <div className="h-10 border-b border-border bg-white px-4 flex items-center justify-between">
                <div className="flex gap-1">
                  {(["edit", "preview", "raw"] as const).map((m) => (
                    <button
                      key={m}
                      onClick={() => setEditorMode(m)}
                      className={`px-3 h-full text-[10px] font-bold tracking-widest transition-all border-b-2 ${editorMode === m ? "border-foreground text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
                    >
                      {m === 'edit' ? 'Soạn thảo' : m === 'preview' ? 'Xem trước' : 'Mã nguồn'}
                    </button>
                  ))}
                </div>
                <div className="text-[10px] text-muted-foreground font-bold tracking-widest">Trình soạn thảo</div>
              </div>

              <div className="flex-1 p-6 overflow-y-auto">
                {editorMode === "edit" ? (
                  <TiptapEditor 
                    initialContent={content} 
                    onSave={(val) => setContent(val)} 
                  />
                ) : editorMode === "preview" ? (
                  <div className="max-w-3xl mx-auto bg-white border border-border p-12 min-h-[80vh] prose prose-neutral" dangerouslySetInnerHTML={{ __html: content }} />
                ) : (
                  <pre className="p-8 bg-black text-white  text-xs overflow-auto font-sans leading-loose">
                    {content || "Chưa có nội dung soạn thảo"}
                  </pre>
                )}
              </div>
            </div>
          )}

          {viewMode === "stats" && (
            <div className="flex-1 p-8 overflow-y-auto animate-in fade-in duration-300">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white p-6 border border-border  shadow-sm">
                  <div className="flex items-center justify-between text-muted-foreground mb-4">
                    <Eye className="w-4 h-4" />
                    <span className="text-[10px] font-bold tracking-widest">Lượt xem</span>
                  </div>
                  <h3 className="text-3xl font-bold">{stats?.total_views || 0}</h3>
                  <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                    <TrendingUp className="w-3 h-3" /> <span>Thay đổi so với tháng trước</span>
                  </div>
                </div>
                <div className="bg-white p-6 border border-border  shadow-sm">
                  <div className="flex items-center justify-between text-muted-foreground mb-4">
                    <Users className="w-4 h-4" />
                    <span className="text-[10px] font-bold tracking-widest">Người theo dõi</span>
                  </div>
                  <h3 className="text-3xl font-bold">{stats?.followers_count || 0}</h3>
                </div>
                <div className="bg-white p-6 border border-border  shadow-sm">
                  <div className="flex items-center justify-between text-muted-foreground mb-4">
                    <Wallet className="w-4 h-4" />
                    <span className="text-[10px] font-bold tracking-widest uppercase">Số dư thu nhập</span>
                  </div>
                  <h3 className="text-3xl font-bold">{revenue?.available_balance || 0} Coin</h3>
                  <Button variant="secondary" size="sm" onClick={requestPayout} className="w-full mt-4 font-bold text-[10px] tracking-widest border-border">RÚT TIỀN</Button>
                </div>
              </div>

              <div className="bg-white border border-border  overflow-hidden">
                <div className="px-6 py-4 border-b border-border bg-muted/20">
                  <h3 className="text-xs font-bold tracking-widest">Hiệu suất từng tài liệu</h3>
                </div>
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-border text-[10px] tracking-widest text-muted-foreground">
                      <th className="px-6 py-4 font-bold">Tài liệu</th>
                      <th className="px-6 py-4 font-bold">Lượt xem</th>
                      <th className="px-6 py-4 font-bold">Đánh giá</th>
                      <th className="px-6 py-4 font-bold text-right">Hành động</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats?.documents?.map((d: any) => (
                      <tr key={d.id} className="border-b border-border last:border-0 hover:bg-muted/10 transition-colors">
                        <td className="px-6 py-4 font-bold">{d.title}</td>
                        <td className="px-6 py-4">{d.views}</td>
                        <td className="px-6 py-4 font-medium">{d.rating.toFixed(1)} / 5.0</td>
                        <td className="px-6 py-4 text-right">
                          <button onClick={() => {setSelectedDocumentId(d.id); setViewMode("edit");}} className="text-[10px] font-bold text-muted-foreground hover:text-foreground">Chi tiết</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

            <div className="flex-1 p-8 overflow-y-auto animate-in fade-in duration-300">
              <div className="max-w-2xl bg-white border border-border p-8  space-y-8">
                <div>
                  <h2 className="text-lg font-bold tracking-tight mb-2">Thiết lập tài liệu</h2>
                  <p className="text-xs text-muted-foreground tracking-wider uppercase font-bold">Cấu hình hiển thị và thương mại hóa cho {selectedDocument?.title}</p>
                </div>

                <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-muted-foreground tracking-widest uppercase">Đơn giá bán</label>
                    <div className="relative">
                      <input 
                        type="number" 
                        value={selectedDocument?.price || 0}
                        onChange={(e) => updateDocumentConfig({ price: parseFloat(e.target.value) })}
                        className="w-full bg-muted/20 border border-border  px-4 py-3 text-sm font-bold outline-none focus:border-foreground"
                      />
                      <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-bold text-muted-foreground uppercase">Coin</span>
                    </div>
                    <p className="text-[9px] text-muted-foreground italic font-medium">Nhập số 0 nếu bạn muốn chia sẻ tài liệu này miễn phí</p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-muted-foreground tracking-widest uppercase">Loại giấy phép bản quyền</label>
                    <select 
                      value={selectedDocument?.license || "copyright"}
                      onChange={(e) => updateDocumentConfig({ license: e.target.value })}
                      className="w-full bg-muted/20 border border-border  px-4 py-3 text-sm font-bold outline-none focus:border-foreground appearance-none"
                    >
                      <option value="copyright">Bản quyền toàn vẹn</option>
                      <option value="cc-by">CC BY - Ghi công</option>
                      <option value="cc-by-sa">CC BY-SA - Chia sẻ tương tự</option>
                      <option value="cc-by-nc">CC BY-NC - Phi thương mại</option>
                      <option value="public-domain">Public Domain - Miền công cộng</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-muted-foreground tracking-widest uppercase">Chế độ hiển thị</label>
                    <select 
                      value={selectedDocument?.visibility || "public"}
                      onChange={(e) => updateDocumentConfig({ visibility: e.target.value })}
                      className="w-full bg-muted/20 border border-border  px-4 py-3 text-sm font-bold outline-none focus:border-foreground appearance-none"
                    >
                      <option value="public">Công khai</option>
                      <option value="private">Riêng tư</option>
                      <option value="unlisted">Không liệt kê</option>
                    </select>
                  </div>

                  <div className="pt-4 border-t border-border flex items-center justify-between">
                    <div>
                      <p className="text-xs font-bold tracking-widest uppercase">Quản lý tài liệu</p>
                      <p className="text-[10px] text-muted-foreground mt-1 font-medium">Chuyển tài liệu vào thùng rác nếu bạn không muốn tiếp tục soạn thảo</p>
                    </div>
                    <Button variant="outline" size="sm" onClick={handleDeleteDocument} className="h-8 text-[10px] font-bold text-black border-zinc-200 hover:bg-zinc-50">CHUYỂN VÀO THÙNG RÁC</Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {viewMode === "versions" && (
            <div className="flex-1 p-8 overflow-y-auto animate-in fade-in duration-300">
              <div className="max-w-2xl bg-white border border-border">
                <div className="p-6 border-b border-border flex justify-between items-center">
                  <div>
                    <h2 className="text-lg font-bold tracking-tight">Lịch sử phiên bản</h2>
                    <p className="text-[10px] text-muted-foreground font-bold tracking-widest mt-1">Các bản sao lưu được lưu trữ thủ công hoặc tự động</p>
                  </div>
                  <Button 
                    variant="default" 
                    size="sm" 
                    className="text-[10px] font-bold tracking-widest"
                    onClick={() => {
                      const note = prompt("Nhập ghi chú cho phiên bản này:");
                      if (note) saveVersion(note);
                    }}
                  >LƯU PHIÊN BẢN MỚI</Button>
                </div>
                <div className="divide-y divide-border">
                  {versions.length === 0 ? (
                    <div className="p-12 text-center text-muted-foreground text-xs tracking-widest font-bold">Chưa có phiên bản nào được lưu.</div>
                  ) : versions.map((v) => (
                    <div key={v._id} className="p-6 flex items-center justify-between hover:bg-muted/20 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-zinc-100 flex items-center justify-center">
                          <Clock className="w-5 h-5 text-zinc-400" />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-foreground">{v.note || "Tự động lưu"}</p>
                          <p className="text-[10px] text-muted-foreground font-bold tracking-widest mt-0.5">
                            {new Date(v.created_at).toLocaleString('vi-VN')}
                          </p>
                        </div>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="text-[10px] font-bold tracking-widest border-border"
                        onClick={() => restoreVersion(v._id)}
                        disabled={isRestoring}
                      >KHÔI PHỤC</Button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {viewMode === "trash" && (
            <div className="flex-1 p-8 overflow-y-auto animate-in fade-in duration-300">
              <div className="max-w-4xl mx-auto">
                <div className="mb-8">
                  <h2 className="text-2xl font-bold tracking-tight">Thùng rác</h2>
                  <p className="text-xs text-muted-foreground tracking-widest mt-1">Tài liệu đã xóa có thể được khôi phục trong vòng 30 ngày.</p>
                </div>

                <div className="grid grid-cols-1 gap-4">
                  {trashDocuments.length === 0 ? (
                    <div className="p-20 border border-dashed border-border flex flex-col items-center justify-center text-muted-foreground">
                      <Trash2 className="w-12 h-12 mb-4 opacity-20" />
                      <p className="text-sm font-bold tracking-widest uppercase">Thùng rác đang trống</p>
                    </div>
                  ) : trashDocuments.map((doc) => (
                    <div key={doc._id} className="bg-white border border-border p-6 flex items-center justify-between hover:border-foreground transition-all">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-16 bg-muted border border-border flex items-center justify-center">
                           <FileText className="w-6 h-6 text-muted-foreground" />
                        </div>
                        <div>
                          <h3 className="font-bold text-sm">{doc.title}</h3>
                          <p className="text-[10px] text-muted-foreground font-bold tracking-widest mt-1 uppercase">Đã xóa vào ngày {new Date(doc.deleted_at).toLocaleString('vi-VN')}</p>
                        </div>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => handleRestoreTrash(doc._id)}
                        className="text-[10px] font-bold tracking-widest border-border"
                      >
                        <RefreshCcw className="w-3.5 h-3.5 mr-2" /> KHÔI PHỤC NGAY
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
