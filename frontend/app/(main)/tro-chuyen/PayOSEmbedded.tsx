"use client";

import { useEffect, useRef } from "react";
import { usePayOS } from "@payos/payos-checkout";

export default function PayOSEmbedded({ checkoutUrl }: { checkoutUrl: string }) {
  const elementId = useRef("payos-" + Math.random().toString(36).substring(7));
  const { open, exit } = usePayOS({
    RETURN_URL: window.location.origin + "/vi-tien",
    ELEMENT_ID: elementId.current,
    CHECKOUT_URL: checkoutUrl,
    embedded: true,
  } as any);

  useEffect(() => {
    open();
    return () => {
      if (exit) exit();
    };
  }, [open, exit]);

  return (
    <div
      id={elementId.current}
      className="w-full min-h-[450px] border border-[#E8E8ED] rounded-[18px] my-4 bg-white overflow-hidden shadow-sm"
    ></div>
  );
}
