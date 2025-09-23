import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import ThemeProvider from "@/components/providers/ThemeProvider";
import { JiveApiProvider } from "@/components/providers/JiveApiProvider";
import { NamespaceProvider } from "@/contexts/NamespaceContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Jive Dev Companion",
  description: "React companion app for Jive MCP development workflow management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider>
          <JiveApiProvider>
            <NamespaceProvider>
              {children}
            </NamespaceProvider>
          </JiveApiProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
