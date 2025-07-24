'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import Image from 'next/image'
import {
  Download, Video, Music, FileText, Loader2, CheckCircle,
  AlertCircle, Eye, ThumbsUp, Calendar, Clock,
  Zap, HardDrive, Cookie, RefreshCw, Shield
} from 'lucide-react'

interface VideoFormat {
  format_id: string
  quality: string
  ext: string
  filesize: number
  fps?: number
  note: string
  vcodec?: string
  acodec?: string
  abr?: number
  type: string
}

interface Subtitle {
  lang: string
  name: string
  formats: string[]
}

interface VideoInfo {
  title: string
  duration: number
  thumbnail: string
  uploader: string
  view_count: number
  like_count?: number
  upload_date?: string
  description?: string
  formats: VideoFormat[]
  audio_formats: VideoFormat[]
  subtitles: Subtitle[]
}

interface DownloadProgress {
  status: string
  percentage?: number
  downloaded?: number
  total?: number
  speed?: number
  eta?: number
  speed_formatted?: string
  eta_formatted?: string
  error?: string
}

interface CookieStatus {
  exists: boolean
  file_size?: number
  age_hours?: number
  needs_refresh?: boolean
  error?: string
}

const API_BASE = process.env.NODE_ENV === 'production'
  ? 'https://video-downloader-app-ic05.onrender.com'
  : 'http://localhost:8000'

