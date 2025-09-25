import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import ThemeProvider from "@/components/providers/ThemeProvider";
import { JiveApiProvider } from "@/components/providers/JiveApiProvider";
import { Inter } from "next/font/google";
import { NamespaceProvider } from "@/contexts/NamespaceContext";

const inter = Inter({
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
      <body className={`${inter.className} antialiased`}>
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
