"use client";

import * as React from "react";
import { Theme as NextThemesProvider } from "next-themes";
import { type ThemeProviderProps } from "next-themes";

export function Theme({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
