import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'CareCompass - AI Shadow Coach',
  description: 'AI-powered patient communication quality analyzer for healthcare providers',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
