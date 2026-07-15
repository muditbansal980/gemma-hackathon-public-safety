import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Public Safety Monitor",
  description: "Real-time public safety monitoring dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
