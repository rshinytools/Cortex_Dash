import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { RBACProvider } from "@/lib/rbac-context";
import { QueryProvider } from "@/components/providers/query-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from 'sonner';

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Clinical Dashboard - Enterprise Clinical Trial Management",
  description: "Enterprise-level clinical trial data visualization and management platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <RBACProvider>
              <QueryProvider>
                {children}
                <Toaster />
                <Sonner />
              </QueryProvider>
            </RBACProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}