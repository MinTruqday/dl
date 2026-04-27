"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken } from "@/app/lib/api";
import { User, BookOpen, Clock, BarChart3, Shield, Save, Eye, EyeOff } from "lucide-react";

export default function ProfilePage() {
  const [profile, setProfile] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [privacy, setPrivacy] = useState({ hide_reading_activity: false, hide_library: false });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({ full_name: "", bio: "", donation_link: "" });
  const [message, setMessage] = useState("");
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  const showMessage = useCallback((msg: string) => {
    setMessage(msg);
    setTimeout(() => setMessage(""), 3000);
  }, []);

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    try {
      const [profileRes, statsRes, privacyRes] = await Promise.all([
        fetch(`${API_URL}/profile/me`, { headers: { Authorization: `Bearer ${getToken()}` } }),
        fetch(`${API_URL}/reader/stats`, { headers: { Authorization: `Bearer ${getToken()}` } }),
        fetch(`${API_URL}/reader/settings/privacy`, { headers: { Authorization: `Bearer ${getToken()}` } }),
      ]);
      if (profileRes.ok) {
        const p = await profileRes.json();
        setProfile(p);
        setEditData({ full_name: p.full_name || "", bio: p.bio || "", donation_link: p.donation_link || "" });
      }
      if (statsRes.ok) setStats(await statsRes.json());
      if (privacyRes.ok) setPrivacy(await privacyRes.json());
    } catch (e) {
      console.error("Profile load error:", e);
    } finally {
      setLoading(false);
    }
  };

  const saveProfile = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/profile/me`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify(editData),
      });
      if (res.ok) {
        showMessage("Đã cập nhật hồ sơ");
        setEditMode(false);
        fetchAll();
      }
    } catch (e) {
      showMessage("Không thể lưu hồ sơ");
    } finally {
      setSaving(false);
    }
  };

  const savePrivacy = async () => {
    try {
      const res = await fetch(`${API_URL}/reader/settings/privacy`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify(privacy),
      });
      if (res.ok) showMessage("Đã cập nhật cài đặt riêng tư");
    } catch (e) {
      showMessage("Không thể lưu cài đặt");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center animate-in fade-in duration-300">
        <div className="w-10 h-10 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[900px] mx-auto px-6 lg:px-8 py-12 md:py-16 bg-white min-h-screen animate-in fade-in duration-300">
      {message && (
        <div className="fixed top-6 right-6 z-50 px-5 py-3 bg-black text-white text-[12px] font-bold tracking-widest animate-in slide-in-from-right-4 duration-300">
          {message}
        </div>
      )}

      <header className="border-b border-black pb-8 mb-10">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <User className="w-5 h-5 text-zinc-400" />
            <span className="text-[12px] font-bold tracking-widest text-zinc-400">Hồ sơ cá nhân</span>
          </div>
          <div className="flex flex-col items-end gap-1">
             <span className="text-[13px] font-bold tracking-tighter">Mức độ hoàn thiện: {
                (() => {
                  let score = 0;
                  if (profile?.full_name) score += 20;
                  if (profile?.bio) score += 20;
                  if (profile?.avatar_url) score += 20;
                  if (profile?.donation_link) score += 20;
                  if (profile?.role !== 'READER') score += 20;
                  return score;
                })()
             }%</span>
             <div className="w-32 h-1 bg-zinc-100 rounded-none overflow-hidden">
                <div 
                  className="bg-black h-full transition-all duration-1000" 
                  style={{ width: `${
                    (() => {
                      let score = 0;
                      if (profile?.full_name) score += 20;
                      if (profile?.bio) score += 20;
                      if (profile?.avatar_url) score += 20;
                      if (profile?.donation_link) score += 20;
                      if (profile?.role !== 'READER') score += 20;
                      return score;
                    })()
                  }%` }} 
                />
             </div>
          </div>
        </div>
        <h1 className="text-4xl font-bold text-black tracking-tighter">{profile?.full_name || "Chưa đặt tên"}</h1>
        <p className="text-sm text-zinc-500 mt-2">{profile?.email}</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <div className="border border-border p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2">
              <User className="w-4 h-4" /> Thông tin cá nhân
            </h2>
            <button
              onClick={() => editMode ? saveProfile() : setEditMode(true)}
              disabled={saving}
              className="text-[12px] font-bold tracking-widest px-4 py-2 border border-border hover:border-black transition-all flex items-center gap-2"
            >
              <Save className="w-3.5 h-3.5" />
              {editMode ? "Lưu" : "Chỉnh sửa"}
            </button>
          </div>
          {editMode ? (
            <div className="space-y-4">
              <div>
                <label className="block text-[12px] font-bold tracking-widest text-zinc-400 mb-1">Tên hiển thị</label>
                <input
                  type="text"
                  value={editData.full_name}
                  onChange={(e) => setEditData({ ...editData, full_name: e.target.value })}
                  className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all"
                />
              </div>
              <div>
                <label className="block text-[12px] font-bold tracking-widest text-zinc-400 mb-1">Giới thiệu</label>
                <textarea
                  value={editData.bio}
                  onChange={(e) => setEditData({ ...editData, bio: e.target.value })}
                  className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all h-24 resize-none"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-3 text-sm">
              <div className="flex justify-between py-2 border-b border-zinc-50">
                <span className="text-zinc-400 font-medium">Vai trò</span>
                <span className="font-bold text-black text-[12px] tracking-widest">{profile?.role || "reader"}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-zinc-50">
                <span className="text-zinc-400 font-medium">Giới thiệu</span>
                <span className="text-black font-medium max-w-[200px] text-right truncate">{profile?.bio || "Chưa cập nhật"}</span>
              </div>
            </div>
          )}
        </div>

        <div className="border border-border p-6">
          <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2 mb-6">
            <BarChart3 className="w-4 h-4" /> Thống kê nghiên cứu
          </h2>
          {stats ? (
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-zinc-50 border border-border">
                <span className="text-2xl font-bold text-black">{stats.total_books_read}</span>
                <p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Tài liệu đã đọc</p>
              </div>
              <div className="p-4 bg-zinc-50 border border-border">
                <span className="text-2xl font-bold text-black">{stats.completed_books}</span>
                <p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Hoàn thành</p>
              </div>
              <div className="p-4 bg-zinc-50 border border-border">
                <span className="text-2xl font-bold text-black">{stats.days_active}</span>
                <p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Ngày hoạt động</p>
              </div>
              <div className="p-4 bg-zinc-50 border border-border">
                <span className="text-2xl font-bold text-black">{stats.average_progress}%</span>
                <p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Tiến độ TB</p>
              </div>
            </div>
          ) : (
            <p className="text-xs text-zinc-400 font-bold tracking-widest">Chưa có dữ liệu</p>
          )}
        </div>
      </div>

      <div className="border border-border p-6">
        <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2 mb-6">
          <Shield className="w-4 h-4" /> Cài đặt riêng tư
        </h2>
        <div className="space-y-4">
          <label className="flex items-center justify-between py-3 border-b border-zinc-50 cursor-pointer group">
            <div className="flex items-center gap-3">
              {privacy.hide_reading_activity ? <EyeOff className="w-4 h-4 text-zinc-400" /> : <Eye className="w-4 h-4 text-black" />}
              <span className="text-sm font-medium">Ẩn hoạt động đọc</span>
            </div>
            <input
              type="checkbox"
              checked={privacy.hide_reading_activity}
              onChange={(e) => setPrivacy({ ...privacy, hide_reading_activity: e.target.checked })}
              className="w-4 h-4 accent-black"
            />
          </label>
          <label className="flex items-center justify-between py-3 border-b border-zinc-50 cursor-pointer group">
            <div className="flex items-center gap-3">
              {privacy.hide_library ? <EyeOff className="w-4 h-4 text-zinc-400" /> : <Eye className="w-4 h-4 text-black" />}
              <span className="text-sm font-medium">Ẩn thư viện cá nhân</span>
            </div>
            <input
              type="checkbox"
              checked={privacy.hide_library}
              onChange={(e) => setPrivacy({ ...privacy, hide_library: e.target.checked })}
              className="w-4 h-4 accent-black"
            />
          </label>
          <button
            onClick={savePrivacy}
            className="px-6 py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-all mt-4"
          >
            Lưu cài đặt
          </button>
        </div>
      </div>
    </div>
  );
}
