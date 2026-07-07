import { useEffect, useRef } from "react";

export const PayOSEmbedded = ({
  checkoutUrl,
  onSuccess,
  onCancel,
  onExit,
}: {
  checkoutUrl: string;
  onSuccess?: (event: any) => void;
  onCancel?: (event: any) => void;
  onExit?: (event: any) => void;
}) => {
  const initialized = useRef(false);
  const { open, exit } = usePayOS({
    RETURN_URL: window.location.origin + "/vi-tien",
    ELEMENT_ID: "payos-checkout-container",
    CHECKOUT_URL: checkoutUrl,
    embedded: true,
    onSuccess: (event: any) => onSuccess?.(event),
    onCancel: (event: any) => onCancel?.(event),
    onExit: (event: any) => onExit?.(event),
  } as any);

  useEffect(() => {
    if (!initialized.current) {
      initialized.current = true;
      open();
    }
    // We intentionally don't call exit on unmount to avoid StrictMode double-fire bugs
  }, [open]);

  return (
    <div
      id="payos-checkout-container"
      className="w-full min-h-[450px] border border-[#D2D2D7] rounded-[18px] overflow-hidden bg-white"
    ></div>
  );
};
