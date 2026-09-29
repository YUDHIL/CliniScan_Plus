import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'CliniScan+ | AI Chest X-ray Triage & Specialist Referral Network',
  description: 'Hospital-grade AI Chest Radiograph Abnormality Detection (YOLO11) & Specialist Referral Network',
  icons: {
    icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🫁</text></svg>',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
