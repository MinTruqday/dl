"use client";

import Moderation from "@/components/Moderation";
import { useParams } from "next/navigation";

export default function ModeratorTabPage() {
    const params = useParams();
    const tab = params.tab as any;
    
    return <Moderation initialTab={tab} />;
}
