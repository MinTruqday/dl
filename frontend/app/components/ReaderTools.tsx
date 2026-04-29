"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Moon,
  Sun,
  Volume2,
  VolumeX,
  Minus,
  Plus,
  Settings2,
  Play,
  Pause,
  Search,
  X,
} from "lucide-react";

interface ReaderToolsProps {
  onFontSizeChange: (size: number) => void;
  onThemeChange: (theme: "light" | "zinc" | "night") => void;
  textContent: string;
  onAutoScrollToggle?: (enabled: boolean) => void;
  onScrollSpeedChange?: (speed: number) => void;
  onSearchQuery?: (query: string) => void;
}

export default function ReaderTools({
  onFontSizeChange,
  onThemeChange,
  textContent,
  onAutoScrollToggle,
  onScrollSpeedChange,
  onSearchQuery,
}: ReaderToolsProps) {
  const [fontSize, setFontSize] = useState(16);
  const [theme, setTheme] = useState<"light" | "zinc" | "night">("light");
  const [isReading, setIsReading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [autoScroll, setAutoScroll] = useState(false);
  const [scrollSpeed, setScrollSpeed] = useState(2);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<number>(0);

  const handleFontSize = (delta: number) => {
    const newSize = Math.max(12, Math.min(32, fontSize + delta));
    setFontSize(newSize);
    onFontSizeChange(newSize);
  };

  const handleTheme = (t: "light" | "zinc" | "night") => {
    setTheme(t);
    onThemeChange(t);
  };

  const toggleTTS = () => {
    if (isReading) {
      window.speechSynthesis.cancel();
      setIsReading(false);
    } else {
      const utterance = new SpeechSynthesisUtterance(textContent);
      utterance.lang = "vi-VN";
      utterance.onend = () => setIsReading(false);
      window.speechSynthesis.speak(utterance);
      setIsReading(true);
    }
  };

  const toggleAutoScroll = () => {
    const newState = !autoScroll;
    setAutoScroll(newState);
    onAutoScrollToggle?.(newState);
  };

  const handleScrollSpeed = (delta: number) => {
    const newSpeed = Math.max(1, Math.min(10, scrollSpeed + delta));
    setScrollSpeed(newSpeed);
    onScrollSpeedChange?.(newSpeed);
  };

  const handleSearch = useCallback(
    (query: string) => {
      setSearchQuery(query);
      if (!query.trim()) {
        setSearchResults(0);
        onSearchQuery?.("");
        return;
      }
      const matches = textContent.toLowerCase().split(query.toLowerCase()).length - 1;
      setSearchResults(matches);
      onSearchQuery?.(query);
    },
    [textContent, onSearchQuery]
  );

  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  return (
    <div className="fixed bottom-8 right-8 z-[100] flex flex-col items-end gap-4 font-sans">
      {showSearch && (
        <div className="bg-white border border-zinc-200 p-6 animate-in slide-in-from-bottom-4 fade-in duration-300 w-80">
          <div className="flex items-center gap-3 mb-4">
            <Search className="w-4 h-4 text-zinc-400 shrink-0" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder=""
              className="flex-1 text-sm outline-none border-b border-zinc-100 pb-1 focus:border-black transition-all"
              autoFocus
            />
            <button
              onClick={() => {
                setShowSearch(false);
                handleSearch("");
              }}
              className="p-1 hover:bg-zinc-50 transition-colors"
            >
              <X className="w-4 h-4 text-zinc-400" />
            </button>
          </div>
          {searchQuery && (
            <p className="text-[11px] font-bold text-zinc-400">
              {searchResults > 0 ? `Tìm thấy ${searchResults} kết quả` : "Không tìm thấy kết quả"}
            </p>
          )}
        </div>
      )}

      {showSettings && (
        <div className="bg-white border border-zinc-200 p-8 space-y-8 animate-in slide-in-from-bottom-4 fade-in duration-300 w-72">
          <div className="space-y-4">
            <label className="text-[11px] font-bold text-zinc-400">Kích thước chữ</label>
            <div className="flex items-center justify-between bg-zinc-50 border border-zinc-100 p-2">
              <button
                onClick={() => handleFontSize(-2)}
                className="p-2 hover:bg-white border border-transparent hover:border-zinc-100 transition-all active:scale-90"
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="text-sm font-bold">{fontSize}px</span>
              <button
                onClick={() => handleFontSize(2)}
                className="p-2 hover:bg-white border border-transparent hover:border-zinc-100 transition-all active:scale-90"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="space-y-4">
            <label className="text-[11px] font-bold text-zinc-400">Chế độ hiển thị</label>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => handleTheme("light")}
                className={`p-2 border text-center text-[11px] font-bold transition-all ${
                  theme === "light" ? "bg-black text-white border-black" : "bg-white border-zinc-200 hover:border-black"
                }`}
              >
                Sáng
              </button>
              <button
                onClick={() => handleTheme("zinc")}
                className={`p-2 border text-center text-[11px] font-bold transition-all ${
                  theme === "zinc"
                    ? "bg-zinc-100 text-black border-zinc-400"
                    : "bg-white border-zinc-200 hover:border-black"
                }`}
              >
                Xám
              </button>
              <button
                onClick={() => handleTheme("night")}
                className={`p-2 border text-center text-[11px] font-bold transition-all ${
                  theme === "night" ? "bg-black text-white border-black" : "bg-white border-zinc-200 hover:border-black"
                }`}
              >
                Tối
              </button>
            </div>
          </div>

          <div className="space-y-4">
            <label className="text-[11px] font-bold text-zinc-400">Tự động cuộn</label>
            <div className="flex items-center justify-between">
              <button
                onClick={toggleAutoScroll}
                className={`flex items-center gap-2 px-4 py-2.5 border text-[11px] font-bold transition-all active:scale-95 ${
                  autoScroll ? "bg-black text-white border-black" : "border-zinc-200 hover:border-black"
                }`}
              >
                {autoScroll ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                <span>{autoScroll ? "Dừng" : "Bật"}</span>
              </button>
              {autoScroll && (
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleScrollSpeed(-1)}
                    className="p-1.5 hover:bg-zinc-50 border border-transparent hover:border-zinc-100 transition-all"
                  >
                    <Minus className="w-3 h-3" />
                  </button>
                  <span className="text-xs font-bold w-6 text-center">{scrollSpeed}</span>
                  <button
                    onClick={() => handleScrollSpeed(1)}
                    className="p-1.5 hover:bg-zinc-50 border border-transparent hover:border-zinc-100 transition-all"
                  >
                    <Plus className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={toggleTTS}
            className={`w-full p-4 border flex items-center justify-center gap-3 text-[11px] font-bold transition-all active:scale-[0.98] ${
              isReading ? "bg-black text-white border-black" : "border-zinc-200 hover:border-black"
            }`}
          >
            {isReading ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            <span>{isReading ? "Dừng đọc" : "Nghe đọc"}</span>
          </button>
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => {
            setShowSearch(!showSearch);
            setShowSettings(false);
          }}
          className="w-14 h-14 bg-zinc-800 text-white flex items-center justify-center transition-all hover:bg-black active:scale-90"
        >
          <Search className="w-5 h-5" />
        </button>
        <button
          onClick={() => {
            setShowSettings(!showSettings);
            setShowSearch(false);
          }}
          className="w-14 h-14 bg-black text-white flex items-center justify-center transition-all hover:bg-zinc-800 active:scale-90"
        >
          <Settings2 className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
}
