"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

const easeOutExpo = (t: number) => t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
const easeInOutCubic = (t: number) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));

const GREETINGS = [
  "Xin chào,", "Hello,", "你好,", "Bonjour,", "Hola,",
  "こんにちは,", "안녕하세요,", "Ciao,", "Olá,", "Hallo,",
  "Merhaba,", "Привет,", "Γεια σας,", "Ahoj,", "Witaj,",
  "Zdravo,", "مرحبا,", "नमस्ते,", "Sawubona,", "Sveiki,",
  "Hei,", "Hej,", "Szia,", "Halo,", "Kamusta,",
  "سلام,", "שלום,", "Jambo,", "Kia ora,", "Bula,",
  "Aloha,", "Talofa,", "Malo e lelei,", "Salama,", "Sannu,",
  "Dumela,", "Molo,", "Dzień dobry,", "God dag,", "Hoi,",
  "Habari,", "สวัสดี,", "សួស្តី,", "ສະບາຍດີ,", "မင်္ဂလာပါ,",
  "ආයුබෝවන්,", "வணக்கம்,", "ನಮಸ್ಕಾರ,", "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ,", "કેમ છો,",
  "ሰላም,", "Tena koe,", "Mauri,", "Fakaalofa,", "Alii,",
  "Kaselehlia,", "Ran annim,", "Mogethin,", "Lenwo,", "Iokwe,",
  "Hafa adai,", "Tungjou,", "Akkam,", "Tena yistelegn,", "Բարև,",
  "გამარჯობა,", "Khosh amadid,", "Dobar dan,", "Dober dan,", "Mirëdita,",
  "Tungjatjeta,", "Buna,", "Здравейте,", "Привіт,", "Прывітанне,",
  "Сәлем,", "Салам,", "Сайн уу,", "བཀྲ་ཤིས་བདེ་ལེགས།,", "Kaixo,",
  "Dia dhuit,", "Slav,", "Mabuhay,", "Niltze,", "Allianchu,",
  "Cześć,", "Sain uu,", "Tansi,", "Aanii,", "Kwe,",
  "Halito,", "ᎣᏏᏲ,", "Hau,", "Mba'éichapa,", "Irasshaimase,",
  "Namaskar,", "Aho,", "Boozhoo,", "Wachiya,", "Yá'át'ééh,",
  "Ahéhee',", "Tlazocamati,", "Na'at'áanii,", "Saluton,"
];
const HOLD_MS = 900, FADE_MS = 280, LANG_MS = FADE_MS + HOLD_MS + FADE_MS;

