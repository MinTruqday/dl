import React from "react";
import { NodeViewWrapper, NodeViewContent } from "@tiptap/react";

export default function NodeView() {
  return (
    <NodeViewWrapper className="latex-node-view relative my-4 p-4 bg-white border border-zinc-100 rounded-none group">
      <div className="absolute top-2 right-2 flex gap-2 opacity-0 ">
        <button className="px-2 py-1 bg-black text-white text-[10px] font-bold uppercase tracking-widest active:scale-95 ">
          Sửa
        </button>
      </div>
      <div className="flex flex-col gap-2">
        <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
          LaTeX Node
        </label>
        <div className="min-h-[40px] font-mono text-sm text-black">
          <NodeViewContent className="outline-none" placeholder="" />
        </div>
      </div>
    </NodeViewWrapper>
  );
}
