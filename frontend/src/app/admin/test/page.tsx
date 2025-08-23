// ABOUTME: Test page to debug navigation issues
// ABOUTME: Simple page to verify client-side navigation

'use client';

export default function TestPage() {
  console.log('Test page rendered');
  
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Test Admin Page</h1>
      <p>If you see "Auth context: Checking authentication..." in console, the app remounted.</p>
      <p>If not, navigation worked correctly.</p>
    </div>
  );
}