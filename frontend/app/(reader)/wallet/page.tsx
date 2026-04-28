'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/app/contexts/AuthContext';
import { Wallet, History, CreditCard, Gift, ArrowUpRight, ArrowDownLeft, Zap, Coins } from 'lucide-react';
import { API_URL, getToken } from '@/app/lib/api';

interface Transaction {
  _id: string;
  amount: number;
  type: string;
  status: string;
  note: string;
  created_at: string;
}

export default function WalletPage() {
  const { user } = useAuth();
  const [balance, setBalance] = useState<number>(0);
  const [history, setHistory] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [voucherCode, setVoucherCode] = useState('');
  const [isRedeeming, setIsRedeeming] = useState(false);
  const [message, setMessage] = useState<{ text: string, type: 'success' | 'error' } | null>(null);

  const fetchWalletData = async () => {
    setIsLoading(true);
    const token = getToken();
    if (!token) return;

    try {
      // Fetch Balance
      const balanceRes = await fetch(`${API_URL}/wallet/balance`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const balanceData = await balanceRes.json();
      if (balanceData.status === 200) setBalance(balanceData.data.balance);

      // Fetch History
      const historyRes = await fetch(`${API_URL}/wallet/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const historyData = await historyRes.json();
      if (historyData.status === 200) setHistory(historyData.data);
    } catch (error) {
      console.error('Failed to fetch wallet data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWalletData();
  }, []);

  const handleRedeemVoucher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!voucherCode.trim() || isRedeeming) return;

    setIsRedeeming(true);
    setMessage(null);
    const token = getToken();

    try {
      const res = await fetch(`${API_URL}/wallet/redeem-voucher`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code: voucherCode })
      });
      const data = await res.json();
      if (res.ok) {
        setMessage({ text: 'Nạp voucher thành công!', type: 'success' });
        setVoucherCode('');
        fetchWalletData();
      } else {
        setMessage({ text: data.detail || 'Voucher không hợp lệ hoặc đã hết hạn.', type: 'error' });
      }
    } catch (error) {
      setMessage({ text: 'Lỗi hệ thống, vui lòng thử lại sau.', type: 'error' });
    } finally {
      setIsRedeeming(false);
    }
  };

  const handleMomoTopup = () => {
     alert("Tính năng nạp tiền qua MoMo đang được tích hợp. Vui lòng quay lại sau!");
  };

  if (!user) return (
    <div className="flex flex-col items-center justify-center h-[60vh]">
        <p className="text-zinc-500 font-medium">Vui lòng đăng nhập để xem thông tin ví.</p>
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto py-10 px-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-black tracking-tight flex items-center gap-3">
          <Wallet className="w-8 h-8" />
          Ví của tôi
        </h1>
        <p className="text-zinc-500 mt-2 font-medium">Quản lý số dư dl và lịch sử giao dịch của bạn.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Balance & Top-up */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <div className="bg-black text-white rounded-md p-8 shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <Zap className="w-32 h-32 -mr-16 -mt-16" />
            </div>
            <p className="text-zinc-400 text-sm font-bold tracking-widest uppercase">Số dư hiện tại</p>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-5xl font-black">{balance}</span>
              <span className="text-xl font-bold text-zinc-400">dl</span>
            </div>
            <div className="mt-8 flex gap-3">
              <button 
                onClick={handleMomoTopup}
                className="flex-1 bg-white text-black py-3 px-4 rounded-sm font-bold text-sm hover:bg-zinc-100 transition-colors flex items-center justify-center gap-2"
              >
                <CreditCard className="w-4 h-4" />
                Nạp qua MoMo
              </button>
            </div>
          </div>

          <div className="bg-white border border-zinc-200 rounded-md p-6 shadow-sm">
            <h3 className="text-sm font-bold text-black flex items-center gap-2 mb-4">
              <Gift className="w-4 h-4" />
              Nạp bằng Voucher
            </h3>
            <form onSubmit={handleRedeemVoucher} className="space-y-3">
              <input
                type="text"
                placeholder="Nhập mã voucher (VD: DOCLIB2024)"
                value={voucherCode}
                onChange={(e) => setVoucherCode(e.target.value)}
                className="w-full px-4 py-3 bg-zinc-50 border border-zinc-200 rounded-sm text-sm focus:outline-none focus:border-black transition-colors"
              />
              <button
                type="submit"
                disabled={isRedeeming || !voucherCode.trim()}
                className="w-full bg-zinc-900 text-white py-3 rounded-sm font-bold text-sm hover:bg-black transition-colors disabled:opacity-50"
              >
                {isRedeeming ? 'Đang xử lý...' : 'Kích hoạt'}
              </button>
              {message && (
                <p className={`text-xs font-bold mt-2 ${message.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                  {message.text}
                </p>
              )}
            </form>
          </div>
        </div>

        {/* Right Column: History */}
        <div className="lg:col-span-2">
          <div className="bg-white border border-zinc-200 rounded-md overflow-hidden shadow-sm flex flex-col h-full">
            <div className="px-6 py-5 border-b border-zinc-200 flex items-center justify-between bg-zinc-50/50">
              <h3 className="font-bold text-black flex items-center gap-2">
                <History className="w-4 h-4" />
                Lịch sử giao dịch
              </h3>
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">{history.length} giao dịch</span>
            </div>

            <div className="flex-1 overflow-y-auto">
              {isLoading ? (
                <div className="p-10 text-center">
                  <div className="animate-spin w-6 h-6 border-2 border-black border-t-transparent rounded-full mx-auto"></div>
                </div>
              ) : history.length === 0 ? (
                <div className="p-20 text-center flex flex-col items-center">
                  <div className="w-12 h-12 bg-zinc-50 rounded-full flex items-center justify-center mb-4 text-zinc-300">
                    <History className="w-6 h-6" />
                  </div>
                  <p className="text-sm text-zinc-500 font-medium">Bạn chưa thực hiện giao dịch nào.</p>
                </div>
              ) : (
                <div className="divide-y divide-zinc-100">
                  {history.map((tx) => (
                    <div key={tx._id} className="px-6 py-4 flex items-center justify-between hover:bg-zinc-50 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${tx.type === 'TOPUP' ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
                          {tx.type === 'TOPUP' ? <ArrowDownLeft className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
                        </div>
                        <div>
                          <p className="text-sm font-bold text-black">{tx.note || (tx.type === 'TOPUP' ? 'Nạp tiền vào tài khoản' : 'Thanh toán dịch vụ')}</p>
                          <p className="text-[11px] text-zinc-400 font-bold uppercase tracking-tighter mt-0.5">
                            {new Date(tx.created_at).toLocaleDateString('vi-VN', { 
                              day: '2-digit', month: '2-digit', year: 'numeric',
                              hour: '2-digit', minute: '2-digit'
                            })}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-black ${tx.type === 'TOPUP' ? 'text-green-600' : 'text-black'}`}>
                          {tx.type === 'TOPUP' ? '+' : '-'}{tx.amount} dl
                        </p>
                        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">{tx.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
