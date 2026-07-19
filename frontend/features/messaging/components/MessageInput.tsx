import React, { useRef, useState } from "react";
import { Paperclip, Mic, Pause, Trash2, Send, FileText, X, BarChart2 } from "lucide-react";
import { ReplyBlock } from "@/features/messaging/components/ReplyBlock";
import { useAudioRecording } from "@/features/messaging/hooks/useAudioRecording";

interface MessageInputProps {
  onSendMessage: (text: string, files: File[], audioBlob: File | null, replyToId?: string) => Promise<void>;
  replyingTo: any;
  onCancelReply: () => void;
  onOpenPollModal: () => void;
  onTyping: (isTyping: boolean) => void;
}

export function MessageInput({
  onSendMessage,
  replyingTo,
  onCancelReply,
  onOpenPollModal,
  onTyping,
}: MessageInputProps) {
  const [text, setText] = useState("");
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const {
    isRecording,
    isRecordingPaused,
    recordingDuration,
    handleStartRecording,
    handleTogglePauseRecording,
    handleStopRecording,
    handleCancelRecording
  } = useAudioRecording();

  const handleTyping = (e: React.ChangeEvent<HTMLInputElement>) => {
    setText(e.target.value);
    if (e.target.value.trim().length > 0) {
      onTyping(true);
    } else {
      onTyping(false);
    }
  };

  const handleSend = async () => {
    if (!text.trim() && imageFiles.length === 0 && !isRecording) return;
    
    let audioFile: File | null = null;
    if (isRecording) {
      audioFile = await handleStopRecording();
    }
    
    const replyToId = replyingTo ? (replyingTo._id || replyingTo.id) : undefined;
    
    await onSendMessage(text, imageFiles, audioFile, replyToId);
    
    setText("");
    setImageFiles([]);
    onTyping(false);
    if (replyingTo) onCancelReply();
  };

  return (
    <div className="px-4 pb-4 pt-2 bg-transparent relative flex-shrink-0">
      <ReplyBlock replyingTo={replyingTo} onCancel={onCancelReply} />

      {imageFiles.length > 0 && (
        <div className="flex gap-2 mb-3 overflow-x-auto hide-scrollbar pt-2">
          {imageFiles.map((file, idx) => {
            let objectUrl = "";
            const isImg = !!(file.type && file.type.startsWith("image/"));
            if (isImg) {
              try { objectUrl = URL.createObjectURL(file); } catch (err) {}
            }
            return (
              <div key={idx} className="relative w-16 h-16 shrink-0 rounded-[10px] overflow-hidden border border-[#D2D2D7] bg-white flex items-center justify-center">
                {isImg && objectUrl ? (
                  <img src={objectUrl} alt="" className="w-full h-full object-cover" />
                ) : (
                  <FileText className="w-6 h-6 text-[#6E6E73]" />
                )}
                <button onClick={() => setImageFiles(prev => prev.filter((_, i) => i !== idx))} className="absolute top-1 right-1 w-5 h-5 bg-black/50 rounded-full flex items-center justify-center text-white hover:bg-black/70">
                  <X className="w-3 h-3" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      <div className="flex items-center gap-3 h-[44px]">
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          multiple
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              const newFiles = Array.from(e.target.files);
              setImageFiles(prev => [...prev, ...newFiles]);
            }
            if (fileInputRef.current) fileInputRef.current.value = "";
          }}
        />
        <div className="flex-1 relative">
          {isRecording ? (
            <div className="w-full bg-[#E8E8ED] border border-transparent rounded-[980px] pl-4 pr-1.5 h-[44px] text-[15px] flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className={`w-2 h-2 bg-red-500 rounded-full ${!isRecordingPaused ? "animate-pulse" : ""}`} />
                <span className="text-red-500 font-medium">
                  {isRecordingPaused ? "Tạm dừng" : "Đang thu âm"} ({Math.floor(recordingDuration / 60)}:{(recordingDuration % 60).toString().padStart(2, "0")})
                </span>
              </div>
              <div className="flex items-center gap-0.5">
                <button onClick={handleTogglePauseRecording} className="w-8 h-8 flex items-center justify-center text-[#0071E3] hover:bg-black/5 rounded-full transition-colors">
                  {isRecordingPaused ? <Mic className="w-[18px] h-[18px]" /> : <Pause className="w-[18px] h-[18px]" />}
                </button>
                <button onClick={handleCancelRecording} className="w-8 h-8 flex items-center justify-center text-[#6E6E73] hover:text-red-500 hover:bg-black/5 rounded-full transition-colors">
                  <Trash2 className="w-[18px] h-[18px]" />
                </button>
              </div>
            </div>
          ) : (
            <>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="absolute left-1.5 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full z-10"
              >
                <Paperclip className="w-[18px] h-[18px]" />
              </button>
              <button
                onClick={onOpenPollModal}
                className="absolute left-[36px] top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full z-10"
              >
                <BarChart2 className="w-[18px] h-[18px]" />
              </button>
              <input
                type="text"
                value={text}
                onChange={handleTyping}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSend();
                }}
                placeholder="Nhập tin nhắn..."
                className="w-full h-[44px] bg-white border border-[#E8E8ED] rounded-[980px] pl-[70px] pr-[40px] text-[15px] focus:outline-none focus:border-[#0071E3] transition-colors"
              />
              <button
                onClick={handleStartRecording}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full z-10 transition-colors"
              >
                <Mic className="w-[18px] h-[18px]" />
              </button>
            </>
          )}
        </div>
        <button
          onClick={handleSend}
          disabled={!text.trim() && imageFiles.length === 0 && !isRecording}
          className="w-11 h-11 bg-[#0071E3] text-white rounded-full flex items-center justify-center hover:bg-[#0055C6] disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
        >
          <Send className="w-5 h-5 ml-0.5" />
        </button>
      </div>
    </div>
  );
}
