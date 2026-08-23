"use client";
import React, { createContext, useContext, useState, useEffect, useCallback, } from "react";
import { getAnnouncementsAPI, markAnnouncementReadAPI, } from "@/features/notification/services/announcement.service";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "./ToastContext";
const AnnouncementContext = createContext(undefined);
export function AnnouncementProvider({ children, }) {
    const notificationEnabled = process.env.NEXT_PUBLIC_NOTIFICATION_ENABLED === "true";
    const { user } = useAuth();
    const { showToast } = useToast();
    const [announcements, setAnnouncements] = useState([]);
    const fetchAnnouncements = useCallback(async () => {
        if (!user || !notificationEnabled)
            return;
        try {
            const data = await getAnnouncementsAPI();
            let arr = data.data || data || [];
            if (!Array.isArray(arr))
                arr = [];
            setAnnouncements(arr);
        }
        catch (e) {
            console.error("Error fetching global announcements:", e);
        }
    }, [notificationEnabled, user]);
    const markAsRead = useCallback(async (id) => {
        try {
            await markAnnouncementReadAPI(id);
            setAnnouncements((prev) => prev.map((n) => (n._id === id ? Object.assign(Object.assign({}, n), { is_read: true }) : n)));
        }
        catch (e) {
            console.error("Error marking announcement as read:", e);
        }
    }, []);
    useEffect(() => {
        if (!user || !notificationEnabled) {
            setAnnouncements([]);
            return;
        }
        fetchAnnouncements();
        const interval = setInterval(() => {
            fetchAnnouncements();
        }, 30000);
        return () => {
            clearInterval(interval);
        };
    }, [notificationEnabled, user, fetchAnnouncements]);
    const unreadCount = Array.isArray(announcements)
        ? announcements.filter((n) => !n.is_read).length
        : 0;
    return (<AnnouncementContext.Provider value={{ announcements, unreadCount, fetchAnnouncements, markAsRead }}>
      {children}
    </AnnouncementContext.Provider>);
}
export function useAnnouncements() {
    const context = useContext(AnnouncementContext);
    if (!context) {
        throw new Error("useAnnouncements must be used within a AnnouncementProvider");
    }
    return context;
}
