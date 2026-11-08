import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinPass AI – Intelligent Financial Planning",
  description: "AI-powered financial planning and investment guidance for Indian investors.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return <html lang="en"><body>{children}</body></html>;
}
