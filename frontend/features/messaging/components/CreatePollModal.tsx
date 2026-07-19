import { useState } from "react";
import { X, Plus, Trash2 } from "lucide-react";
import { showToast } from "@/core/components/Toast";

interface CreatePollModalProps {
  onClose: () => void;
  onSubmit: (question: string, options: string[]) => Promise<void>;
}

export function CreatePollModal({ onClose, onSubmit }: CreatePollModalProps) {
  const [question, setQuestion] = useState("");
  const [options, setOptions] = useState<string[]>(["", ""]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAddOption = () => {
    if (options.length >= 10) {
      showToast("Tối đa 10 lựa chọn", "error");
      return;
    }
    setOptions([...options, ""]);
  };

  const handleRemoveOption = (index: number) => {
    if (options.length <= 2) return;
    setOptions(options.filter((_, i) => i !== index));
  };

  const handleChangeOption = (index: number, val: string) => {
    const newOptions = [...options];
    newOptions[index] = val;
    setOptions(newOptions);
  };

  const handleSubmit = async () => {
    const validOptions = options.filter(o => o.trim() !== "");
    if (!question.trim()) {
      showToast("Vui lòng nhập câu hỏi", "error");
      return;
    }
    if (validOptions.length < 2) {
      showToast("Cần ít nhất 2 lựa chọn", "error");
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(question, validOptions);
      showToast("Tạo bình chọn thành công");
      onClose();
    } catch (error: any) {
      showToast(error.message || "Tạo bình chọn thất bại", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div 
        className="bg-white rounded-[18px] w-full max-w-[400px] flex flex-col overflow-hidden shadow-2xl p-5"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-[#1D1D1F] text-[18px]">Tạo bình chọn</h3>
          <button onClick={onClose} className="p-1.5 rounded-full hover:bg-[#F5F5F7] text-[#6E6E73] transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4 max-h-[60vh] overflow-y-auto hide-scrollbar">
          <div>
            <label className="block text-[13px] font-medium text-[#6E6E73] mb-1">Câu hỏi</label>
            <input 
              type="text" 
              value={question}
              onChange={e => setQuestion(e.target.value)}
              placeholder="Đặt câu hỏi bình chọn..."
              className="w-full bg-[#F5F5F7] text-[15px] rounded-[10px] px-3 py-2.5 outline-none focus:ring-1 focus:ring-[#0071E3] transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-[13px] font-medium text-[#6E6E73] mb-1">Các lựa chọn</label>
            {options.map((opt, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <input 
                  type="text" 
                  value={opt}
                  onChange={e => handleChangeOption(idx, e.target.value)}
                  placeholder={`Lựa chọn ${idx + 1}`}
                  className="flex-1 bg-[#F5F5F7] text-[15px] rounded-[10px] px-3 py-2 outline-none focus:ring-1 focus:ring-[#0071E3] transition-all"
                />
                {options.length > 2 && (
                  <button onClick={() => handleRemoveOption(idx)} className="p-2 text-[#6E6E73] hover:text-red-500 rounded-full hover:bg-[#FFF5F5] transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
            <button 
              onClick={handleAddOption}
              className="flex items-center gap-2 text-[#0071E3] text-[14px] font-medium mt-2 hover:opacity-80 transition-opacity p-1"
            >
              <Plus className="w-4 h-4" /> Thêm lựa chọn
            </button>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-[#E8E8ED]">
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full bg-[#0071E3] text-white rounded-[10px] py-2.5 font-medium flex items-center justify-center gap-2 hover:bg-[#0055C6] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Tạo bình chọn
          </button>
        </div>
      </div>
    </div>
  );
}
