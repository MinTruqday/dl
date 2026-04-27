"use client";
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Mathematics from '@tiptap/extension-mathematics';
import React, { useState, useEffect } from 'react';
import { LatexBlockExtension } from './LatexBlockExtension';
import { LatexAutocomplete } from './LatexAutoComplete';
import 'katex/dist/katex.min.css';
import { Code, FileText, Download, Bold, Italic, Play, Save, ChevronLeft, Loader2, List, Image as ImageIcon, Link as LinkIcon, Underline as UnderlineIcon, AlignLeft, AlignCenter, AlignRight, AlignJustify, Highlighter, CheckSquare, Subscript as SubscriptIcon, Superscript as SuperscriptIcon, Type, Undo, Redo, Strikethrough, Quote, Code as CodeIcon, SquareTerminal, Minus, Video, Sparkles } from 'lucide-react';
import { getToken } from '@/app/lib/api';


import Placeholder from '@tiptap/extension-placeholder';
import Table from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import Focus from '@tiptap/extension-focus';
import CharacterCount from '@tiptap/extension-character-count';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';
import Underline from '@tiptap/extension-underline';
import TextAlign from '@tiptap/extension-text-align';
import Highlight from '@tiptap/extension-highlight';
import Typography from '@tiptap/extension-typography';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import TextStyle from '@tiptap/extension-text-style';
import Color from '@tiptap/extension-color';
import Subscript from '@tiptap/extension-subscript';
import Superscript from '@tiptap/extension-superscript';
import Dropcursor from '@tiptap/extension-dropcursor';
import Youtube from '@tiptap/extension-youtube';

