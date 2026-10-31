import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'EDEN Grid Sentinel | Microgrid Control Room',
  description: 'Read-only, simulation-only school microgrid energy forecasting and scheduling dashboard.',
};

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body>{children}</body></html>;
}
