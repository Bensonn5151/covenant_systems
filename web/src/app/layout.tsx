import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Covenant Systems: The Operating System for Regulation",
  description: "Turn static regulatory noise into dynamic, auditable action.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider
      appearance={{
        variables: {
          colorPrimary: "#22c55e",
          colorBackground: "#111111",
          colorInputBackground: "#1a1a1a",
          colorInputText: "#f3f4f6",
          colorText: "#f3f4f6",
          colorTextSecondary: "#9ca3af",
          colorTextOnPrimaryBackground: "#000000",
          colorNeutral: "#f3f4f6",
          borderRadius: "0.75rem",
        },
        elements: {
          card: "bg-[#111111] border border-gray-800 shadow-2xl",
          headerTitle: "text-white",
          headerSubtitle: "text-gray-400",
          socialButtonsBlockButton: "bg-[#1a1a1a] border-gray-700 text-gray-200 hover:bg-[#222]",
          socialButtonsBlockButtonText: "text-gray-200",
          dividerLine: "bg-gray-700",
          dividerText: "text-gray-500",
          formFieldLabel: "text-gray-300",
          formFieldInput: "bg-[#1a1a1a] border-gray-700 text-gray-100 placeholder-gray-500",
          footerActionLink: "text-green-400 hover:text-green-300",
          footerActionText: "text-gray-400",
          identityPreviewEditButton: "text-green-400",
          formButtonPrimary: "bg-green-500 hover:bg-green-400 text-black font-bold",
          internal: "text-gray-300",
        },
      }}
    >
      <html lang="en">
        <body
          className={`${geistSans.variable} ${geistMono.variable} antialiased`}
        >
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
