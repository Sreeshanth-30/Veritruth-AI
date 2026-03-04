import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
  display: "swap",
});

export const metadata: Metadata = {
  title: "VeriTruth AI — Multi-Layer Fake News Intelligence",
  description:
    "AI-powered system that analyses news content for misinformation, propaganda, sentiment manipulation, and source credibility. Built for students.",
  keywords: [
    "fake news",
    "misinformation",
    "AI",
    "fact check",
    "propaganda",
    "credibility",
    "media literacy",
  ],
  authors: [{ name: "VeriTruth AI Team" }],
  openGraph: {
    title: "VeriTruth AI — Multi-Layer Fake News Intelligence",
    description:
      "Analyse any news article or text for misinformation using advanced AI.",
    type: "website",
    locale: "en_US",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${spaceGrotesk.variable} font-sans`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
