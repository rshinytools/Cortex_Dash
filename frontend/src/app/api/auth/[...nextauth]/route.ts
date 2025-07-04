// ABOUTME: NextAuth API route handler for authentication endpoints
// ABOUTME: Handles login, logout, and session management

import NextAuth from 'next-auth';
import { authOptions } from '@/lib/auth';

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };