// ABOUTME: Debug page to check session and user information
// ABOUTME: Temporary page to diagnose authentication issues

'use client';

import { useSession } from 'next-auth/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function DebugPage() {
  const { data: session, status } = useSession();

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">Debug Information</h1>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Session Status</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-lg overflow-auto">
              {JSON.stringify({ status }, null, 2)}
            </pre>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Session Data</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-lg overflow-auto">
              {JSON.stringify(session, null, 2)}
            </pre>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>User Information</CardTitle>
          </CardHeader>
          <CardContent>
            {session?.user && (
              <div className="space-y-2">
                <p><strong>Email:</strong> {session.user.email}</p>
                <p><strong>Name:</strong> {session.user.full_name || 'Not set'}</p>
                <p><strong>Role:</strong> {session.user.role || 'Not set'}</p>
                <p><strong>Org ID:</strong> {session.user.org_id || 'Not set'}</p>
                <p><strong>Is Superuser:</strong> {(session.user as any).is_superuser ? 'Yes' : 'No'}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}