"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

const easeOutExpo = (t: number) => t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
const easeInOutCubic = (t: number) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));

const GREETINGS = [
  "Xin chào,", "Hello,", "Bonjour,", "你好,", "Hola,",
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
  const router    = useRouter();
  const [showBtn, setShowBtn] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current!;
    const ctx    = canvas.getContext("2d")!;
    const dpr    = window.devicePixelRatio || 1;

    canvas.width        = window.innerWidth  * dpr;
    canvas.height       = window.innerHeight * dpr;
    canvas.style.width  = `${window.innerWidth}px`;
    canvas.style.height = `${window.innerHeight}px`;
    ctx.scale(dpr, dpr);

    const W = window.innerWidth, H = window.innerHeight;
    const cy = H / 2, cx = W / 2;
    const FS   = Math.min(W * 0.08, 72);
    const FONT = `bold ${FS}px -apple-system,"SF Pro Display","Noto Sans",BlinkMacSystemFont,sans-serif`;

    ctx.font = FONT;
    const HELLO = "Xin chào, ", METIS = "Metis", EXCL = "!", DOCLIB = "DocLib";
    const helloW  = ctx.measureText(HELLO).width;
    const metisW  = ctx.measureText(METIS).width;
    const doclibW = ctx.measureText(DOCLIB).width;
    const exclW   = ctx.measureText(EXCL).width;

    const FROM  = ["D","o","c","L","i","b"];
    const TO    = ["M","e","t","i","s",""];
    const fromW = FROM.map(ch => ch ? ctx.measureText(ch).width : 0);

    const startXD = cx - (helloW+doclibW+exclW)/2;
    const wordXD  = startXD + helloW;
    const exclXD  = wordXD + doclibW + 4;
    const startXM = cx - (helloW+metisW+exclW)/2;
    const wordXM  = startXM + helloW;
    const exclXM  = wordXM + metisW + 4;

    const fromCharX: number[] = [];
    let ax = wordXD;
    for (let i = 0; i < FROM.length; i++) { fromCharX.push(ax); ax += fromW[i]; }

    const metisChars = METIS.split("");
    const metisCharW = metisChars.map(ch => ctx.measureText(ch).width);
    const metisCharX: number[] = [];
    let bx = wordXM;
    for (const ch of metisChars) { metisCharX.push(bx); bx += ctx.measureText(ch).width; }

    const TW: Array<{at:number;text:string}> = [];
    let t = 400;
    const HW = HELLO + "Thế giới!";
    for (let i=0;i<=HW.length;i++) { TW.push({at:t,text:HW.substring(0,i)}); t+=110; }
    t += 900;
    for (let i=HW.length;i>=HELLO.length;i--) { TW.push({at:t,text:HW.substring(0,i)}); t+=55; }
    t += 80;
    const DF = DOCLIB+EXCL;
    for (let i=1;i<=DF.length;i++) { TW.push({at:t,text:HELLO+DF.substring(0,i)}); t+=110; }
    t += 1400;

    const MS=90, MD=450;
    const T_MORPH=t, T_MORPH_END=t+MS*5+MD+200;
    const SWEEP_DUR=1000;
    const T_SWEEP_E=T_MORPH_END+1600, T_SWEEP_W=T_SWEEP_E+SWEEP_DUR+200;
    const T_SWEEP_DONE=T_SWEEP_W+SWEEP_DUR;
    const T_LANG_START=T_SWEEP_DONE;

    const SLOTS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    let startTime=-1, typedText="", cursorVis=true, cursorTick=0;
    let rafId:number, done=false;

    const draw = (ts: number) => {
      if (startTime<0) startTime=ts;
      const now = ts-startTime;

      ctx.clearRect(0,0,W,H);
      ctx.font=FONT; ctx.textBaseline="middle";

      if (now<T_MORPH) {
        for (const s of TW) { if(now>=s.at) typedText=s.text; }
        cursorTick+=16; if(cursorTick>530){cursorVis=!cursorVis;cursorTick=0;}
        const tw=ctx.measureText(typedText).width, tx=cx-tw/2;
        ctx.fillStyle="#1D1D1F"; ctx.globalAlpha=1;
        ctx.fillText(typedText,tx,cy);
        if(now<T_MORPH-300&&cursorVis) ctx.fillRect(tx+tw+3,cy-FS*0.38,3,FS*0.74);
        rafId=requestAnimationFrame(draw); return;
      }

      if (now<T_MORPH_END) {
        const mp=Math.min(1,(now-T_MORPH)/(T_MORPH_END-T_MORPH)), mep=easeOutExpo(mp);
        ctx.fillStyle="#1D1D1F"; ctx.globalAlpha=1;
        ctx.fillText(HELLO, startXD+(startXM-startXD)*mep, cy);
        for (let i=0;i<FROM.length;i++) {
          const ls=T_MORPH+i*MS, fc=FROM[i], tc=TO[i];
          if(now<ls){if(fc){ctx.fillStyle="#1D1D1F";ctx.globalAlpha=1;ctx.fillText(fc,fromCharX[i],cy);}}
          else {
            const p=Math.min(1,(now-ls)/MD), ep=easeOutExpo(p);
            if(tc===""){
              ctx.globalAlpha=1-ep; ctx.fillStyle="#1D1D1F";
              ctx.save(); ctx.translate(fromCharX[i]+fromW[i]/2,cy);
              ctx.scale(1-ep*0.9,1-ep*0.9); ctx.fillText(fc,-fromW[i]/2,0); ctx.restore();
            } else {
              const dc=p<0.75?SLOTS[Math.floor(Math.random()*SLOTS.length)]:tc;
              ctx.globalAlpha=1; ctx.fillStyle="#1D1D1F";
              ctx.fillText(dc, fromCharX[i]+(metisCharX[i<5?i:4]-fromCharX[i])*ep, cy);
            }
          }
        }
        ctx.globalAlpha=1; ctx.fillStyle="#1D1D1F";
        ctx.fillText(EXCL, exclXD+(exclXM-exclXD)*easeOutExpo(Math.min(1,(now-T_MORPH)/(T_MORPH_END-T_MORPH))), cy);
        rafId=requestAnimationFrame(draw); return;
      }

      const sweepE=now>=T_SWEEP_E&&now<T_SWEEP_W;
      const sweepW=now>=T_SWEEP_W&&now<T_SWEEP_DONE;
      const afterSweep=now>=T_SWEEP_DONE;
      let exX=exclXM;
      if(sweepE) exX=exclXM+(wordXM-exclXM)*easeInOutCubic(clamp((now-T_SWEEP_E)/SWEEP_DUR,0,1));
      else if(sweepW) exX=wordXM+(exclXM-wordXM)*easeInOutCubic(clamp((now-T_SWEEP_W)/SWEEP_DUR,0,1));

      const sinColor = (i: number) => {
        const tt = now * 0.0006 + i * 0.4;
        const h = 210 + (Math.sin(tt) * 0.5 + 0.5) * 130;
        return `hsl(${h},75%,60%)`;
      };

      if (now >= T_LANG_START) {
        const elapsed = now - T_LANG_START;
        const adj = elapsed + FADE_MS;
        const li  = Math.floor(adj / LANG_MS) % GREETINGS.length;
        const g   = GREETINGS[li];
        const ln  = adj % LANG_MS;
        let a = 1;
        if (ln < FADE_MS) a = easeOutExpo(ln / FADE_MS);
        else if (ln > FADE_MS + HOLD_MS) a = 1 - easeOutExpo((ln - FADE_MS - HOLD_MS) / FADE_MS);

        const gW    = ctx.measureText(g + " ").width;
        const fullW = gW + metisW + exclW;
        const gX    = cx - fullW / 2;

        ctx.globalAlpha = a; ctx.fillStyle = "#1D1D1F";
        ctx.fillText(g + " ", gX, cy);
        const mxLang = gX + gW;
        for (let i = 0; i < metisChars.length; i++) {
          let lx = mxLang; for (let j = 0; j < i; j++) lx += metisCharW[j];
          ctx.fillStyle = sinColor(i);
          ctx.fillText(metisChars[i], lx, cy);
        }
        ctx.fillStyle = "#1D1D1F"; ctx.fillText(EXCL, mxLang + metisW + 4, cy);
        ctx.globalAlpha = 1;

        if (!done) { done = true; setTimeout(() => setShowBtn(true), 600); }

        rafId = requestAnimationFrame(draw); return;
      }

      for (let i=0;i<metisChars.length;i++) {
        const lx=metisCharX[i], cw=metisCharW[i];
        let a=1, color="#1D1D1F";
        if(sweepE) a=clamp((exX-lx)/cw,0,1);
        else if(sweepW||afterSweep) {
          if(sweepW) a=clamp((exX-lx)/cw,0,1);
          color=sinColor(i);
        }
        ctx.globalAlpha=a; ctx.fillStyle=color;
        ctx.fillText(metisChars[i],lx,cy);
      }
      ctx.globalAlpha=1; ctx.fillStyle="#1D1D1F";
      ctx.fillText(HELLO,startXM,cy);
      ctx.fillText(EXCL,exX,cy);

      rafId=requestAnimationFrame(draw);
    };

    rafId=requestAnimationFrame(draw);
    return () => cancelAnimationFrame(rafId);
  }, []);

  return (
    <div style={{ position:"fixed", inset:0, background:"#fff", overflow:"hidden" }}>
      <canvas ref={canvasRef} style={{ display:"block" }} />

      <div style={{
        position:"absolute", inset:0,
        display:"flex", flexDirection:"column",
        alignItems:"center", justifyContent:"center",
        pointerEvents: showBtn ? "auto" : "none",
      }}>
        <div style={{ height:"220px" }} />

        <button
          onClick={() => router.push("/kham-pha")}
          style={{
            opacity: showBtn ? 1 : 0,
            transform: showBtn ? "scale(1) translateY(0)" : "scale(0.8) translateY(8px)",
            transition: "opacity 500ms ease, transform 500ms cubic-bezier(0.34,1.56,0.64,1)",
            background:"#0071E3",
            color:"#fff",
            border:"none",
            borderRadius:"980px",
            padding:"10px 28px",
            fontSize:"15px",
            fontWeight:600,
            fontFamily:"-apple-system,'SF Pro Display',BlinkMacSystemFont,sans-serif",
            cursor:"pointer",
            letterSpacing:"-0.01em",
            whiteSpace:"nowrap",
          }}
          onMouseEnter={e => { const el=e.currentTarget; el.style.background="#0055C6"; el.style.transform="scale(1.04)"; }}
          onMouseLeave={e => { const el=e.currentTarget; el.style.background="#0071E3"; el.style.transform="scale(1)"; }}
        >
          Bắt đầu
        </button>
      </div>
    </div>
  );
}
