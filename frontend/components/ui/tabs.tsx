"use client";
import React, { createContext, useContext, useState } from "react";
import { cn } from "@/app/lib/utils";

const TabsContext = createContext<{
  val: string;
  setVal: React.Dispatch<React.SetStateAction<string>>;
} | null>(null);

export const Tabs = ({ defaultValue, className, children }: { defaultValue: string; className?: string; children: React.ReactNode }) => {
  const [val, setVal] = useState(defaultValue);
  return <TabsContext.Provider value={{ val, setVal }}><div className={className}>{children}</div></TabsContext.Provider>;
};

export const TabsList = ({ className, children }: { className?: string; children: React.ReactNode }) => {
  return <div className={cn("flex items-center", className)}>{children}</div>;
};

export const TabsTrigger = ({ value, className, children }: { value: string; className?: string; children: React.ReactNode }) => {
  const ctx = useContext(TabsContext);
  const isActive = ctx?.val === value;
  return (
    <button
      type="button"
      data-state={isActive ? "active" : "inactive"}
      onClick={() => ctx?.setVal(value)}
      className={cn("inline-flex items-center justify-center whitespace-nowrap px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow", className)}
    >
      {children}
    </button>
  );
};

export const TabsContent = ({ value, className, children }: { value: string; className?: string; children: React.ReactNode }) => {
  const ctx = useContext(TabsContext);
  if (ctx?.val !== value) return null;
  return <div className={className}>{children}</div>;
};
