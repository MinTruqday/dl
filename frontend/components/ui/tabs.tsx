"use client";
import React, { createContext, useContext, useState } from "react";
import { cn } from "@/lib/utils";

const TabsContext = createContext<{
  val: string;
  setVal: React.Dispatch<React.SetStateAction<string>>;
} | null>(null);

export const Tabs = ({
  defaultValue,
  className,
  children,
}: {
  defaultValue: string;
  className?: string;
  children: React.ReactNode;
}) => {
  const [val, setVal] = useState(defaultValue);
  return (
    <TabsContext.Provider value={{ val, setVal }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
};

export const TabsList = ({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) => {
  return <div className={cn("flex items-center", className)}>{children}</div>;
};

export const TabsTrigger = ({
  value,
  className,
  children,
}: {
  value: string;
  className?: string;
  children: React.ReactNode;
}) => {
  const ctx = useContext(TabsContext);
  const isActive = ctx?.val === value;
  return (
    <button
      type="button"
      data-state={isActive ? "active" : "inactive"}
      onClick={() => ctx?.setVal(value)}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap px-8 py-3 text-xs font-bold focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-black data-[state=active]:text-white data-[state=inactive]:bg-white data-[state=inactive]:text-zinc-400 data-[state=inactive]: border-b-2 data-[state=active]:border-black data-[state=inactive]:border-transparent",
        className,
      )}
    >
      {children}
    </button>
  );
};

export const TabsContent = ({
  value,
  className,
  children,
}: {
  value: string;
  className?: string;
  children: React.ReactNode;
}) => {
  const ctx = useContext(TabsContext);
  if (ctx?.val !== value) return null;
  return <div className={className}>{children}</div>;
};
