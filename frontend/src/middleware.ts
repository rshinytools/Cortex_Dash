// ABOUTME: NextAuth middleware for protecting routes and handling authentication
// ABOUTME: Redirects users based on their role and enforces access control

import { withAuth } from 'next-auth/middleware';
import { NextResponse } from 'next/server';
import { UserRole } from '@/types';

export default withAuth(
  function middleware(req) {
    const token = req.nextauth.token;
    const pathname = req.nextUrl.pathname;
    
    // If no token or expired, redirect to login
    if (!token || !token.accessToken) {
      // Allow access to auth pages
      if (pathname.startsWith('/auth/')) {
        return NextResponse.next();
      }
      return NextResponse.redirect(new URL('/auth/login', req.url));
    }
    
    // Check token expiration if exp is available
    if (token.exp && Date.now() >= token.exp * 1000) {
      return NextResponse.redirect(new URL('/auth/login', req.url));
    }
    
    // Get user role
    const userRole = token?.user?.role as UserRole;
    
    // Handle root path redirect based on role
    if (pathname === '/') {
      if (userRole === UserRole.SYSTEM_ADMIN || userRole === UserRole.ORG_ADMIN) {
        return NextResponse.redirect(new URL('/admin', req.url));
      } else {
        return NextResponse.redirect(new URL('/dashboard', req.url));
      }
    }
    
    // Protect admin routes
    if (pathname.startsWith('/admin')) {
      if (userRole !== UserRole.SYSTEM_ADMIN && userRole !== UserRole.ORG_ADMIN) {
        return NextResponse.redirect(new URL('/dashboard', req.url));
      }
    }
    
    // Protect dashboard route - only for regular users
    if (pathname === '/dashboard') {
      if (userRole === UserRole.SYSTEM_ADMIN || userRole === UserRole.ORG_ADMIN) {
        return NextResponse.redirect(new URL('/admin', req.url));
      }
    }
    
    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token }) => {
        // This runs before the middleware function
        // Return true to continue to middleware, false to redirect to signIn page
        return !!token;
      },
    },
  }
);

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|auth).*)',
  ],
};