"use client";

import React, { useState } from "react";
 

interface collectorStatus {
  id: string;
  source: string;
  target_url: string;
  status: "idle" | "running" | "completed" | "failed";
  last_run: string | null;
  items_collected: number;
}

export default function collectorManagerPage() {
  const [collectors, setcollectors] = useState<collectorStatus[]>([
    {
      id: "hcm-bio",
      source: "HoChiMinhCollection",
      target_url: "https:
      status: "idle",
      last_run: "2026-04-19 10:00:00",
      items_collected: 45,
    },
    {
      id: "nxbgd-books",
      source: "NXBGDCollection",
      target_url: "https:
      status: "idle",
      last_run: "2026-04-19 11:30:00",
      items_collected: 1200,
    }
  ]);
  const [runningId, setRunningId] = useState<string | null>(null);

  const startcollector = async (id: string) => {
    setRunningId(id);
    setcollectors(prev => prev.map(c => c.id === id ? { ...c, status: "running" } : c));
    try {
      const token = localStorage.getItem("access_token") || "";
      
      
      
      
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setcollectors(prev => prev.map(c => 
        c.id === id 
          ? { 
              ...c, 
              status: "completed", 
              last_run: new Date().toLocaleString("vi-VN"),
              items_collected: c.items_collected + Math.floor(Math.random() * 10) + 1 
            } 
          : c
      ));
    } catch (err: any) {
      console.error(err);
      setcollectors(prev => prev.map(c => c.id === id ? { ...c, status: "failed" } : c));
      alert("Hệ thống đang bảo trì dữ liệu, không thể khởi chạy bộ thu thập ngay lúc này.");
    } finally {
      if (runningId === id) setRunningId(null);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="border-b pb-4 border-gray-200">
        <h1 className="text-2xl font-semibold tracking-tight">Nguồn thu thập dữ liệu</h1>
        <p className="text-sm text-gray-500 mt-1">Quản lý và kích hoạt các bộ thu thập dữ liệu sách ngoại vi (collector/Scraper)</p>
      </div>

      <div className="border border-gray-200 bg-white">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-50 border-b border-gray-200 text-gray-700">
            <tr>
              <th className="px-4 py-3 font-medium">Bản thu thập (Collection)</th>
              <th className="px-4 py-3 font-medium">Nguồn đích (URL)</th>
              <th className="px-4 py-3 font-medium">Cập nhật lúc</th>
              <th className="px-4 py-3 font-medium">Đã thu thập</th>
              <th className="px-4 py-3 font-medium">Trạng thái</th>
              <th className="px-4 py-3 font-medium whitespace-nowrap w-32 text-right">Hành động</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {collectors.map((collector) => (
              <tr key={collector.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-900">{collector.source}</td>
                <td className="px-4 py-3 text-gray-500 truncate max-w-[200px]" title={collector.target_url}>
                  {collector.target_url}
                </td>
                <td className="px-4 py-3 text-gray-500">{collector.last_run || "Chưa chạy"}</td>
                <td className="px-4 py-3 text-gray-500">{collector.items_collected} bản ghi</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center px-2 py-0.5 border text-[10px] font-bold tracking-widest ${
                    collector.status === 'running' 
                      ? 'border-black text-white bg-black' 
                      : collector.status === 'completed'
                      ? 'border-black text-black bg-white'
                      : collector.status === 'failed'
                      ? 'border-zinc-200 text-zinc-400 bg-white'
                      : 'border-zinc-100 text-zinc-400 bg-zinc-50'
                  }`}>
                    {collector.status === 'running' ? 'Đang chạy' : 
                     collector.status === 'completed' ? 'Hoàn tất' : 
                     collector.status === 'failed' ? 'Lỗi' : 'Sẵn sàng'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => startcollector(collector.id)}
                    disabled={collector.status === "running"}
                    className="inline-flex items-center justify-center px-3 py-1 text-xs font-medium text-white bg-black hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {collector.status === "running" ? "Đang xử lý" : "Khởi động"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}