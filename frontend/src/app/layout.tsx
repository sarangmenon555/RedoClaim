import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "RedoClaim — AI Insurance Research Tool (Not Legal Advice)",
  description: "AI-assisted tool for Indian policyholders to understand IRDAI regulations and prepare draft appeal documents. Not a substitute for legal advice.",
  keywords: "insurance claim rejection IRDAI grievance ombudsman India AI tool",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body style={{background:"#0A0A0F",color:"#F1F0FF",fontFamily:"'Inter',system-ui,sans-serif"}}>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              borderRadius: "10px",
              fontSize: "13px",
              background: "#16161F",
              color: "#F1F0FF",
              border: "1px solid #2E2E42",
            },
          }}
        />
      </body>
    </html>
  );
}
