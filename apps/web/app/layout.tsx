import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EGYXOS Password Manager",
  description: "A local-first, zero-knowledge password manager."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
