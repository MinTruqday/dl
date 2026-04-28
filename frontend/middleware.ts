import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  const role = request.cookies.get('role')?.value || 'reader'
  const { pathname } = request.nextUrl

  // Chưa đăng nhập -> Luôn đá về /login (trừ các route auth)
  const isAuthRoute = pathname.startsWith('/login') || pathname.startsWith('/register')
  if (!token && !isAuthRoute) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Reader block
  if (role === 'reader') {
    if (pathname.startsWith('/studio') || pathname.startsWith('/moderation') || pathname.startsWith('/admin')) {
      return NextResponse.redirect(new URL('/', request.url))
    }
  }

  // Author block
  if (role === 'author') {
    if (pathname.startsWith('/moderation') || pathname.startsWith('/admin')) {
      return NextResponse.redirect(new URL('/studio', request.url))
    }
  }

  // Moderator block
  if (role === 'moderator') {
    if (pathname.startsWith('/studio') || pathname.startsWith('/admin')) {
      return NextResponse.redirect(new URL('/moderation', request.url))
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
