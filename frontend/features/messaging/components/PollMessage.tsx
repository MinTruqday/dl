import { useState } from "react";
import { CheckCircle2, Circle } from "lucide-react";
import { showToast } from "@/core/components/Toast";

interface PollOption {
  id: string;
  text: string;
  voter_ids: string[];
}

interface PollData {
  question: string;
  options: PollOption[];
  multiple_choice?: boolean;
}

interface PollMessageProps {
  messageId: string;
  pollData: PollData;
  currentUserId: string;
  onVote: (messageId: string, optionId: string) => Promise<void>;
}

export function PollMessage({ messageId, pollData, currentUserId, onVote }: PollMessageProps) {
  const [isVoting, setIsVoting] = useState(false);

  const totalVotes = pollData.options.reduce((sum, opt) => sum + opt.voter_ids.length, 0);

  const handleVote = async (optionId: string) => {
    if (isVoting) return;
    setIsVoting(true);
    try {
      await onVote(messageId, optionId);
    } catch (err: any) {
      showToast(err.message || "Bỏ phiếu thất bại", "error");
    } finally {
      setIsVoting(false);
    }
  };

  return (
    <div className="w-full min-w-[260px] max-w-[320px] bg-white rounded-[18px] border border-[#E8E8ED] overflow-hidden shadow-sm flex flex-col">
      <div className="p-4 border-b border-[#E8E8ED] bg-[#F5F5F7]">
        <h4 className="font-semibold text-[#1D1D1F] text-[15px] leading-snug">
          {pollData.question}
        </h4>
        <span className="text-[12px] text-[#6E6E73] mt-1 block">Bình chọn • {totalVotes} lượt vote</span>
      </div>
      <div className="p-2 space-y-1">
        {pollData.options.map((opt) => {
          const voteCount = opt.voter_ids.length;
          const percentage = totalVotes > 0 ? Math.round((voteCount / totalVotes) * 100) : 0;
          const hasVoted = opt.voter_ids.includes(currentUserId);

          return (
            <div 
              key={opt.id}
              onClick={() => handleVote(opt.id)}
              className="relative rounded-[10px] overflow-hidden cursor-pointer group transition-colors"
            >
              {/* Progress Bar background */}
              <div 
                className="absolute inset-0 bg-[#E8E8ED] origin-left transition-transform duration-500 ease-out"
                style={{ transform: `scaleX(${percentage / 100})`, opacity: hasVoted ? 0.8 : 0.4 }}
              />
              {/* Hover effect */}
              <div className="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity" />
              
              <div className="relative flex items-center justify-between p-3 z-10">
                <div className="flex items-center gap-3">
                  {hasVoted ? (
                    <CheckCircle2 className="w-[18px] h-[18px] text-[#0071E3] shrink-0" />
                  ) : (
                    <Circle className="w-[18px] h-[18px] text-[#6E6E73] shrink-0" />
                  )}
                  <span className={`text-[15px] font-medium ${hasVoted ? "text-[#0071E3]" : "text-[#1D1D1F]"}`}>
                    {opt.text}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {voteCount > 0 && (
                     <div className="flex -space-x-1.5 mr-1">
                        {/* Simulate avatars if we had them, just showing count for now */}
                        <div className="w-5 h-5 rounded-full bg-white border border-[#D2D2D7] flex items-center justify-center text-[9px] font-bold text-[#6E6E73]">
                          {voteCount}
                        </div>
                     </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
