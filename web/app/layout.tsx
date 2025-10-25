import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import NavBar from "@/components/NavBar";
import Footer from "@/components/Footer";

// Define font variables
const fontSans = GeistSans;
const fontMono = GeistMono;

export const metadata: Metadata = {
  title: "VIBES.FM — Music Mixes & Tracklists",
  description: "Nalostta's curated music mixes, playlists, and tracklists.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${fontSans.variable} ${fontMono.variable}`}>
      <body className="font-sans antialiased bg-black text-white min-h-screen flex flex-col dark">
        <NavBar />
        <div className="flex-1">
          {children}
        </div>
        <Footer />
      </body>
    </html>
  );
}
