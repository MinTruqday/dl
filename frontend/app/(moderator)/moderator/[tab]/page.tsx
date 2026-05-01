"use client";

import ModerationDashboard from "@/app/components/ModerationDashboard";
import { useParams } from "next/navigation";

export default function ModeratorTabPage() {
    const params = useParams();
    const tab = params.tab as any;
    
    return <ModerationDashboard initialTab={tab} />;
}
