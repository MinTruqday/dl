import { NextResponse } from "next/server";
export function middleware(request) {
  const token = request.cookies.get("token")?.value;
  const { pathname } = request.nextUrl;
  if (
    !token &&
    (pathname.startsWith("/du-an") ||
      pathname.startsWith("/van-hanh") ||
      pathname.startsWith("/cai-dat"))
  )
    return NextResponse.redirect(new URL("/dang-nhap", request.url));
  return NextResponse.next();
}
export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
