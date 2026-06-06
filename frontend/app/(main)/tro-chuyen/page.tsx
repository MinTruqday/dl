import AiChat from "@/components/AiChat";

export default function TroChuyenPage() {
  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 min-h-[calc(100dvh-var(--navbar-height))] font-sans text-black selection:bg-black selection:text-white">
      <AiChat standalone={true} />
    </div>
  );
}
