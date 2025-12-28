import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'ATLAS - Decision Intelligence for Market Viability',
  description: 'Evaluate startup market viability under uncertainty',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}


