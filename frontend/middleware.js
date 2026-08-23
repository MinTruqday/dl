import { NextResponse } from "next/server";
export function middleware(request) {
    var _a;
    const token = (_a = request.cookies.get("token")) === null || _a === void 0 ? void 0 : _a.value;
    const { pathname } = request.nextUrl;
    if (!token && pathname.startsWith("/quan-tri"))
        return NextResponse.redirect(new URL("/dang-nhap", request.url));
    return NextResponse.next();
}
export const config = {
    matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
