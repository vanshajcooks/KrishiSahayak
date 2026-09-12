import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'KhetSaathi — Smart Farming Assistant',
  description: 'Field-ready precision smart farming assistant for Indian farmers (SIH Problem Statement 26180)',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: '#15803d',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased selection:bg-green-100 selection:text-green-900">
        {children}
      </body>
    </html>
  );
}
