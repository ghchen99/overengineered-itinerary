import { Inter } from 'next/font/google';
import { cn } from '@/lib/utils';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'AI Travel Planner',
  description: 'Create personalized travel itineraries with AI assistance',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn('min-h-screen bg-background font-sans antialiased', inter.className)}>
        {children}
      </body>
    </html>
  );
}