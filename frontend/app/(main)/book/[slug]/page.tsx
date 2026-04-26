import BookmarkButton from "@/app/components/BookmarkButton";
import ReviewSection from "@/app/components/ReviewSection";
import DiscussionSection from "@/app/components/DiscussionSection";
import ReaderView from "@/app/components/ReaderView";
import { Metadata } from "next";
import Link from "next/link";
import { Eye, Star, ExternalLink, AlertTriangle, ChevronLeft } from "lucide-react";

const INTERNAL_API_URL = process.env.INTERNAL_API_URL;

interface DocLibBook {
  _id: string;
  title: string;
  slug: string;
  description: string;
  status: string;
  file_url?: string;
  content?: string;
  author_id: string;
  views?: number;
  average_rating?: number;
  rating_count?: number;
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  try {
    const res = await fetch(`${INTERNAL_API_URL}/books/slug/${params.slug}`);
    if (res.ok) {
      const book: DocLibBook = await res.json();
      return {
        title: `${book.title} | DocLib`,
        description: book.description,
      }
    }
  } catch (error) {}
  
  return { title: "Không tìm thấy tài liệu | DocLib" }
}

async function getBookDetail(slug: string): Promise<DocLibBook | null> {
  try {
    const res = await fetch(`${INTERNAL_API_URL}/books/slug/${slug}`, {
      next: { revalidate: 10 }
    });
    if (!res.ok) return null;
    return res.json();
  } catch (error) {
    console.error("Fetch detail error:", error);
    return null;
  }
}

export default async function BookProfilePage({ params }: { params: { slug: string } }) {
  const book = await getBookDetail(params.slug);

  if (!book) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center animate-in fade-in duration-300">
        <h1 className="text-3xl font-bold text-black mb-4">Không tìm thấy tài liệu</h1>
        <p className="text-zinc-500 mb-8">Trang bạn yêu cầu không tồn tại hoặc đã bị xóa.</p>
        <Link href="/" className="px-6 py-3 bg-black text-white  hover:bg-zinc-800 transition-all duration-150">
          Trở về Trang chủ
        </Link>
      </div>
    );
  }

  const renderPdfUrl = book.file_url ? book.file_url : null;

  return (
    <div className="w-full animate-in fade-in duration-300">
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 pb-20">
        <Link href="/" className="inline-flex items-center text-sm font-bold text-zinc-400 hover:text-black mb-8 transition-colors gap-1.5 tracking-tight">
          <ChevronLeft className="w-4 h-4" />
          Quay lại danh sách
        </Link>

        <div className="bg-white  border border-border overflow-hidden">
          <div className="p-8 sm:p-12">
            <div className="flex items-center space-x-3 mb-6">
              <span className={`px-4 py-1.5  text-[10px] font-bold tracking-widest ${book.status === "published" ? "bg-black text-white" : "bg-zinc-100 text-black"}`}>
                {book.status === "published" ? "Xuất bản" : book.status === "draft" ? "Bản thảo" : book.status}
              </span>
              <span className="text-[10px] text-zinc-400 font-bold tracking-widest">ID: {book.slug}</span>
              <span className="text-zinc-200">|</span>
              <div className="flex items-center text-[11px] font-bold text-zinc-500 gap-1.5">
                <Eye className="w-3.5 h-3.5" />
                {book.views || 0}
              </div>
              <div className="flex items-center text-[11px] font-bold text-black gap-1.5">
                <Star className="w-3.5 h-3.5" />
                {book.average_rating ? Number(book.average_rating).toFixed(1) : "Chưa có"} <span className="text-zinc-400 ml-1">({book.rating_count || 0})</span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4 border-b border-border pb-8">
              <h1 className="text-4xl sm:text-5xl font-extrabold text-black leading-tight tracking-tighter">
                {book.title}
              </h1>
              <BookmarkButton bookId={book._id} />
            </div>
            
            <div className="prose prose-zinc prose-lg text-zinc-600 max-w-none mb-12 leading-relaxed">
              <p>{book.description || "Tác giả chưa cung cấp mô tả cho tài liệu này."}</p>
            </div>

            {book.content ? (
              <div className="border-t border-border mt-12 pt-12">
                 <ReaderView content={book.content} title={book.title} />
              </div>
            ) : renderPdfUrl ? (
              <div className="border-t border-border pt-12">
                <div className="flex items-center justify-between mb-8">
                  <h3 className="text-xl font-bold text-black tracking-tight">Bản đọc</h3>
                  <a href={renderPdfUrl} target="_blank" rel="noreferrer" className="text-[11px] font-bold flex items-center space-x-2 text-black hover:bg-zinc-100 border border-border px-4 py-2  transition-all tracking-widest">
                    <ExternalLink className="w-4 h-4" />
                    <span>Mở toàn màn hình</span>
                  </a>
                </div>
                <div className="w-full bg-zinc-50  border border-border" style={{ height: "800px" }}>
                  <iframe 
                    src={renderPdfUrl} 
                    className="w-full h-full"
                    title="DocLib Live PDF Reader"
                  />
                </div>
              </div>
            ) : (
               <div className="border-t border-border pt-12 mt-12">
                 <div className="bg-zinc-50 border border-border p-10  text-center flex flex-col items-center">
                    <div className="w-12 h-12 rounded-none bg-zinc-200 flex items-center justify-center mb-4">
                      <AlertTriangle className="w-6 h-6 text-black" />
                    </div>
                    <h3 className="text-lg font-bold text-black mb-2">Tài liệu đang được hoàn thiện</h3>
                    <p className="text-sm text-zinc-500 max-w-md">Tài liệu chưa có nội dung trực tuyến hoặc PDF. Tác giả hiện đang chuẩn bị nội dung. Vui lòng quay lại sau.</p>
                 </div>
               </div>
            )}
            
            <div className="mt-12">
              <ReviewSection bookId={book._id} />
            </div>
            <div className="mt-12">
              <DiscussionSection bookId={book._id} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}