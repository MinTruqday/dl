import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("token")?.value;
  const role = request.cookies.get("role")?.value || "reader";
  const { pathname } = request.nextUrl;

  const isAuthRoute =
    pathname.startsWith("/dang-nhap") ||
    pathname.startsWith("/dang-ky") ||
    pathname.startsWith("/quen-mat-khau") ||
    pathname.startsWith("/xac-thuc") ||
    pathname.startsWith("/dat-lai-mat-khau");

  const isPublicRoute =
    pathname === "/" ||
    pathname.startsWith("/kham-pha") ||
    pathname.startsWith("/discovery") ||
    pathname.startsWith("/search") ||
    pathname.startsWith("/document") ||
    pathname.startsWith("/tac-gia") ||
    pathname.startsWith("/xem-truoc") ||
    pathname.startsWith("/auth/google/callback");

  if (!token && !isAuthRoute && !isPublicRoute) {
    return NextResponse.redirect(new URL("/dang-nhap", request.url));
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



  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
