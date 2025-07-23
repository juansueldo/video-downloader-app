import VideoDownloader from './components/VideoDownloader'
import { Youtube, Download, Music, FileText } from 'lucide-react'

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <Youtube className="w-8 h-8 text-red-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-800">
                YouTube Downloader
              </h1>
              <p className="text-gray-600 text-sm">
                Descarga videos con calidad profesional
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Features */}
      <section className="py-8 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Download className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-800 mb-1">Múltiples Calidades</h3>
              <p className="text-sm text-gray-600">Desde 144p hasta 4K</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Music className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-800 mb-1">Solo Audio</h3>
              <p className="text-sm text-gray-600">Extrae MP3 de alta calidad</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <FileText className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-800 mb-1">Subtítulos</h3>
              <p className="text-sm text-gray-600">Descarga en múltiples idiomas</p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-8">
        <div className="container mx-auto px-4">
          <VideoDownloader />
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-6 mt-12">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm text-gray-400">
            ⚠️ Usa esta herramienta responsablemente y respeta los derechos de autor
          </p>
        </div>
      </footer>
    </main>
  )
}