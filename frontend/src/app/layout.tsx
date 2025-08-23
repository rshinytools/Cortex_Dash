import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { RootProviders } from "@/components/providers/root-providers";

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
        <RootProviders>
          {children}
        </RootProviders>
      </body>
    </html>
  );
}