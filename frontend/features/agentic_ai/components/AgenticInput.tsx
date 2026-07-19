import React, { useRef, useEffect } from "react";
import { Folder, X, Paperclip, ArrowUp, Loader2 } from "lucide-react";

interface AgenticInputProps {
  input: string;
  setInput: (value: string) => void;
  handleSubmit: (e: React.FormEvent) => void;
  isSending: boolean;
  selectedFolder: any;
  setSelectedFolder: (folder: any) => void;
  fileInputRef: React.RefObject<HTMLInputElement>;
  textareaRef: React.RefObject<HTMLTextAreaElement>;
}

export function AgenticInput({
  input,
  setInput,
  handleSubmit,
  isSending,
  selectedFolder,
  setSelectedFolder,
  fileInputRef,
  textareaRef,
}: AgenticInputProps) {
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="p-4 md:p-6 sticky bottom-0 z-20">
      <div className="bg-[#F5F5F7] max-w-4xl mx-auto rounded-[24px] p-3 shadow-[0_2px_12px_rgba(0,0,0,0.04)] border border-[#E8E8ED]">
        {selectedFolder && (
          <div className="px-3 pb-2 pt-1 flex items-center gap-2">
            <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-[12px] border border-[#E8E8ED] text-[#1D1D1F] text-[13px] font-medium shadow-sm">
              <Folder className="w-4 h-4 text-[#0071E3]" />
              <span className="truncate max-w-[200px]">
                {selectedFolder.name}
              </span>
              <button
                onClick={() => setSelectedFolder(null)}
                className="p-0.5 hover:bg-[#F5F5F7] rounded-full transition-colors ml-1 text-[#86868B] hover:text-[#1D1D1F]"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
        <form onSubmit={handleSubmit} className="flex items-end gap-2 relative">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".zip"
            onChange={() => {
              if (fileInputRef.current?.files?.[0]) {
                const file = fileInputRef.current.files[0];
                setSelectedFolder({ name: file.name, isFile: true, file });
              }
            }}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-3 text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-white rounded-full transition-colors mb-0.5"
            disabled={isSending}
          >
            <Paperclip className="w-5 h-5" />
          </button>
          
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Bạn muốn thực hiện điều gì..."
            className="flex-1 bg-transparent px-3 py-3 text-[15px] text-[#1D1D1F] placeholder:text-[#86868B] focus:outline-none resize-none min-h-[48px] max-h-[120px] custom-scrollbar"
            rows={1}
            disabled={isSending}
          />

          <button
            type="submit"
            disabled={!input.trim() || isSending}
            className={`p-2.5 rounded-full mb-0.5 transition-all ${
              input.trim() && !isSending
                ? "bg-[#0071E3] text-white hover:bg-[#0055C6] shadow-sm"
                : "bg-white text-[#A1A1A6] border border-[#E8E8ED]"
            }`}
          >
            {isSending ? (
              <Loader2 className="w-5 h-5 animate-spin text-[#0071E3]" />
            ) : (
              <ArrowUp className="w-5 h-5" />
            )}
          </button>
        </form>
      </div>
      <p className="text-center text-[12px] text-[#86868B] mt-4 font-medium px-4">
        AI có thể mắc lỗi. Vui lòng kiểm tra lại thông tin quan trọng.
      </p>
    </div>
  );
}
