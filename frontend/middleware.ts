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
    pathname.startsWith("/images/") ||
    pathname.startsWith("/kham-pha") ||
    pathname.startsWith("/tai-lieu/") ||
    pathname.startsWith("/chia-se/") ||
    pathname.startsWith("/dieu-khoan") ||
    pathname.startsWith("/tro-giup") ||
    pathname.startsWith("/auth/google/callback");

  if (!token && !isAuthRoute && !isPublicRoute) {
    return NextResponse.redirect(new URL("/dang-nhap", request.url));
  }

  if (role === "reader") {
    if (
      pathname.startsWith("/soan-thao") ||
      pathname === "/tai-lieu" ||
      pathname.startsWith("/cong-tac") ||
      pathname.startsWith("/luu-tru") ||
      pathname.startsWith("/phan-tich") ||
      pathname.startsWith("/kiem-toan") ||
      pathname.startsWith("/thu-thap") ||
      pathname.startsWith("/nguoi-dung") ||
      pathname.startsWith("/bao-cao") ||
      pathname.startsWith("/van-hanh")
    ) {
      return NextResponse.redirect(new URL("/", request.url));
    }
  }

  if (role === "author") {
    if (
      pathname.startsWith("/kiem-toan") ||
      pathname.startsWith("/thu-thap") ||
      pathname.startsWith("/nguoi-dung") ||
      pathname.startsWith("/bao-cao") ||
      pathname.startsWith("/van-hanh")
    ) {
      return NextResponse.redirect(new URL("/soan-thao", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
