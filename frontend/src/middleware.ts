/**
 * VeriTruth AI — Next.js Route Protection Middleware
 * Redirects unauthenticated users away from protected pages.
 */
import { NextRequest, NextResponse } from "next/server";

const PROTECTED_PATHS = ["/dashboard", "/admin", "/analyze"];
const AUTH_PATHS = ["/login", "/signup"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("access_token")?.value;

  // Redirect authenticated users away from login/signup
  if (token && AUTH_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // Redirect unauthenticated users away from protected pages
  if (!token && PROTECTED_PATHS.some((p) => pathname.startsWith(p))) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|api/).*)",
  ],
};
