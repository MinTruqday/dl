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
    pathname.startsWith("/verify-code") ||
    pathname.startsWith("/reset-password");

  const isPublicRoute =
    pathname === "/" ||
    pathname.startsWith("/feed") ||
    pathname.startsWith("/explore") ||
    pathname.startsWith("/leaderboard") ||
    pathname.startsWith("/search") ||
    pathname.startsWith("/document") ||
    pathname.startsWith("/documents") ||
    pathname.startsWith("/authors") ||
    pathname.startsWith("/preview") ||
    pathname.startsWith("/auth/google/callback");

  if (!token && !isAuthRoute && !isPublicRoute) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (role === "reader") {
    if (
      pathname.startsWith("/studio") ||
      pathname.startsWith("/moderation") ||
      pathname.startsWith("/admin")
    ) {
      return NextResponse.redirect(new URL("/", request.url));
    }
  }

  if (role === "author") {
    if (pathname.startsWith("/moderation") || pathname.startsWith("/admin")) {
      return NextResponse.redirect(new URL("/studio", request.url));
    }
  }

  if (role === "moderator") {
    if (pathname.startsWith("/studio") || pathname.startsWith("/admin")) {
      return NextResponse.redirect(new URL("/moderation", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
