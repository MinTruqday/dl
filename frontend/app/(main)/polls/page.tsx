"use client";
import { useState, useEffect } from "react";
import { Vote, BarChart, Clock, MessageSquare, Share2, TrendingUp } from "lucide-react";

export default function PollsPage() {
  const [activePoll, setActivePoll] = useState<any>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPolls = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/social/polls`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('doclib_token')}` }
        });
        if (res.ok) {
          const data = await res.json();
          setActivePoll(data.active_poll || null);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchPolls();
  }, []);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 animate-in fade-in duration-500">
      <header className="border-b-2 border-black pb-8 mb-12">
        <div className="flex items-center gap-3 mb-2">
           <Vote className="w-5 h-5 text-black" />
           <span className="text-[12px] font-bold tracking-widest text-zinc-400">Tiếng nói cộng đồng</span>
        </div>
        <h1 className="text-4xl font-bold text-black tracking-tighter">Khảo sát & Bình chọn</h1>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
         <div className="lg:col-span-8 space-y-12">
            <section className="border border-black p-10 bg-white space-y-8 shadow-[12px_12px_0px_0px_rgba(0,0,0,1)]">
               {activePoll ? (
                  <>
                     <div className="space-y-2">
                        <h2 className="text-2xl font-bold tracking-tighter leading-tight">{activePoll.question}</h2>
                        <p className="text-[12px] font-bold text-zinc-400 tracking-widest flex items-center gap-2">
                           <Clock className="w-3.5 h-3.5" /> Kết thúc: {new Date(activePoll.end_date).toLocaleDateString("vi-VN")}
                        </p>
                     </div>

                     <div className="space-y-4">
                        {activePoll.options.map((opt: any) => (
                           <button 
                              key={opt.id}
                              onClick={() => setSelected(opt.id)}
                              className={`w-full p-6 border flex items-center justify-between transition-all duration-300 ${selected === opt.id ? 'bg-black text-white border-black' : 'bg-white border-zinc-100 hover:border-black'}`}
                           >
                              <div className="flex items-center gap-4">
                                 <div className={`w-5 h-5 border flex items-center justify-center ${selected === opt.id ? 'border-white' : 'border-black'}`}>
                                    {selected === opt.id && <div className="w-2.5 h-2.5 bg-white" />}
                                 </div>
                                 <span className="text-sm font-bold tracking-tight">{opt.text}</span>
                              </div>
                              <span className={`text-xs font-bold tabular-nums ${selected === opt.id ? 'text-zinc-400' : 'text-zinc-300'}`}>
                                 {activePoll.total_votes > 0 ? Math.round((opt.votes / activePoll.total_votes) * 100) : 0}%
                              </span>
                           </button>
                        ))}
                     </div>

                     <div className="flex items-center justify-between pt-6">
                        <p className="text-[12px] font-bold text-zinc-400 tracking-widest">Tổng cộng: {activePoll.total_votes?.toLocaleString() || 0} lượt bình chọn</p>
                        <button className="px-10 py-4 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-all">
                           Xác nhận bình chọn
                        </button>
                     </div>
                  </>
               ) : (
                  <div className="py-12 text-center text-zinc-500 font-medium">Hiện không có khảo sát nào đang diễn ra.</div>
               )}
            </section>

            <section className="space-y-6">
               <h3 className="text-xs font-bold tracking-widest border-l-4 border-black pl-4">Khảo sát đã kết thúc</h3>
               <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {[1, 2].map(i => (
                     <div key={i} className="border border-zinc-100 p-6 space-y-4 grayscale hover:grayscale-0 transition-all opacity-60 hover:opacity-100">
                        <div className="flex justify-between items-start">
                           <span className="text-[13px] font-bold tracking-widest text-zinc-400">01/04/2024</span>
                           <BarChart className="w-4 h-4 text-zinc-300" />
                        </div>
                        <h4 className="text-sm font-bold tracking-tight line-clamp-2">
                           Bạn đánh giá thế nào về giao diện Brutalist mới của DocLib?
                        </h4>
                        <div className="pt-2">
                           <div className="flex justify-between text-[12px] font-bold mb-1">
                              <span>Hài lòng</span>
                              <span>82%</span>
                           </div>
                           <div className="w-full h-1 bg-zinc-100 overflow-hidden">
                              <div className="w-[82%] h-full bg-black" />
                           </div>
                        </div>
                     </div>
                  ))}
               </div>
            </section>
         </div>

         <aside className="lg:col-span-4 space-y-12">
            <div className="border border-black p-8 space-y-6 bg-zinc-50">
               <h3 className="text-xs font-bold tracking-widest">Góp ý tính năng</h3>
               <p className="text-xs font-medium text-zinc-500 leading-relaxed">
                  Nếu bạn có ý tưởng tuyệt vời nào khác, đừng ngần ngại chia sẻ trực tiếp với đội ngũ phát triển.
               </p>
               <textarea 
                  className="w-full bg-white border border-zinc-200 p-4 text-xs font-medium outline-none focus:border-black transition-all h-32 resize-none"
                  placeholder="Mô tả tính năng bạn mong muốn"
               />
               <button className="w-full py-4 bg-black text-white text-[12px] font-bold tracking-widest">
                  Gửi ý tưởng
               </button>
            </div>
         </aside>
      </div>
    </div>
  );
}
