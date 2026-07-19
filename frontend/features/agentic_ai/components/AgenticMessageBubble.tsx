import React, { useEffect, useState } from "react";
import { User, Sparkles, Folder, Activity, ChevronDown, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remarkGfm";
import remarkMath from "remarkMath";
import rehypeKatex from "rehypeKatex";
import rehypeHighlight from "rehypeHighlight";
import { ThoughtTimer } from "./ThoughtTimer";
import { UserMessage } from "./UserMessage";
import { PayOSEmbedded } from "./PayOSEmbedded";
import "katex/dist/katex.min.css";

interface AgenticMessageBubbleProps {
  msg: any;
  idx: number;
  isSending: boolean;
  isLastMessage: boolean;
}

export function AgenticMessageBubble({ msg, idx, isSending, isLastMessage }: AgenticMessageBubbleProps) {
  if (msg.role === "user") {
    return (
      <div className="flex justify-end mb-6">
        <div className="max-w-[85%] md:max-w-[75%]">
          {msg.attachments && msg.attachments.folder && (
            <div className="mb-2 flex justify-end">
              <span className="inline-flex items-center gap-1.5 bg-[#F5F5F7] px-3 py-1.5 rounded-[12px] text-[13px] font-medium text-[#1D1D1F] border border-[#E8E8ED]">
                <Folder className="w-3.5 h-3.5 text-[#0071E3]" />
                {msg.attachments.folder}
              </span>
            </div>
          )}
          {msg.content && <UserMessage content={msg.content} />}
        </div>
      </div>
    );
  }

  const displayContent = msg.isThinkingEnabled ? msg.content : msg.content.replace(/<think>[\s\S]*?(?:<\/think>|$)/g, "");
  const segments = displayContent
    .split(/(<think>[\s\S]*?(?:<\/think>|$))/g)
    .filter((s: string) => s.trim() !== "");
  
  const isLastAssistant = isLastMessage && msg.role === "assistant";

  return (
    <div className="flex justify-start mb-6">
      <div className="w-full">
        <div className="py-2 w-full relative group">
          {msg.isThinkingEnabled && msg.thoughts && msg.thoughts.length > 0 && (
            <div className="mb-3 mt-1">
              <details className="group/details bg-[#F5F5F7] rounded-[14px] overflow-hidden border border-[#E8E8ED]" open={isSending && isLastMessage}>
                <summary className="flex items-center gap-2 px-4 py-2.5 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-transparent group-open/details:border-[#E8E8ED] transition-colors">
                  <div className="flex-1 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-[#0071E3]" />
                    <span className="text-[14px] font-semibold text-[#1D1D1F]">
                      Quá trình xử lý
                    </span>
                  </div>
                  <ChevronDown className="w-4 h-4 text-[#86868B] transition-transform duration-200 group-open/details:rotate-180" />
                </summary>
                <div className="px-4 py-3 bg-white text-[14px] text-[#6E6E73] border-t border-[#E8E8ED] flex flex-col gap-2">
                  {msg.thoughts.map((t: string, tIdx: number) => (
                    <div key={tIdx} className="flex gap-2 items-start">
                      <div className="mt-1">
                        {(isSending && isLastMessage && tIdx === msg.thoughts!.length - 1) ? (
                          <Loader2 className="w-3.5 h-3.5 text-[#0071E3] animate-spin" />
                        ) : (
                          <div className="w-1.5 h-1.5 rounded-full bg-[#34C759] mt-1" />
                        )}
                      </div>
                      <span className="text-[14px] text-[#1D1D1F] leading-relaxed">{t}</span>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}
          {segments.map((segment: string, sIdx: number) => {
            if (segment.startsWith("<think>")) {
              const thinkContent = segment.replace(/^<think>/, "").replace(/<\/think>$/, "").trim();
              
              return (
                <div key={sIdx} className="mb-3 mt-1">
                  <details className="group/details bg-[#F5F5F7] rounded-[14px] overflow-hidden border border-[#E8E8ED]" open={isSending && isLastMessage && sIdx === segments.length - 1}>
                    <summary className="flex items-center gap-2 px-4 py-2.5 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-transparent group-open/details:border-[#E8E8ED] transition-colors">
                      <div className="flex-1 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-[#0071E3]" />
                        <span className="text-[14px] font-semibold text-[#1D1D1F]">
                          <ThoughtTimer isRunning={isSending && isLastMessage && sIdx === segments.length - 1} />
                        </span>
                      </div>
                      <ChevronDown className="w-4 h-4 text-[#86868B] transition-transform duration-200 group-open/details:rotate-180" />
                    </summary>
                    <div className="px-4 py-3 bg-white text-[14px] text-[#6E6E73] border-t border-[#E8E8ED]">
                      {thinkContent ? (
                        <div className="prose prose-sm max-w-none prose-zinc prose-p:leading-relaxed text-[#6E6E73]">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm as any, remarkMath as any]}
                            rehypePlugins={[rehypeKatex as any, rehypeHighlight as any]}
                          >
                            {thinkContent}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <div className="flex gap-2 items-center py-1">
                          <Loader2 className="w-4 h-4 text-[#0071E3] animate-spin" />
                          <span className="text-[14px] text-[#6E6E73] font-medium animate-pulse">
                            Đang kích hoạt không gian suy luận...
                          </span>
                        </div>
                      )}
                    </div>
                  </details>
                </div>
              );
            }

            return (
              <ReactMarkdown
                key={sIdx}
                remarkPlugins={[remarkGfm as any, remarkMath as any]}
                rehypePlugins={[rehypeKatex as any, rehypeHighlight as any]}
                className="prose prose-sm max-w-none prose-zinc prose-p:text-[15px] prose-p:text-[#1D1D1F] prose-p:leading-relaxed prose-code:bg-[#F5F5F7] prose-code:text-[#FF3B30] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-[6px] prose-pre:bg-[#1D1D1F] prose-pre:rounded-[14px]"
                components={{
                  a: ({ href, children, ...props }) => {
                    if (
                      href &&
                      (href.includes("payos.vn") ||
                        href.includes("pay.payos.vn"))
                    ) {
                      return <PayOSEmbedded checkoutUrl={href} />;
                    }
                    return (
                      <a
                        href={href}
                        className="text-[#0071E3] font-medium hover:underline"
                        target="_blank"
                        rel="noreferrer"
                        {...props}
                      >
                        {children}
                      </a>
                    );
                  },
                }}
              >
                {segment}
              </ReactMarkdown>
            );
          })}
        </div>
      </div>
    </div>
  );
}
