import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("token")?.value;
  const role = request.cookies.get("role")?.value || "reader";
  const { pathname } = request.nextUrl;

  const isAuthRoute =
    pathname.startsWith("/login") ||
    pathname.startsWith("/register") ||
    pathname.startsWith("/forgot-password") ||
    pathname.startsWith("/verify") ||
    pathname.startsWith("/reset-password");

  const isPublicRoute =
    pathname === "/" ||
    pathname.startsWith("/discovery") ||

    pathname.startsWith("/search") ||
    pathname.startsWith("/document") ||
    pathname.startsWith("/tac-gia") ||
    pathname.startsWith("/xem-truoc") ||
    pathname.startsWith("/auth/google/callback");

  if (!token && !isAuthRoute && !isPublicRoute) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (role === "reader") {
    if (
      pathname.startsWith("/compose") ||
      pathname.startsWith("/operation") ||
      pathname.startsWith("/tac-gia-tiem-nang") ||
      pathname.startsWith("/admin")
    ) {
      return NextResponse.redirect(new URL("/", request.url));
    }
  }

  if (role === "author") {
    if (
      pathname.startsWith("/operation") || 
      pathname.startsWith("/tac-gia-tiem-nang") ||
      pathname.startsWith("/admin")
    ) {
      return NextResponse.redirect(new URL("/compose", request.url));
    }
  }

  if (role === "moderator") {
    if (pathname.startsWith("/compose") || pathname.startsWith("/admin")) {
      return NextResponse.redirect(new URL("/operation", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
