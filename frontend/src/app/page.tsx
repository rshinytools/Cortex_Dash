// ABOUTME: Home page that redirects authenticated users to dashboard
// ABOUTME: Shows a loading state while checking authentication

import { redirect } from 'next/navigation';

export default function Home() {
  redirect('/dashboard');
}
