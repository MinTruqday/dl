"use client";
import React from "react";
import { ChevronRight, BookOpen, Lock } from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
} from "@/components/ui/Modal";

interface PreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: any;
}

export default function Preview({
  isOpen,
  onClose,
  document,
}: PreviewModalProps) {
  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-5xl h-full max-h-[85vh] flex flex-col p-0 md:p-0 overflow-hidden">
      {/* Header */}
      <div className="p-8 border-b border-zinc-100 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-6">
          <div className="w-12 h-12 bg-black flex items-center justify-center text-white shrink-0 rounded-sm">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <ModalTitle className="text-xl uppercase">{document.title}</ModalTitle>
            <ModalDescription>Bản xem trước giới hạn</ModalDescription>
          </div>
        </div>
      </div>

      {/* Content Preview */}
      <div className="flex-1 overflow-y-auto p-12 md:p-20 bg-white/20 scrollbar-none relative">
        <div className="max-w-3xl mx-auto space-y-12">
          <div className="prose prose-zinc max-w-none">
            <h2 className="text-4xl font-bold text-black mb-10 tracking-tight leading-tight">
              Mở đầu tri thức
            </h2>
            <div className="text-zinc-800 leading-relaxed text-lg font-medium space-y-6">
              {document.content ? (
                <div
                  dangerouslySetInnerHTML={{
                    __html: document.content
                      .slice(0, 2000)
                      .replace(/\n/g, "<br/>"),
                  }}
                />
              ) : (
                <p>{document.description}</p>
              )}
            </div>
          </div>

          {/* Fade out effect */}
          <div className="relative h-64 mt-10">
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-50 via-zinc-50/80 to-transparent z-10" />
            <div className="absolute inset-0 flex flex-col items-center justify-center z-20 gap-6">
              <div className="w-16 h-16 bg-white border border-zinc-100 flex items-center justify-center rounded-sm">
                <Lock className="w-6 h-6 text-zinc-300" />
              </div>
              <div className="text-center">
                <p className="text-sm font-bold text-black uppercase tracking-tight mb-2">
                  Đã đạt đến giới hạn xem trước
                </p>
                <p className="text-[11px] font-bold text-zinc-400">
                  Sở hữu tài liệu để khai mở toàn bộ kho tàng tri thức này
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Action */}
      <div className="p-8 border-t border-zinc-100 bg-white flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <span className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest italic">
            DocLib Premium Preview
          </span>
        </div>
        <button
          onClick={onClose}
          className="h-14 px-10 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] active:scale-95 flex items-center gap-3 rounded-sm transition-transform"
        >
          Mua tài liệu ngay <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </Modal>
  );
}

