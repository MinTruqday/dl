import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("token")?.value;
  const role = request.cookies.get("role")?.value || "reader";
  const { pathname } = request.nextUrl;

  if (token && role === "reader") {
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

  if (token && role === "author") {
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