export default function IntroSplash() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const router = useRouter();
  const [showBtn, setShowBtn] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;

    let startTime = -1, typedText = "", cursorVis = true, cursorTick = 0;
    let rafId: number, done = false;

    const TW: Array<{ at: number; text: string }> = [];
    const HELLO = "Xin chào, ", METIS = "Metis", EXCL = "!", DOCLIB = "DocLib";
    const HW = HELLO + "Thế giới!";
    
    let t = 400;
    for (let i = 0; i <= HW.length; i++) { TW.push({ at: t, text: HW.substring(0, i) }); t += 110; }
    t += 900;
    for (let i = HW.length; i >= HELLO.length; i--) { TW.push({ at: t, text: HW.substring(0, i) }); t += 55; }
    t += 80;
    const DF = DOCLIB + EXCL;
    for (let i = 1; i <= DF.length; i++) { TW.push({ at: t, text: HELLO + DF.substring(0, i) }); t += 110; }
    t += 1400;

    const MS = 90, MD = 450;
    const T_MORPH = t, T_MORPH_END = t + MS * 5 + MD + 200;
    const SWEEP_DUR = 1000;
    const T_SWEEP_E = T_MORPH_END + 600, T_SWEEP_W = T_SWEEP_E + SWEEP_DUR + 200;
    const T_SWEEP_DONE = T_SWEEP_W + SWEEP_DUR;
    const T_LANG_START = T_SWEEP_DONE;

    const FROM = ["D", "o", "c", "L", "i", "b"];
    const TO = ["M", "e", "t", "i", "s", ""];
    const metisChars = METIS.split("");
    const SLOTS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

    const layout = {
      W: 0, H: 0, cx: 0, cy: 0, FS: 0, FONT: "",
      helloW: 0, metisW: 0, doclibW: 0, exclW: 0,
      startXD: 0, startXM: 0, wordXD: 0, wordXM: 0,
      exclXD: 0, exclXM: 0,
      fromW: [] as number[],
      fromCharX: [] as number[],
      metisCharW: [] as number[],
      metisCharX: [] as number[]
    };

    const updateLayout = () => {
      const dpr = window.devicePixelRatio || 1;
      layout.W = window.innerWidth;
      layout.H = window.innerHeight;
      
      canvas.width = layout.W * dpr;
      canvas.height = layout.H * dpr;
      canvas.style.width = `${layout.W}px`;
      canvas.style.height = `${layout.H}px`;
      ctx.scale(dpr, dpr);

      layout.cx = layout.W / 2;
      layout.cy = layout.H * 0.46;

      layout.FS = Math.min(layout.W * 0.08, 72);
      layout.FONT = `bold ${layout.FS}px -apple-system,"SF Pro Display","Noto Sans",BlinkMacSystemFont,sans-serif`;
      ctx.font = layout.FONT;

      layout.helloW = ctx.measureText(HELLO).width;
      layout.metisW = ctx.measureText(METIS).width;
      layout.doclibW = ctx.measureText(DOCLIB).width;
      layout.exclW = ctx.measureText(EXCL).width;

      layout.startXD = layout.cx - (layout.helloW + layout.doclibW + layout.exclW) / 2;
      layout.wordXD = layout.startXD + layout.helloW;
      layout.exclXD = layout.wordXD + layout.doclibW + 4;
      
      layout.startXM = layout.cx - (layout.helloW + layout.metisW + layout.exclW) / 2;
      layout.wordXM = layout.startXM + layout.helloW;
      layout.exclXM = layout.wordXM + layout.metisW + 4;

      layout.fromW = FROM.map(ch => ch ? ctx.measureText(ch).width : 0);
      layout.fromCharX = [];
      let ax = layout.wordXD;
      for (let i = 0; i < FROM.length; i++) { 
        layout.fromCharX.push(ax); 
        ax += layout.fromW[i]; 
      }

      layout.metisCharW = metisChars.map(ch => ctx.measureText(ch).width);
      layout.metisCharX = [];
      let bx = layout.wordXM;
      for (const ch of metisChars) { 
        layout.metisCharX.push(bx); 
        bx += ctx.measureText(ch).width; 
      }
    };

    window.addEventListener("resize", updateLayout);
    updateLayout();

    const draw = (ts: number) => {
      if (startTime < 0) startTime = ts;
      const now = ts - startTime;

      ctx.clearRect(0, 0, layout.W, layout.H);
      ctx.font = layout.FONT; 
      ctx.textBaseline = "middle";

      if (now < T_MORPH) {
        for (const s of TW) { if (now >= s.at) typedText = s.text; }
        cursorTick += 16; if (cursorTick > 530) { cursorVis = !cursorVis; cursorTick = 0; }
        const tw = ctx.measureText(typedText).width;
        const tx = layout.cx - tw / 2;
        ctx.fillStyle = "#1D1D1F"; ctx.globalAlpha = 1;
        ctx.fillText(typedText, tx, layout.cy);
        if (now < T_MORPH - 300 && cursorVis) {
          ctx.fillRect(tx + tw + 3, layout.cy - layout.FS * 0.38, 3, layout.FS * 0.74);
        }
        rafId = requestAnimationFrame(draw); 
        return;
      }

      if (now < T_MORPH_END) {
        const mp = Math.min(1, (now - T_MORPH) / (T_MORPH_END - T_MORPH));
        const mep = easeOutExpo(mp);
        ctx.fillStyle = "#1D1D1F"; ctx.globalAlpha = 1;
        ctx.fillText(HELLO, layout.startXD + (layout.startXM - layout.startXD) * mep, layout.cy);
        
        for (let i = 0; i < FROM.length; i++) {
          const ls = T_MORPH + i * MS;
          const fc = FROM[i], tc = TO[i];
          if (now < ls) { 
            if (fc) { 
              ctx.fillStyle = "#1D1D1F"; ctx.globalAlpha = 1; 
              ctx.fillText(fc, layout.fromCharX[i], layout.cy); 
            } 
          } else {
            const p = Math.min(1, (now - ls) / MD);
            const ep = easeOutExpo(p);
            if (tc === "") {
              ctx.globalAlpha = 1 - ep; ctx.fillStyle = "#1D1D1F";
              ctx.save(); 
              ctx.translate(layout.fromCharX[i] + layout.fromW[i] / 2, layout.cy);
              ctx.scale(1 - ep * 0.9, 1 - ep * 0.9); 
              ctx.fillText(fc, -layout.fromW[i] / 2, 0); 
              ctx.restore();
            } else {
              const dc = p < 0.75 ? SLOTS[Math.floor(Math.random() * SLOTS.length)] : tc;
              ctx.globalAlpha = 1; ctx.fillStyle = "#1D1D1F";
              ctx.fillText(dc, layout.fromCharX[i] + (layout.metisCharX[i < 5 ? i : 4] - layout.fromCharX[i]) * ep, layout.cy);
            }
          }
        }
        ctx.globalAlpha = 1; ctx.fillStyle = "#1D1D1F";
        ctx.fillText(EXCL, layout.exclXD + (layout.exclXM - layout.exclXD) * easeOutExpo(Math.min(1, (now - T_MORPH) / (T_MORPH_END - T_MORPH))), layout.cy);
        
        rafId = requestAnimationFrame(draw); 
        return;
      }

      const sweepE = now >= T_SWEEP_E && now < T_SWEEP_W;
      const sweepW = now >= T_SWEEP_W && now < T_SWEEP_DONE;
      const afterSweep = now >= T_SWEEP_DONE;
      
      let exX = layout.exclXM;
      if (sweepE) exX = layout.exclXM + (layout.wordXM - layout.exclXM) * easeInOutCubic(clamp((now - T_SWEEP_E) / SWEEP_DUR, 0, 1));
      else if (sweepW) exX = layout.wordXM + (layout.exclXM - layout.wordXM) * easeInOutCubic(clamp((now - T_SWEEP_W) / SWEEP_DUR, 0, 1));

      const sinColor = (i: number) => {
        const tt = now * 0.0006 + i * 0.4;
        const h = 210 + (Math.sin(tt) * 0.5 + 0.5) * 130;
        return `hsl(${h},75%,60%)`;
      };

      if (now >= T_LANG_START) {
        const elapsed = now - T_LANG_START;
        const adj = elapsed + FADE_MS;
        const li = Math.floor(adj / LANG_MS) % GREETINGS.length;
        const g = GREETINGS[li];
        const ln = adj % LANG_MS;
        
        let a = 1;
        if (ln < FADE_MS) a = easeOutExpo(ln / FADE_MS);
        else if (ln > FADE_MS + HOLD_MS) a = 1 - easeOutExpo((ln - FADE_MS - HOLD_MS) / FADE_MS);

        const gW = ctx.measureText(g + " ").width;
        const fullW = gW + layout.metisW + layout.exclW;
        const gX = layout.cx - fullW / 2;

        ctx.globalAlpha = a; ctx.fillStyle = "#1D1D1F";
        ctx.fillText(g + " ", gX, layout.cy);
        
        const mxLang = gX + gW;
        for (let i = 0; i < metisChars.length; i++) {
          let lx = mxLang; 
          for (let j = 0; j < i; j++) lx += layout.metisCharW[j];
          ctx.fillStyle = sinColor(i);
          ctx.fillText(metisChars[i], lx, layout.cy);
        }
        ctx.fillStyle = "#1D1D1F"; 
        ctx.fillText(EXCL, mxLang + layout.metisW + 4, layout.cy);
        ctx.globalAlpha = 1;

        if (!done) { 
          done = true; 
          setTimeout(() => setShowBtn(true), 2500); 
        }

        rafId = requestAnimationFrame(draw); 
        return;
      }

      for (let i = 0; i < metisChars.length; i++) {
        const lx = layout.metisCharX[i], cw = layout.metisCharW[i];
        let a = 1, color = "#1D1D1F";
        if (sweepE) a = clamp((exX - lx) / cw, 0, 1);
        else if (sweepW || afterSweep) {
          if (sweepW) a = clamp((exX - lx) / cw, 0, 1);
          color = sinColor(i);
        }
        ctx.globalAlpha = a; ctx.fillStyle = color;
        ctx.fillText(metisChars[i], lx, layout.cy);
      }
      
      ctx.globalAlpha = 1; ctx.fillStyle = "#1D1D1F";
      ctx.fillText(HELLO, layout.startXM, layout.cy);
      ctx.fillText(EXCL, exX, layout.cy);

      rafId = requestAnimationFrame(draw);
    };

    rafId = requestAnimationFrame(draw);
    return () => {
      window.removeEventListener("resize", updateLayout);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <div className="fixed inset-0 bg-white overflow-hidden">
      <canvas ref={canvasRef} className="absolute inset-0 block w-full h-full" />

      <div className="absolute inset-x-0 bottom-0 top-1/2 flex items-center justify-center pointer-events-none">
        <button
          onClick={() => router.push("/kham-pha")}
          style={{
            opacity: showBtn ? 1 : 0,
            transform: showBtn ? "scale(1) translateY(0)" : "scale(0.8) translateY(8px)",
            transition: "opacity 500ms ease, transform 500ms cubic-bezier(0.34,1.56,0.64,1)",
          }}
          className={`
            pointer-events-auto bg-[#0071E3] hover:bg-[#0055C6] hover:scale-105 text-white 
            border-none rounded-[980px] px-8 py-3 text-[15px] font-semibold 
            font-['-apple-system','SF_Pro_Display',BlinkMacSystemFont,sans-serif] 
            cursor-pointer tracking-tight whitespace-nowrap shadow-md
            transition-all duration-300
          `}
        >
          Bắt đầu
        </button>
      </div>
    </div>
  );
}
