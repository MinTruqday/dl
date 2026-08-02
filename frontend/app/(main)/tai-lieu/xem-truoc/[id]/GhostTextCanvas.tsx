"use client";

import { useLayoutEffect, useRef } from "react";

export default function GhostTextCanvas({ content }: { content: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useLayoutEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const render = () => {
      const width = Math.max(280, canvas.parentElement?.clientWidth || 720);
      const ratio = Math.min(2, window.devicePixelRatio || 1);
      const context = canvas.getContext("2d");
      if (!context) return;
      const fontSize = 16;
      const lineHeight = 32;
      const padding = 4;
      const maxWidth = width - padding * 2;
      context.font = `${fontSize}px ui-sans-serif, system-ui, sans-serif`;
      const lines: string[] = [];
      for (const paragraph of String(content || "").split("\n")) {
        const words = paragraph.split(/\s+/).filter(Boolean);
        if (!words.length) {
          lines.push("");
          continue;
        }
        let line = words[0];
        for (const word of words.slice(1)) {
          const candidate = `${line} ${word}`;
          if (context.measureText(candidate).width <= maxWidth) line = candidate;
          else {
            lines.push(line);
            line = word;
          }
        }
        lines.push(line);
      }
      const height = Math.max(lineHeight, lines.length * lineHeight + padding * 2);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      canvas.width = Math.floor(width * ratio);
      canvas.height = Math.floor(height * ratio);
      context.scale(ratio, ratio);
      context.clearRect(0, 0, width, height);
      const ink = getComputedStyle(document.documentElement)
        .getPropertyValue("--ink")
        .trim();
      context.fillStyle = ink ? `hsl(${ink})` : "#111827";
      context.font = `${fontSize}px ui-sans-serif, system-ui, sans-serif`;
      context.textBaseline = "top";
      lines.forEach((line, index) => {
        context.fillText(line, padding, padding + index * lineHeight, maxWidth);
      });
    };
    render();
    const observer = new ResizeObserver(render);
    if (canvas.parentElement) observer.observe(canvas.parentElement);
    return () => observer.disconnect();
  }, [content]);

  return (
    <canvas
      ref={canvasRef}
      role="img"
      aria-label="Nội dung được bảo vệ"
      className="block max-w-full select-none"
      onContextMenu={(event) => event.preventDefault()}
    />
  );
}
