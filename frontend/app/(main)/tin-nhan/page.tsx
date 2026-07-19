"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/core/context/AuthContext";
import { PageLoader } from "@/shared/components/common/PageLoader";
import { getConversationsAPI, updateConversationSettingsAPI, getConversationMessagesAPI, sendMessageAPI, recallMessageAPI, deleteMessageForMeAPI, reactMessageAPI, pinMessageAPI, editMessageAPI, forwardMessageAPI, createPollAPI, votePollAPI } from "@/features/messaging/services/thread.service";
import { uploadFileAPI } from "@/features/storage/services/file.service";
import { showToast } from "@/core/components/Toast";

import { MessageSidebar } from "@/features/messaging/components/MessageSidebar";
import { MessageHeader } from "@/features/messaging/components/MessageHeader";
import { MessageBubble } from "@/features/messaging/components/MessageBubble";
import { MessageInput } from "@/features/messaging/components/MessageInput";
import { ForwardModal } from "@/features/messaging/components/ForwardModal";
import { CreatePollModal } from "@/features/messaging/components/CreatePollModal";
import { useMessageWebSocket } from "@/features/messaging/hooks/useMessageWebSocket";

export default function MessagingPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [conversations, setConversations] = useState<any[]>([]);
  const [loadingConv, setLoadingConv] = useState(true);
  const [messages, setMessages] = useState<any[]>([]);
  const [loadingMsgs, setLoadingMsgs] = useState(false);
  const [selectedConv, setSelectedConv] = useState<any>(null);

  const [onlineUsers, setOnlineUsers] = useState<{[key: string]: boolean}>({});
  const [typingUsers, setTypingUsers] = useState<{[key: string]: boolean}>({});
  
  const conversationsRef = useRef<any[]>([]);
  const selectedConvRef = useRef<any>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const [activeMsgMenuId, setActiveMsgMenuId] = useState<string | null>(null);
  const [showDeleteSubMenu, setShowDeleteSubMenu] = useState<string | null>(null);
  const [activeMsgRect, setActiveMsgRect] = useState<any>(null);
  const [activeMsgObj, setActiveMsgObj] = useState<any>(null);

  const [showForwardModal, setShowForwardModal] = useState<string | null>(null);
  const [showPollModal, setShowPollModal] = useState(false);
  const [replyingTo, setReplyingTo] = useState<any>(null);

  const updateConversationInPlace = useCallback((senderId: string, messageData: any) => {
    setConversations((prev) => {
      const idx = prev.findIndex((c) => c.other_user_id === senderId || c._id === senderId);
      if (idx === -1) return prev;
      const updated = [...prev];
      const conv = { ...updated[idx], last_message: messageData };
      if (selectedConvRef.current && (selectedConvRef.current.other_user_id !== senderId && selectedConvRef.current._id !== senderId))
        conv.unread_count = (conv.unread_count || 0) + 1;
      updated.splice(idx, 1);
      updated.unshift(conv);
      conversationsRef.current = updated;
      return updated;
    });
  }, []);

  const { socketRef, sendTypingEvent, markAsRead } = useMessageWebSocket({
    user,
    conversationsRef,
    selectedConvRef,
    setMessages,
    updateConversationInPlace,
    setOnlineUsers,
    setTypingUsers
  });

  const loadConversations = useCallback(async () => {
    try {
      const res = await getConversationsAPI();
      const loaded = res.data || res || [];
      setConversations(loaded);
      conversationsRef.current = loaded;
      if (socketRef.current?.readyState === WebSocket.OPEN) {
          const userIds = loaded.filter((c:any) => c.type !== 'group').map((c: any) => c.other_user_id);
          if (userIds.length > 0) {
              socketRef.current.send(JSON.stringify({ action: "check_online", data: { user_ids: userIds } }));
          }
      }
    } catch (err: any) {
      showToast("Lỗi đồng bộ danh sách", "error");
    } finally {
      setLoadingConv(false);
    }
  }, [socketRef]);

  useEffect(() => {
    if (!authLoading && !user) router.push("/dang-nhap");
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!authLoading && user) loadConversations();
  }, [authLoading, user, loadConversations]);

  useEffect(() => {
    if (messagesContainerRef.current && !loadingMsgs) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages.length, loadingMsgs]);

  const selectConversation = async (conv: any) => {
    setSelectedConv(conv);
    selectedConvRef.current = conv;
    setMessages([]);
    setLoadingMsgs(true);
    setReplyingTo(null);
    try {
      const isGroup = conv.type === "group";
      const targetId = isGroup ? conv._id : conv.other_user_id;
      const res = await getConversationMessagesAPI(targetId, 1, 50, isGroup);
      const msgs = res.data?.items || res.items || res.data || [];
      setMessages(msgs.reverse());
      markAsRead(targetId);
      
      setConversations((prev) => prev.map((c) => {
        if ((isGroup && c._id === targetId) || (!isGroup && c.other_user_id === targetId)) {
          return { ...c, unread_count: 0 };
        }
        return c;
      }));
    } catch (err: any) {
      showToast("Lỗi tải tin nhắn", "error");
    } finally {
      setLoadingMsgs(false);
    }
  };

  const handleSendMessage = async (text: string, files: File[], audioBlob: File | null, replyToId?: string) => {
    if (!selectedConv) return;
    const isGroup = selectedConv.type === "group";
    const receiverId = isGroup ? selectedConv._id : selectedConv.other_user_id;
    
    let uploadedFiles: any[] = [];
    if (files.length > 0) {
      for (const file of files) {
        try {
          const res = await uploadFileAPI(file, null);
          const url = res.data?.url || res.url;
          uploadedFiles.push({ url, name: file.name, type: file.type });
        } catch (e) {
          showToast("Lỗi tải file đính kèm", "error");
        }
      }
    }
    
    let audioUrl = "";
    if (audioBlob) {
      try {
        const res = await uploadFileAPI(audioBlob, null);
        audioUrl = res.data?.url || res.url;
      } catch (e) {
        showToast("Lỗi tải file ghi âm", "error");
      }
    }

    try {
      const payload: any = { receiver_id: receiverId, is_group: isGroup, reply_to: replyToId };
      if (text.trim()) payload.content = text;
      if (audioUrl) { payload.audio_url = audioUrl; payload.content = "Tin nhắn thoại"; }
      
      const images = uploadedFiles.filter(f => f.type.startsWith("image/"));
      const docs = uploadedFiles.filter(f => !f.type.startsWith("image/"));
      if (images.length > 0) payload.image_url = images[0].url;
      if (docs.length > 0) payload.attachments = docs;

      await sendMessageAPI(payload);
    } catch (err: any) {
      showToast("Lỗi gửi tin nhắn", "error");
    }
  };

  const handleReaction = async (msgId: string, emoji: string) => {
    try {
      await reactMessageAPI(msgId, emoji);
    } catch (e) { showToast("Lỗi thả cảm xúc", "error"); }
  };

  const handleRecall = async (msgId: string) => {
    try {
      await recallMessageAPI(msgId);
      setActiveMsgMenuId(null);
    } catch (e) { showToast("Lỗi thu hồi tin nhắn", "error"); }
  };

  const handleDeleteForMe = async (msgId: string) => {
    try {
      await deleteMessageForMeAPI(msgId);
      setMessages(prev => prev.filter(m => (m._id || m.id) !== msgId));
      setActiveMsgMenuId(null);
    } catch (e) { showToast("Lỗi xoá tin nhắn", "error"); }
  };

  const handleCreatePoll = async (question: string, options: string[]) => {
    if (!selectedConv) return;
    try {
      const isGroup = selectedConv.type === "group";
      const receiverId = isGroup ? selectedConv._id : selectedConv.other_user_id;
      await createPollAPI({
        receiver_id: receiverId,
        is_group: isGroup,
        question,
        options
      });
      setShowPollModal(false);
    } catch (err) {
      showToast("Lỗi tạo bình chọn", "error");
    }
  };

  const handleVotePoll = async (msgId: string, optionId: string) => {
    try {
      await votePollAPI(msgId, optionId);
    } catch (e) { showToast("Lỗi bình chọn", "error"); }
  };

  const handleForward = async (msgId: string, targets: {id: string, isGroup: boolean}[]) => {
    try {
      for (const t of targets) {
        await forwardMessageAPI(msgId, { receiver_id: t.id, is_group: t.isGroup });
      }
      showToast("Đã chuyển tiếp tin nhắn", "success");
      setShowForwardModal(null);
      setActiveMsgMenuId(null);
    } catch (e) { showToast("Lỗi chuyển tiếp", "error"); }
  };

  if (authLoading || !user) return <PageLoader />;

  return (
    <div className="w-full h-full flex flex-col font-sans text-[#1D1D1F]" onClick={() => setActiveMsgMenuId(null)}>
      <div className="flex-1 flex overflow-hidden">
        <MessageSidebar
          user={user}
          conversations={conversations}
          selectedConv={selectedConv}
          onlineUsers={onlineUsers}
          onSelectConversation={selectConversation}
          onStartNewChat={(other) => {
            const existing = conversations.find(c => c.other_user_id === (other._id || other.id));
            if (existing) selectConversation(existing);
            else {
              setSelectedConv({ other_user_id: other._id || other.id, other_user: other });
              setMessages([]);
            }
          }}
        />

        <div className="flex-1 flex flex-col bg-white relative">
          {selectedConv ? (
            <>
              <MessageHeader
                selectedConv={selectedConv}
                onlineUsers={onlineUsers}
                onBack={() => setSelectedConv(null)}
                onOpenSettings={() => {}} // TODO
              />

              <div className="flex-1 overflow-y-auto px-4 pt-6 pb-2 relative" ref={messagesContainerRef}>
                {loadingMsgs ? (
                  <div className="flex-1 flex items-center justify-center min-h-[200px]">
                    <PageLoader />
                  </div>
                ) : messages.length === 0 ? (
                  <div className="flex-1 flex flex-col items-center justify-center text-center px-4 min-h-[300px]">
                    <div className="w-16 h-16 bg-[#F5F5F7] rounded-full flex items-center justify-center mb-4 border border-[#E8E8ED]">
                      👋
                    </div>
                    <p className="text-[15px] text-[#6E6E73] font-medium max-w-sm">
                      Hãy gửi lời chào đến {selectedConv.type === "group" ? selectedConv.group_name : selectedConv.other_user?.full_name}
                    </p>
                  </div>
                ) : (
                  messages.map((msg, index) => {
                    const isSender = msg.sender_id === user._id;
                    const prevMsg = index > 0 ? messages[index - 1] : null;
                    let showTime = false;
                    if (prevMsg) {
                      const diff = new Date(msg.created_at).getTime() - new Date(prevMsg.created_at).getTime();
                      if (diff > 10 * 60 * 1000) showTime = true;
                    } else showTime = true;

                    return (
                      <MessageBubble
                        key={msg._id || msg.id}
                        msg={msg}
                        isSender={isSender}
                        showTime={showTime}
                        conversationTheme={selectedConv.theme || "default"}
                        user={user}
                        activeMsgMenuId={activeMsgMenuId}
                        showDeleteSubMenu={showDeleteSubMenu}
                        onDoubleClick={(m, rect, isS) => {
                          if (activeMsgMenuId === m._id || activeMsgMenuId === m.id) {
                            setActiveMsgMenuId(null);
                          } else {
                            setActiveMsgMenuId(m._id || m.id);
                            setActiveMsgRect(rect);
                            setActiveMsgObj(m);
                            setShowDeleteSubMenu(null);
                          }
                        }}
                        onReaction={handleReaction}
                        onReply={(m) => { setReplyingTo(m); setActiveMsgMenuId(null); }}
                        onPin={() => {}}
                        onEdit={() => {}}
                        onToggleDeleteMenu={(id) => setShowDeleteSubMenu(id)}
                        onRecall={handleRecall}
                        onDeleteForMe={handleDeleteForMe}
                        onForward={(id) => setShowForwardModal(id)}
                        onVote={handleVotePoll}
                        onScrollToReply={(id) => {
                           // implement scroll
                        }}
                      />
                    );
                  })
                )}
                {typingUsers[selectedConv.other_user_id] && (
                  <div className="flex items-center gap-2 text-[#6E6E73] text-[13px] italic p-2 bg-[#F5F5F7] rounded-full max-w-fit mt-2 shadow-sm animate-pulse">
                    Đang soạn tin...
                  </div>
                )}
              </div>

              <MessageInput
                onSendMessage={handleSendMessage}
                replyingTo={replyingTo}
                onCancelReply={() => setReplyingTo(null)}
                onOpenPollModal={() => setShowPollModal(true)}
                onTyping={(isTyping) => sendTypingEvent(isTyping)}
              />
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 bg-[#F5F5F7]">
              <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mb-6 shadow-sm border border-[#E8E8ED]">
                💬
              </div>
              <h2 className="text-[22px] font-bold text-[#1D1D1F] mb-2 tracking-tight">DocLib Messages</h2>
              <p className="text-[15px] text-[#6E6E73] max-w-sm">Chọn một đoạn chat hoặc bắt đầu cuộc trò chuyện mới để kết nối với mọi người.</p>
            </div>
          )}
        </div>
      </div>

      {showPollModal && (
        <CreatePollModal onClose={() => setShowPollModal(false)} onCreate={handleCreatePoll} />
      )}
      
      {showForwardModal && (
        <ForwardModal 
          isOpen={true} 
          onClose={() => setShowForwardModal(null)} 
          conversations={conversations} 
          onForward={(targets) => handleForward(showForwardModal, targets)}
        />
      )}
      
      {/* Context Menu Portal placeholder - to be fully extracted later, simplified here */}
      {activeMsgMenuId && activeMsgRect && activeMsgObj && (
        <div 
          className="fixed z-50 bg-white/95 backdrop-blur-md border border-[#E8E8ED] rounded-[16px] shadow-[0_8px_32px_rgba(0,0,0,0.15)] flex flex-col p-1.5 min-w-[180px]"
          style={{
             top: activeMsgRect.top - 100 > 0 ? activeMsgRect.top - 100 : activeMsgRect.bottom + 10,
             left: activeMsgRect.isSender ? activeMsgRect.left - 180 : activeMsgRect.right + 10
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex gap-1 p-1 bg-[#F5F5F7] rounded-[10px] justify-center mb-2">
            {["❤️", "👍", "😂", "😮", "😢", "🙏"].map(emoji => (
              <button key={emoji} onClick={() => { handleReaction(activeMsgObj._id || activeMsgObj.id, emoji); setActiveMsgMenuId(null); }} className="hover:scale-125 transition-transform">{emoji}</button>
            ))}
          </div>
          <button onClick={() => { setReplyingTo(activeMsgObj); setActiveMsgMenuId(null); }} className="text-left px-3 py-2 text-[14px] hover:bg-[#F5F5F7] rounded-md">Trả lời</button>
          <button onClick={() => setShowForwardModal(activeMsgObj._id || activeMsgObj.id)} className="text-left px-3 py-2 text-[14px] hover:bg-[#F5F5F7] rounded-md">Chuyển tiếp</button>
          <div className="h-[1px] bg-[#E8E8ED] my-1" />
          <button onClick={() => setShowDeleteSubMenu(activeMsgObj._id || activeMsgObj.id)} className="text-left px-3 py-2 text-[14px] text-red-500 hover:bg-red-50 rounded-md">Xóa</button>
          
          {showDeleteSubMenu === (activeMsgObj._id || activeMsgObj.id) && (
            <div className="absolute top-0 right-full mr-2 bg-white/95 rounded-[16px] border border-[#E8E8ED] p-1.5 shadow-lg min-w-[150px]">
               {activeMsgObj.sender_id === user._id && (
                  <button onClick={() => handleRecall(activeMsgObj._id || activeMsgObj.id)} className="w-full text-left px-3 py-2 text-[14px] text-red-500 hover:bg-red-50 rounded-md">Thu hồi (cả 2 phía)</button>
               )}
               <button onClick={() => handleDeleteForMe(activeMsgObj._id || activeMsgObj.id)} className="w-full text-left px-3 py-2 text-[14px] hover:bg-[#F5F5F7] rounded-md">Xóa phía tôi</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
