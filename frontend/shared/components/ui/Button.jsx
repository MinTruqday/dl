"use client";
var __rest = (this && this.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
};
import React from "react";
export function Button(_a) {
    var { variant = "primary", size = "md", className = "", children, icon } = _a, props = __rest(_a, ["variant", "size", "className", "children", "icon"]);
    const vClass = {
        primary: "border-brand bg-brand text-white hover:border-brand-hover hover:bg-brand-hover",
        secondary: "border-border-strong bg-surface text-ink hover:bg-surface-quiet",
        outline: "border-border-strong bg-transparent text-ink hover:bg-surface-quiet",
        ghost: "border-transparent bg-transparent text-ink hover:bg-surface-quiet",
        danger: "border-danger bg-danger text-white hover:bg-danger/90",
    };
    const sClass = {
        sm: "min-h-9 px-3 py-1.5 text-[13px] border",
        md: "min-h-11 px-4 py-2.5 text-[14px] border",
        lg: "min-h-12 px-5 py-3 text-[15px] border",
        icon: "h-11 w-11 border p-2",
    };
    return (<button className={`inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-control font-semibold transition duration-150 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50 ${vClass[variant]} ${sClass[size]} ${className}`} {...props}>
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </button>);
}
