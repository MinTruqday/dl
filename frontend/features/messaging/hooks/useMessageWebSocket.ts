import { useEffect, useRef } from "react";
import { WS_URL } from "@/core/config";
import { getToken } from "@/shared/lib/token";

interface UseChatWebSocketProps {
  user: any;
  conversationsRef: React.MutableRefObject<any[]>;
  selectedConvRef: React.MutableRefObject<any>;
  setMessages: React.Dispatch<React.SetStateAction<any[]>>;
  updateConversationInPlace: (senderId: string, messageData: any) => void;
  setOnlineUsers: React.Dispatch<React.SetStateAction<{[key: string]: boolean}>>;
  setTypingUsers: React.Dispatch<React.SetStateAction<{[key: string]: boolean}>>;
}

export function useMessageWebSocket({
  user,
  conversationsRef,
  selectedConvRef,
  setMessages,
  updateConversationInPlace,
  setOnlineUsers,
  setTypingUsers
}: UseChatWebSocketProps) {
  const socketRef = useRef<WebSocket | null>(null);
  const typingTimeoutRef = useRef<any>(null);

  useEffect(() => {
    if (!user?._id) return;
    const wsUrl = `${WS_URL}/ws/${user._id}?token=${getToken()}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;
    
    socket.onopen = () => {
      const lastMsgId = localStorage.getItem(`last_msg_id_${user._id}`);
      if (lastMsgId) {
        socket.send(JSON.stringify({ action: "sync", data: { last_message_id: lastMsgId } }));
      }
    };

    const pingInterval = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ action: "ping" }));
        const userIds = conversationsRef.current.map((c: any) => c.other_user_id);
        if (userIds.length > 0) {
          socket.send(JSON.stringify({ action: "check_online", data: { user_ids: userIds } }));
        }
      }
    }, 30000);

    socket.onmessage = (event) => {
      try {
        const { type, data } = JSON.parse(event.data);
        if (type === "new_message") {
          if (selectedConvRef.current && data.sender_id === selectedConvRef.current.other_user_id) {
            setMessages((prev) => {
              if (prev.some((m) => (m._id || m.id) === (data._id || data.id))) return prev;
              return [...prev, data];
            });
            if (socketRef.current?.readyState === WebSocket.OPEN) {
              socketRef.current.send(JSON.stringify({
                action: "mark_read",
                data: { other_user_id: selectedConvRef.current.other_user_id },
              }));
            }
          }
          updateConversationInPlace(data.sender_id, data);
          localStorage.setItem(`last_msg_id_${user._id}`, data._id || data.id);
        } else if (type === "message_sent_ack") {
          setMessages((prev) => {
            if (prev.some((m) => (m._id || m.id) === (data._id || data.id))) return prev;
            return [...prev, data];
          });
          updateConversationInPlace(data.receiver_id, data);
          localStorage.setItem(`last_msg_id_${user._id}`, data._id || data.id);
        } else if (type === "message_edited" || type === "message_pinned" || type === "message_recalled" || type === "message_reaction") {
          setMessages((prev) => prev.map((m) => (m._id || m.id) === (data._id || data.id) ? data : m));
        } else if (type === "user_online") {
          setOnlineUsers((prev) => ({ ...prev, [data.user_id]: true }));
        } else if (type === "user_offline") {
          setOnlineUsers((prev) => ({ ...prev, [data.user_id]: false }));
        } else if (type === "online_status_result") {
          setOnlineUsers(data);
        } else if (type === "typing_start") {
          setTypingUsers((prev) => ({ ...prev, [data.sender_id]: true }));
          if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
          typingTimeoutRef.current = setTimeout(() => {
            setTypingUsers((prev) => ({ ...prev, [data.sender_id]: false }));
          }, 3000);
        } else if (type === "typing_end") {
          setTypingUsers((prev) => ({ ...prev, [data.sender_id]: false }));
        } else if (type === "messages_read") {
          if (selectedConvRef.current && data.reader_id === selectedConvRef.current.other_user_id) {
             setMessages((prev) => prev.map((m) => {
                if (m.sender_id === user._id && !m.is_read && new Date(m.created_at) <= new Date(data.read_at)) {
                    return { ...m, is_read: true };
                }
                return m;
             }));
          }
        }
      } catch (err) {
        console.error("Lỗi parse WS message", err);
      }
    };

    socket.onerror = (err) => console.error("WS Error", err);
    socket.onclose = () => console.log("WS Closed");

    return () => {
      clearInterval(pingInterval);
      if (socket.readyState === WebSocket.OPEN) socket.close();
    };
  }, [user?._id, conversationsRef, selectedConvRef, setMessages, updateConversationInPlace, setOnlineUsers, setTypingUsers]);

  const sendTypingEvent = (isTyping: boolean) => {
    if (socketRef.current?.readyState === WebSocket.OPEN && selectedConvRef.current) {
        socketRef.current.send(JSON.stringify({
            action: isTyping ? "typing_start" : "typing_end",
            data: { receiver_id: selectedConvRef.current.other_user_id }
        }));
    }
  };

  const markAsRead = (otherUserId: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
            action: "mark_read",
            data: { other_user_id: otherUserId }
        }));
    }
  };

  return { socketRef, sendTypingEvent, markAsRead };
}
