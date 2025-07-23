import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'YouTube Downloader - Descarga videos fácilmente',
  description: 'Descarga videos de YouTube con opciones de calidad, audio y subtítulos. Interfaz moderna y fácil de usar.',
  keywords: 'youtube, downloader, video, audio, subtitulos, descarga',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        {children}
      </body>
    </html>
  )
}