export default function TiptapEditor({ initialContent, onSave }: { initialContent?: string, onSave?: (data: string) => void }) {
  const [isPreview, setIsPreview] = useState(false);
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        history: { depth: 100 }
      }),
      Mathematics,
      LatexBlockExtension,
      LatexAutocomplete,
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
      Focus.configure({ className: 'has-focus', mode: 'all' }),
      CharacterCount.configure({ limit: 100000 }),
      Image.configure({ inline: true, allowBase64: true }),
      Link.configure({ openOnClick: false, autolink: true }),
      Underline,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Highlight.configure({ multicolor: true }),
      Typography,
      TaskList,
      TaskItem.configure({ nested: true }),
      TextStyle,
      Color,
      Subscript,
      Superscript,
      Dropcursor.configure({ color: '#000000', width: 2 }),
      Youtube.configure({ inline: false, width: 840, height: 472.5, controls: true }),
      Placeholder.configure({ placeholder: 'Bắt đầu soạn thảo nội dung hoặc gõ \\ để chèn mã LaTeX' })
    ],
    content: initialContent || '',
    editorProps: {
      attributes: {
        class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none min-h-[500px] border border-border p-4  bg-white',
      },
    },

    onUpdate: ({ editor }) => {
      onSave?.(editor.getHTML());
    },
  });

  useEffect(() => {
    if (editor && initialContent !== undefined && editor.getHTML() !== initialContent) {
      editor.commands.setContent(initialContent);
    }
  }, [initialContent, editor]);


  useEffect(() => {
    if (!editor) return;
    const interval = setInterval(() => {
      onSave?.(editor.getHTML());
    }, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, [editor, onSave]);

  const estimatedReadTime = Math.ceil(editor?.storage.characterCount.words() / 200) || 1;


  const handleCompile = async () => {
    if (!editor) return;
    setIsCompiling(true);
    try {
      const json = editor.getJSON();
      let latexContent = "";
      
      json.content?.forEach((node: any) => {
          if (node.type === 'latexBlock') {
              latexContent += node.attrs.text + "\n\n";
          } else if (node.type === 'paragraph') {
              const text = node.content?.map((c: any) => c.text || '').join('') || '';
              latexContent += text + "\n\n";
          }
      });
      
      if (!latexContent.trim()) {
         latexContent = editor.getText();
      }

      const token = localStorage.getItem('doclib_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/latex/compile-preview`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ content: latexContent, is_fragment: true })
      });

      if (!response.ok) {
        throw new Error('Không thể hiển thị bản xem trước: ' + await response.text());
      }
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setPreviewPdfUrl(`${url}#view=FitH&toolbar=0`);
      setIsPreview(true);
    } catch (error) {
      console.error(error);
      alert('Không thể xuất bản tài liệu lúc này.');
    } finally {
      setIsCompiling(false);
    }
  };

  const handleSynonyms = async () => {
    if (!editor) return;
    const { from, to } = editor.state.selection;
    const word = editor.state.doc.textBetween(from, to, ' ');
    if (!word || word.length > 50) {
      alert("Vui lòng chọn một từ để tìm từ đồng nghĩa.");
      return;
    }

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/inference/synonyms`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${getToken()}` 
        },
        body: JSON.stringify({ word, context: editor.getText().substring(Math.max(0, from - 100), Math.min(editor.getText().length, to + 100)) })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.synonyms && data.synonyms.length > 0) {
          const choice = window.prompt(`Từ đồng nghĩa gợi ý cho "${word}":\n${data.synonyms.join(", ")}\n\nNhập từ bạn muốn thay thế (hoặc để trống để bỏ qua):`);
          if (choice) {
            editor.chain().focus().insertContent(choice).run();
          }
        } else {
          alert("Không tìm thấy từ đồng nghĩa phù hợp.");
        }
      }
    } catch (e) { console.error(e); }
  };


  if (!editor) {
    return null;
  }

  return (
    <div className="flex flex-col w-full h-[85vh] mx-auto bg-white border border-border  animate-in fade-in duration-300 relative">
      <div className="flex justify-between items-center bg-white border-b border-border p-3">
        <div className="flex flex-wrap gap-2 items-center">
            <div className="flex gap-1 border-r pr-2 border-border">
              <button onClick={() => editor.chain().focus().undo().run()} disabled={!editor.can().undo()} className="p-2  bg-white text-zinc-600 hover:bg-zinc-100 disabled:opacity-50" title="Hoàn tác"><Undo className="w-4 h-4" /></button>
              <button onClick={() => editor.chain().focus().redo().run()} disabled={!editor.can().redo()} className="p-2  bg-white text-zinc-600 hover:bg-zinc-100 disabled:opacity-50" title="Làm lại"><Redo className="w-4 h-4" /></button>
            </div>

            <div className="flex gap-1 border-r pr-2 border-border">
              <button onClick={() => editor.chain().focus().toggleBold().run()} className={`p-2  transition-all duration-150 ${editor.isActive('bold') ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="In đậm"><Bold className="w-4 h-4" /></button>
              <button onClick={() => editor.chain().focus().toggleItalic().run()} className={`p-2  transition-all duration-150 ${editor.isActive('italic') ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="In nghiêng"><Italic className="w-4 h-4" /></button>
              <button onClick={() => editor.chain().focus().toggleUnderline().run()} className={`p-2  transition-all duration-150 ${editor.isActive('underline') ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Gạch chân"><UnderlineIcon className="w-4 h-4" /></button>
              <button onClick={() => editor.chain().focus().toggleStrike().run()} className={`p-2  transition-all duration-150 ${editor.isActive('strike') ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Gạch ngang"><Strikethrough className="w-4 h-4" /></button>
              <button onClick={() => editor.chain().focus().toggleHighlight().run()} className={`p-2  transition-all duration-150 ${editor.isActive('highlight') ? 'bg-zinc-200 text-black' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Tô sáng"><Highlighter className="w-4 h-4" /></button>
            </div>

            <div className="flex gap-1 border-r pr-2 border-border">
               <button onClick={() => editor.chain().focus().toggleCode().run()} className={`p-2  transition-all duration-150 ${editor.isActive('code') ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Mã nội dòng"><CodeIcon className="w-4 h-4" /></button>
               <button onClick={() => editor.chain().focus().toggleCodeBlock().run()} className={`p-2  transition-all duration-150 ${editor.isActive('codeBlock') ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Khối mã"><SquareTerminal className="w-4 h-4" /></button>
               <button onClick={() => editor.chain().focus().toggleBlockquote().run()} className={`p-2  transition-all duration-150 ${editor.isActive('blockquote') ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Trích dẫn"><Quote className="w-4 h-4" /></button>
               <button onClick={() => editor.chain().focus().setHorizontalRule().run()} className="p-2  transition-all duration-150 bg-white text-zinc-600 hover:bg-zinc-100" title="Đường phân cách"><Minus className="w-4 h-4" /></button>
            </div>


            <div className="flex gap-1 border-r pr-2 border-border">
               <button onClick={() => editor.chain().focus().toggleSubscript().run()} className={`p-2  transition-all duration-150 ${editor.isActive('subscript') ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Chỉ số dưới"><SubscriptIcon className="w-4 h-4" /></button>
               <button onClick={() => editor.chain().focus().toggleSuperscript().run()} className={`p-2  transition-all duration-150 ${editor.isActive('superscript') ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Chỉ số trên"><SuperscriptIcon className="w-4 h-4" /></button>
            </div>

            <div className="flex gap-1 border-r pr-2 border-border">
               <button onClick={() => editor.chain().focus().setTextAlign('left').run()} className={`p-2  transition-all duration-150 ${editor.isActive({ textAlign: 'left' }) ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Căn trái"><AlignLeft className="w-4 h-4" /></button>
               <button onClick={() => editor.chain().focus().setTextAlign('center').run()} className={`p-2  transition-all duration-150 ${editor.isActive({ textAlign: 'center' }) ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Căn giữa"><AlignCenter className="w-4 h-4" /></button>
               <button onClick={() => editor.chain().focus().setTextAlign('right').run()} className={`p-2  transition-all duration-150 ${editor.isActive({ textAlign: 'right' }) ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Căn phải"><AlignRight className="w-4 h-4" /></button>
               <button onClick={() => editor.chain().focus().setTextAlign('justify').run()} className={`p-2  transition-all duration-150 ${editor.isActive({ textAlign: 'justify' }) ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Căn đều"><AlignJustify className="w-4 h-4" /></button>
            </div>

            <div className="flex gap-1 border-r pr-2 border-border">
               <button onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()} className={`w-8 h-8  shrink-0 transition-all duration-150 font-bold text-xs ${editor.isActive('heading', { level: 1 }) ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`}>H1</button>
               <button onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} className={`w-8 h-8  shrink-0 transition-all duration-150 font-bold text-xs ${editor.isActive('heading', { level: 2 }) ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`}>H2</button>
               <button onClick={() => editor.chain().focus().toggleTaskList().run()} className={`p-2  transition-all duration-150 ${editor.isActive('taskList') ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Danh sách công việc"><CheckSquare className="w-4 h-4" /></button>
               <button onClick={() => { const url = window.prompt('Nhập URL liên kết:'); if (url) { editor.chain().focus().setLink({ href: url }).run(); } }} className={`p-2  transition-all duration-150 ${editor.isActive('link') ? 'bg-black text-white' : 'bg-white text-zinc-600 hover:bg-zinc-100'}`} title="Chèn Liên kết"><LinkIcon className="w-4 h-4" /></button>
               <button onClick={() => { const url = window.prompt('Nhập URL ảnh:'); if (url) { editor.chain().focus().setImage({ src: url }).run(); } }} className="p-2  transition-all duration-150 bg-white text-zinc-600 hover:bg-zinc-100" title="Chèn Ảnh"><ImageIcon className="w-4 h-4" /></button>
               <button onClick={() => { const url = window.prompt('Nhập URL Youtube:'); if (url) { editor.chain().focus().setYoutubeVideo({ src: url }).run(); } }} className="p-2  transition-all duration-150 bg-white text-zinc-600 hover:bg-zinc-100" title="Chèn Video Youtube"><Video className="w-4 h-4" /></button>
               <button 
                onClick={() => {
                  const headings = editor.getJSON().content?.filter((n: any) => n.type === 'heading') || [];
                  let tocHtml = "<div class='toc-container bg-zinc-50 p-6 border border-zinc-200 mb-8'><h2 class='text-sm font-bold tracking-widest mb-4'>Mục lục</h2><ul class='space-y-2'>";
                  headings.forEach((h: any) => {
                    const text = h.content?.map((c: any) => c.text || '').join('') || '';
                    const level = h.attrs.level;
                    tocHtml += `<li class='text-xs ${level === 1 ? 'font-bold' : 'ml-4'} hover:underline cursor-pointer'>${text}</li>`;
                  });
                  tocHtml += "</ul></div>";
                  editor.chain().focus().insertContent(tocHtml).run();
                }} 
                className="p-2  transition-all duration-150 bg-white text-zinc-600 hover:bg-zinc-100" 
                title="Tạo Mục lục (TOC)"
               ><List className="w-4 h-4" /></button>

            </div>


            <div className="flex gap-1 border-r pr-2 border-border">
               <button 
                 onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}
                 className="px-2 py-1.5  bg-white text-zinc-600 hover:bg-zinc-100 transition-all duration-150 text-xs font-bold"
               >
                 Chèn Bảng
               </button>
               <button 
                 onClick={() => editor.chain().focus().addColumnAfter().run()}
                 className="px-2 py-1.5  bg-white text-zinc-600 hover:bg-zinc-100 transition-all duration-150 text-xs font-bold"
               >
                 + Cột
               </button>
               <button 
                 onClick={() => editor.chain().focus().addRowAfter().run()}
                 className="px-2 py-1.5  bg-white text-zinc-600 hover:bg-zinc-100 transition-all duration-150 text-xs font-bold"
               >
                 + Hàng
               </button>
               <button 
                 onClick={() => editor.chain().focus().deleteTable().run()}
                 className="px-2 py-1.5  bg-zinc-50 text-black border border-zinc-200 hover:bg-zinc-100 transition-all duration-150 text-xs font-bold"
               >
                 Xóa Bảng
               </button>
            </div>

             <button 
                onClick={() => editor.chain().focus().setLatexBlock({ text: '\\documentclass{article}\n\\begin{document}\n\n\\end{document}' }).run()}
                className="px-4 py-1.5  bg-black text-white hover:bg-zinc-800 transition-all duration-150 flex gap-2 items-center text-xs font-bold tracking-tight"
             >
                <Code className="w-4 h-4" />
                Mã LaTeX
             </button>

              <button 
                onClick={handleSynonyms}
                className="px-4 py-1.5 border border-zinc-200 text-zinc-600 hover:bg-zinc-50 transition-all duration-150 flex gap-2 items-center text-xs font-bold tracking-tight"
              >
                <Sparkles className="w-4 h-4" />
                Gợi ý từ ngữ
              </button>
        </div>
        <div className="flex gap-2">
          {isPreview ? (
            <button 
              onClick={() => setIsPreview(false)} 
              className="px-4 py-1.5 bg-zinc-600 text-white  text-xs font-bold hover:bg-zinc-700 transition-all duration-300 flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Soạn thảo
            </button>
          ) : (
            <button 
               onClick={handleCompile} 
               disabled={isCompiling}
               className="px-4 py-1.5 bg-black text-white disabled:bg-zinc-100 disabled:text-zinc-400  text-xs font-bold hover:bg-zinc-800 transition-all duration-300 flex items-center gap-2"
            >
              {isCompiling ? (
                 <><Loader2 className="w-4 h-4 animate-spin" /> Đang xử lý</>
              ) : (
                 <><Play className="w-4 h-4" /> Bản xem trước</>
              )}
            </button>
          )}
          <button 
              onClick={() => onSave?.(editor.getHTML())} 
              className="px-4 py-1.5 bg-black text-white  text-xs font-bold hover:bg-zinc-800 transition-all duration-300 flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            Lưu
          </button>
        </div>
      </div>

      <div className="flex-1 w-full flex overflow-hidden relative bg-zinc-50/30">
         <div className={`h-full overflow-y-auto transition-all duration-500 ease-in-out ${isPreview ? 'w-1/2 border-r border-border' : 'w-full'} flex justify-center p-8`}>
            <div className="w-full max-w-4xl bg-white shadow-sm border border-border min-h-[800px]">
              <EditorContent editor={editor} className="h-full" />
            </div>
         </div>

         {isPreview && previewPdfUrl && (
             <div className="w-1/2 h-full border-l border-border  overflow-hidden bg-zinc-100 flex flex-col relative animate-in slide-in-from-right-8 fade-in duration-500">
                
                <div className="px-4 py-3 bg-black text-white text-xs flex justify-between items-center z-10">
                    <div className="flex items-center gap-3">
                         <div className="p-1.5 bg-zinc-800 ">
                            <FileText className="w-4 h-4 text-white" />
                         </div>
                        <span className="font-bold tracking-tight flex flex-col">
                           Bản in PDF
                           <span className="text-[13px] text-zinc-400 font-medium normal-case tracking-normal">Đã hoàn thành biên dịch</span>
                        </span>
                    </div>
                    <div className="flex gap-2">
                        <a href={previewPdfUrl} download="doclib-preview.pdf" className="p-1.5 hover:bg-zinc-800  transition-colors text-zinc-300 hover:text-white" title="Tải xuống">
                           <Download className="w-4 h-4" />
                        </a>
                    </div>
                </div>
                
                <div className="flex-1 bg-zinc-200 overflow-hidden relative p-4 lg:p-8 flex justify-center items-start">
                   <iframe 
                       src={previewPdfUrl} 
                       className="w-full max-w-[850px] aspect-[1/1.414] bg-white border border-border shadow-none transition-transform" 
                       style={{ minHeight: '100%' }}
                   />
                </div>
             </div>
         )}
      </div>
      <div className="absolute bottom-4 left-4 bg-white/80 backdrop-blur-sm px-3 py-1.5 border border-border text-[12px] font-bold text-zinc-500 tracking-widest pointer-events-none flex gap-4">
         <span>{editor.storage.characterCount.words()} Từ</span>
         <span>{editor.storage.characterCount.characters()} Ký tự</span>
         <span>Khoảng {estimatedReadTime} phút đọc</span>
      </div>

    </div>
  );
}

