import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '面談記録',
  description: 'Zoom面談の記録と分析',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body className="bg-gray-50 min-h-screen">
        {children}
      </body>
    </html>
  )
}