export default function VideoDownloader() {
  const [url, setUrl] = useState('')
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedFormat, setSelectedFormat] = useState('')
  const [includeSubtitles, setIncludeSubtitles] = useState(false)
  const [selectedSubtitle, setSelectedSubtitle] = useState('')
  const [audioOnly, setAudioOnly] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress | null>(null)
  const [error, setError] = useState('')
  
  // Estados para cookies
  const [cookieStatus, setCookieStatus] = useState<CookieStatus | null>(null)
  const [cookieLoading, setCookieLoading] = useState(false)
  const [showCookieDetails, setShowCookieDetails] = useState(false)

  // Verificar cookies al cargar la página
  useEffect(() => {
    checkCookieStatus()
  }, [])

  useEffect(() => {
    setError('')
    setVideoInfo(null)
    setDownloadProgress(null)
  }, [url])

  const checkCookieStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/cookies/status`)
      setCookieStatus(response.data)
    } catch (error) {
      console.error('Error checking cookies:', error)
      setCookieStatus({ exists: false, needs_refresh: true })
    }
  }

  const refreshCookies = async () => {
    setCookieLoading(true)
    try {
      const response = await axios.post(`${API_BASE}/api/cookies/refresh`)
      if (response.data.success) {
        await checkCookieStatus()
        setError('')
      }
    } catch (error: any) {
      const errorMsg = error?.response?.data?.detail || error?.message || 'Error desconocido'
      setError(`Error actualizando cookies: ${errorMsg}`)
    } finally {
      setCookieLoading(false)
    }
  }

  const ensureCookiesBeforeDownload = async (): Promise<boolean> => {
    // Verificar estado actual de cookies
    await checkCookieStatus()
    
    if (!cookieStatus?.exists || cookieStatus?.needs_refresh) {
      setError('Actualizando cookies necesarias para la descarga...')
      
      try {
        await refreshCookies()
        // Esperar un momento para que se procesen
        await new Promise(resolve => setTimeout(resolve, 1000))
        return true
      } catch (error) {
        setError('No se pudieron actualizar las cookies. Intenta nuevamente.')
        return false
      }
    }
    
    return true
  }

  const isValidYouTubeUrl = (url: string) => {
    const patterns = [
      /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\/.+/,
      /^https?:\/\/(www\.)?youtube\.com\/watch\?v=.+/,
      /^https?:\/\/youtu\.be\/.+/
    ]
    return patterns.some(pattern => pattern.test(url))
  }

  const getVideoInfo = async () => {
    if (!url.trim()) {
      setError('Por favor ingresa una URL')
      return
    }

    if (!isValidYouTubeUrl(url)) {
      setError('Por favor ingresa una URL válida de YouTube')
      return
    }

    setLoading(true)
    setError('')

    try {
      // Asegurar que tenemos cookies antes de obtener info
      const cookiesReady = await ensureCookiesBeforeDownload()
      if (!cookiesReady) {
        setLoading(false)
        return
      }

      const response = await axios.post(`${API_BASE}/api/video-info`, { url }, { 
        timeout: 30000 
      })
      
      setVideoInfo(response.data)
      setSelectedFormat(response.data.formats[0]?.format_id || '')
      if (response.data.subtitles.length > 0) {
        setSelectedSubtitle(response.data.subtitles[0].lang)
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }, message?: string }
      let errorMsg = err?.response?.data?.detail || err?.message || 'Error desconocido'
      
      // Si es un error relacionado con cookies, sugerir actualización
      if (errorMsg.includes('Sign in to confirm') || 
          errorMsg.includes('private') || 
          errorMsg.includes('available')) {
        errorMsg += '. Intenta actualizar las cookies y vuelve a intentar.'
        setShowCookieDetails(true)
      }
      
      setError(`Error al obtener información: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const startDownload = async () => {
    if (!selectedFormat) {
      setError('Selecciona un formato')
      return
    }

    setError('')

    try {
      // Asegurar cookies antes de descargar
      const cookiesReady = await ensureCookiesBeforeDownload()
      if (!cookiesReady) {
        return
      }

      const response = await axios.post(`${API_BASE}/api/download`, {
        url,
        format_id: selectedFormat,
        include_subtitles: includeSubtitles,
        subtitle_lang: selectedSubtitle,
        audio_only: audioOnly
      })

      pollDownloadProgress(response.data.download_id)

    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }, message?: string }
      let errorMsg = err?.response?.data?.detail || err?.message || 'Error desconocido'
      
      // Si es un error relacionado con cookies
      if (errorMsg.includes('Sign in to confirm') || 
          errorMsg.includes('private') || 
          errorMsg.includes('available')) {
        errorMsg += '. Las cookies pueden estar desactualizadas.'
        setShowCookieDetails(true)
      }
      
      setError(`Error al iniciar descarga: ${errorMsg}`)
    }
  }

  const pollDownloadProgress = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/download-progress/${id}`)
        setDownloadProgress(response.data)

        if (response.data.status === 'completed') {
          clearInterval(interval)
          const link = document.createElement('a')
          link.href = `${API_BASE}/api/download-file/${id}`
          link.download = ''
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        } else if (response.data.status === 'error') {
          clearInterval(interval)
          setError('Error en la descarga: ' + response.data.error)
        }
      } catch (error) {
        clearInterval(interval)
        console.error('Error polling progress:', error)
        setError('Error obteniendo progreso de descarga')
      }
    }, 1000)

    setTimeout(() => clearInterval(interval), 600000)
  }

  const formatFileSize = (bytes: number) => {
    if (!bytes || bytes === 0) return 'Desconocido'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const formatDuration = (seconds: number) => {
    if (!seconds) return '0:00'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  const formatNumber = (num: number) => {
    if (!num) return '0'
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  const getCookieStatusColor = () => {
    if (!cookieStatus?.exists) return 'text-red-600'
    if (cookieStatus.needs_refresh) return 'text-yellow-600'
    return 'text-green-600'
  }

  const getCookieStatusText = () => {
    if (!cookieStatus?.exists) return 'Sin cookies'
    if (cookieStatus.needs_refresh) return 'Necesitan actualización'
    return 'Actualizadas'
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Cookie Status Bar */}
      <div className="card bg-gray-50 border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium">Estado de Cookies:</span>
              <span className={`text-sm font-semibold ${getCookieStatusColor()}`}>
                {getCookieStatusText()}
              </span>
            </div>
            
            {cookieStatus?.age_hours && (
              <span className="text-xs text-gray-500">
                (Edad: {cookieStatus.age_hours.toFixed(1)}h)
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCookieDetails(!showCookieDetails)}
              className="text-xs text-gray-600 hover:text-gray-800"
            >
              {showCookieDetails ? 'Ocultar' : 'Detalles'}
            </button>
            
            <button
              onClick={refreshCookies}
              disabled={cookieLoading}
              className="flex items-center gap-1 px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
            >
              {cookieLoading ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <RefreshCw className="w-3 h-3" />
              )}
              Actualizar
            </button>
          </div>
        </div>

        {showCookieDetails && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div>
                <span className="font-medium">Existe:</span>
                <span className={cookieStatus?.exists ? 'text-green-600 ml-1' : 'text-red-600 ml-1'}>
                  {cookieStatus?.exists ? 'Sí' : 'No'}
                </span>
              </div>
              {cookieStatus?.file_size && (
                <div>
                  <span className="font-medium">Tamaño:</span>
                  <span className="ml-1">{formatFileSize(cookieStatus.file_size)}</span>
                </div>
              )}
              {cookieStatus?.age_hours && (
                <div>
                  <span className="font-medium">Última actualización:</span>
                  <span className="ml-1">{cookieStatus.age_hours.toFixed(1)} horas</span>
                </div>
              )}
            </div>
            
            <div className="mt-2 text-xs text-gray-600">
              <Cookie className="w-3 h-3 inline mr-1" />
              Las cookies se usan para acceder a videos que requieren verificación.
              Se actualizan automáticamente cada 24 horas.
            </div>
          </div>
        )}
      </div>

      {/* URL Input */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className="flex-1 input-field"
            onKeyPress={(e) => e.key === 'Enter' && getVideoInfo()}
          />
          <button
            onClick={getVideoInfo}
            disabled={loading || !url.trim()}
            className="btn-primary min-w-[120px]"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Video className="w-4 h-4" />
            )}
            {loading ? 'Analizando...' : 'Analizar'}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}
      </div>

      {/* Video Info - Rest of your existing component remains the same */}
      {videoInfo && (
        <div className="card">
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Thumbnail y info básica */}
            <div className="lg:w-1/3">
              <img
                src={videoInfo.thumbnail}
                alt={videoInfo.title}
                className="w-full aspect-video object-cover rounded-lg shadow-sm"
              />

              <div className="mt-4 space-y-2">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Eye className="w-4 h-4" />
                  <span>{formatNumber(videoInfo.view_count)} vistas</span>
                </div>

                {videoInfo.like_count && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <ThumbsUp className="w-4 h-4" />
                    <span>{formatNumber(videoInfo.like_count)} likes</span>
                  </div>
                )}

                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Clock className="w-4 h-4" />
                  <span>{formatDuration(videoInfo.duration)}</span>
                </div>

                {videoInfo.upload_date && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Calendar className="w-4 h-4" />
                    <span>{videoInfo.upload_date}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Detalles y opciones */}
            <div className="lg:w-2/3">
              <h2 className="text-xl font-semibold text-gray-800 mb-2 line-clamp-2">
                {videoInfo.title}
              </h2>
              <p className="text-gray-600 mb-4">Canal: {videoInfo.uploader}</p>

              {videoInfo.description && (
                <p className="text-sm text-gray-600 mb-6 line-clamp-3">
                  {videoInfo.description}
                </p>
              )}

              {/* Opciones de descarga */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Resto de tu componente existente... */}
                {/* Formato de video */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Video className="w-4 h-4 inline mr-1" />
                    Calidad del Video
                  </label>
                  <select
                    value={selectedFormat}
                    onChange={(e) => setSelectedFormat(e.target.value)}
                    className="w-full input-field"
                    disabled={audioOnly}
                  >
                    {videoInfo.formats.map((format) => (
                      <option key={format.format_id} value={format.format_id}>
                        {format.quality} ({format.ext}) - {formatFileSize(format.filesize)}
                        {format.fps && format.fps > 30 ? ` - ${format.fps}fps` : ''}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Opciones de audio */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Music className="w-4 h-4 inline mr-1" />
                    Opciones de Audio
                  </label>
                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={audioOnly}
                        onChange={(e) => {
                          setAudioOnly(e.target.checked)
                          if (e.target.checked && videoInfo.audio_formats.length > 0) {
                            setSelectedFormat(videoInfo.audio_formats[0].format_id)
                          } else if (!e.target.checked && videoInfo.formats.length > 0) {
                            setSelectedFormat(videoInfo.formats[0].format_id)
                          }
                        }}
                        className="mr-2"
                      />
                      Solo descargar audio (MP3)
                    </label>

                    {audioOnly && videoInfo.audio_formats.length > 0 && (
                      <select
                        value={selectedFormat}
                        onChange={(e) => setSelectedFormat(e.target.value)}
                        className="w-full input-field"
                      >
                        {videoInfo.audio_formats.map((format) => (
                          <option key={format.format_id} value={format.format_id}>
                            {format.quality} ({format.ext}) - {formatFileSize(format.filesize)}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>

                {/* Subtítulos */}
                {videoInfo.subtitles.length > 0 && (
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <FileText className="w-4 h-4 inline mr-1" />
                      Subtítulos
                    </label>
                    <div className="space-y-3">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={includeSubtitles}
                          onChange={(e) => setIncludeSubtitles(e.target.checked)}
                          className="mr-2"
                        />
                        Incluir subtítulos
                      </label>

                      {includeSubtitles && (
                        <select
                          value={selectedSubtitle}
                          onChange={(e) => setSelectedSubtitle(e.target.value)}
                          className="w-full input-field max-w-xs"
                        >
                          <option value="">Seleccionar idioma</option>
                          {videoInfo.subtitles.map((sub) => (
                            <option key={sub.lang} value={sub.lang}>
                              {sub.name} ({sub.lang})
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Botón de descarga */}
              <div className="mt-6">
                <button
                  onClick={startDownload}
                  disabled={!selectedFormat || downloadProgress?.status === 'downloading'}
                  className="btn-success w-full sm:w-auto min-w-[200px]"
                >
                  <Download className="w-5 h-5" />
                  {downloadProgress?.status === 'downloading' ? 'Descargando...' : 'Descargar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Progress - Rest remains the same */}
      {downloadProgress && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Estado de la Descarga
          </h3>

          {downloadProgress.status === 'starting' && (
            <div className="flex items-center gap-2 text-blue-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Iniciando descarga...</span>
            </div>
          )}

          {downloadProgress.status === 'downloading' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Descargando... {downloadProgress.percentage?.toFixed(1)}%</span>
                </div>
                <div className="text-sm text-gray-600 flex items-center gap-4">
                  {downloadProgress.speed_formatted && (
                    <span className="flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      {downloadProgress.speed_formatted}
                    </span>
                  )}
                  {downloadProgress.eta_formatted && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {downloadProgress.eta_formatted}
                    </span>
                  )}
                </div>
              </div>

              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full progress-bar"
                  style={{ width: `${downloadProgress.percentage || 0}%` }}
                ></div>
              </div>

              {downloadProgress.downloaded && downloadProgress.total && (
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    <HardDrive className="w-3 h-3" />
                    {formatFileSize(downloadProgress.downloaded)} / {formatFileSize(downloadProgress.total)}
                  </span>
                </div>
              )}
            </div>
          )}

          {downloadProgress.status === 'processing' && (
            <div className="flex items-center gap-2 text-orange-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Procesando archivo...</span>
            </div>
          )}

          {downloadProgress.status === 'completed' && (
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle className="w-5 h-5" />
              <span>¡Descarga completada! El archivo se descargará automáticamente.</span>
            </div>
          )}

          {downloadProgress.status === 'error' && (
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-5 h-5" />
              <span>Error: {downloadProgress.error}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
