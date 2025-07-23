#!/usr/bin/env python3
"""
YouTube Downloader API
Servidor FastAPI para descargar videos de YouTube
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
import yt_dlp
import os
import uuid
import asyncio
import logging
from typing import Optional, Dict, List
import json
import time
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Downloader API",
    description="API para descargar videos de YouTube con opciones avanzadas",
    version="1.0.0"
)

# CORS middleware - Permitir todas las origins para demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Limpiar archivos antiguos al iniciar
def cleanup_old_files():
    """Elimina archivos de más de 1 hora"""
    try:
        current_time = time.time()
        for file_path in DOWNLOAD_DIR.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > 3600:  # 1 hora
                    file_path.unlink()
                    logger.info(f"Archivo eliminado: {file_path}")
    except Exception as e:
        logger.error(f"Error limpiando archivos: {e}")

cleanup_old_files()

class VideoInfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    format_id: str
    include_subtitles: bool = False
    subtitle_lang: Optional[str] = None
    audio_only: bool = False

# Almacén de progreso de descargas
download_progress: Dict[str, Dict] = {}

def progress_hook(d):
    """Hook para capturar progreso de yt-dlp"""
    try:
        if d['status'] == 'downloading':
            # Extraer ID de descarga del filename
            filename = d.get('filename', '')
            download_id = None

            # Buscar el download_id en el filename
            for did in download_progress.keys():
                if did in filename:
                    download_id = did
                    break

            if not download_id:
                return

            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            if total_bytes > 0:
                percentage = (downloaded_bytes / total_bytes) * 100
                download_progress[download_id].update({
                    'status': 'downloading',
                    'percentage': round(percentage, 1),
                    'downloaded': downloaded_bytes,
                    'total': total_bytes,
                    'speed': speed,
                    'eta': eta
                })
        elif d['status'] == 'finished':
            # Buscar download_id
            filename = d.get('filename', '')
            for did in download_progress.keys():
                if did in filename:
                    download_progress[did]['status'] = 'processing'
                    break
    except Exception as e:
        logger.error(f"Error en progress_hook: {e}")

@app.get("/")
def read_root():
    return {
        "message": "YouTube Downloader API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "video_info": "/api/video-info",
            "download": "/api/download",
            "progress": "/api/download-progress/{download_id}",
            "file": "/api/download-file/{download_id}"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/api/video-info")
async def get_video_info(request: VideoInfoRequest):
    """Obtiene información detallada del video"""
    try:
        logger.info(f"Obteniendo info para: {request.url}")

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)

        if not info:
            raise HTTPException(status_code=400, detail="No se pudo obtener información del video")

        # Procesar TODOS los formatos de video (muxed y video-only)
        video_formats = []
        audio_formats = []
        seen_video = set()
        seen_audio = set()

        # Primero, agregar formatos especiales para mejores calidades
        special_formats = [
            {'format_id': 'best[height<=4320]', 'quality': '4K (Mejor)', 'ext': 'mp4', 'type': 'best', 'note': 'Mejor calidad disponible en 4K'},
            {'format_id': 'best[height<=2160]', 'quality': '4K', 'ext': 'mp4', 'type': 'best', 'note': 'Mejor calidad disponible en 4K'},
            {'format_id': 'best[height<=1440]', 'quality': '1440p', 'ext': 'mp4', 'type': 'best', 'note': 'Mejor calidad disponible en 1440p'},
            {'format_id': 'best[height<=1080]', 'quality': '1080p', 'ext': 'mp4', 'type': 'best', 'note': 'Mejor calidad disponible en 1080p'},
            {'format_id': 'best[height<=720]', 'quality': '720p', 'ext': 'mp4', 'type': 'best', 'note': 'Mejor calidad disponible en 720p'},
            {'format_id': 'best[height<=480]', 'quality': '480p', 'ext': 'mp4', 'type': 'best', 'note': 'Mejor calidad disponible en 480p'},
            {'format_id': 'best[height<=360]', 'quality': '360p', 'ext': 'mp4', 'type': 'best', 'note': 'Mejor calidad disponible en 360p'},
        ]

        # Agregar formatos especiales al inicio
        for fmt in special_formats:
            video_formats.append({
                'format_id': fmt['format_id'],
                'quality': fmt['quality'],
                'ext': fmt['ext'],
                'filesize': 0,  # No podemos saber el tamaño hasta descargar
                'fps': 30,
                'note': fmt['note'],
                'vcodec': 'auto',
                'acodec': 'auto',
                'type': fmt['type'],
                'is_special': True
            })

        # Luego procesar formatos individuales
        for fmt in info.get('formats', []):
            # Formatos de video (tanto muxed como video-only)
            if fmt.get('vcodec') != 'none':
                height = fmt.get('height', 0)
                if height and height >= 144:  # Filtrar calidades muy bajas
                    quality = f"{height}p"
                    ext = fmt.get('ext', 'mp4')
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    fps = fmt.get('fps', 30)
                    has_audio = fmt.get('acodec') != 'none'
                    
                    # Crear una clave única para evitar duplicados
                    format_key = f"{quality}_{ext}_{fps}_{has_audio}"
                    if format_key not in seen_video:
                        video_type = 'video+audio' if has_audio else 'video-only'
                        note = fmt.get('format_note', '')
                        if not has_audio:
                            note += ' (requiere audio separado)'
                        
                        video_formats.append({
                            'format_id': fmt['format_id'],
                            'quality': quality,
                            'ext': ext,
                            'filesize': filesize,
                            'fps': fps,
                            'note': note,
                            'vcodec': fmt.get('vcodec', ''),
                            'acodec': fmt.get('acodec', 'none'),
                            'type': video_type,
                            'has_audio': has_audio,
                            'is_special': False
                        })
                        seen_video.add(format_key)

            # Formatos de solo audio
            elif fmt.get('vcodec') == 'none' and fmt.get('acodec') != 'none':
                abr = fmt.get('abr', 0)
                if abr and abr >= 64:  # Filtrar calidades muy bajas
                    quality = f"{int(abr)}kbps"
                    ext = fmt.get('ext', 'mp3')
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)

                    format_key = f"{quality}_{ext}"
                    if format_key not in seen_audio and len(audio_formats) < 8:
                        audio_formats.append({
                            'format_id': fmt['format_id'],
                            'quality': quality,
                            'ext': ext,
                            'filesize': filesize,
                            'abr': abr,
                            'acodec': fmt.get('acodec', ''),
                            'type': 'audio',
                            'note': fmt.get('format_note', '')
                        })
                        seen_audio.add(format_key)

        # Ordenar formatos por calidad (especiales primero, luego por resolución)
        def sort_video_formats(fmt):
            if fmt.get('is_special'):
                # Los formatos especiales van primero, ordenados por calidad
                quality_order = {'4K (Mejor)': 0, '4K': 1, '1440p': 2, '1080p': 3, '720p': 4, '480p': 5, '360p': 6}
                return (0, quality_order.get(fmt['quality'], 999))
            else:
                # Formatos individuales van después, ordenados por resolución
                try:
                    height = int(fmt['quality'].replace('p', ''))
                    return (1, -height)  # Negativo para orden descendente
                except:
                    return (2, 0)

        video_formats.sort(key=sort_video_formats)
        audio_formats.sort(key=lambda x: x.get('abr', 0), reverse=True)

        # Procesar subtítulos con más detalle
        subtitles = []
        if info.get('subtitles'):
            for lang, subs in info['subtitles'].items():
                if subs:  # Verificar que hay subtítulos disponibles
                    # Obtener nombre del idioma más descriptivo
                    lang_names = {
                        'en': 'English',
                        'es': 'Español',
                        'fr': 'Français',
                        'de': 'Deutsch',
                        'it': 'Italiano',
                        'pt': 'Português',
                        'ru': 'Русский',
                        'ja': '日本語',
                        'ko': '한국어',
                        'zh': '中文',
                        'ar': 'العربية'
                    }
                    
                    display_name = lang_names.get(lang, lang.upper())
                    
                    subtitles.append({
                        'lang': lang,
                        'name': display_name,
                        'formats': [sub.get('ext', 'vtt') for sub in subs],
                        'auto': any(sub.get('name', '').startswith('auto-generated') for sub in subs)
                    })

        # Ordenar subtítulos (inglés y español primero)
        def sort_subtitles(sub):
            priority_langs = {'en': 0, 'es': 1}
            return priority_langs.get(sub['lang'], 999)
        
        subtitles.sort(key=sort_subtitles)

        # Información adicional
        duration = info.get('duration', 0)
        view_count = info.get('view_count', 0)
        like_count = info.get('like_count', 0)
        upload_date = info.get('upload_date', '')

        result = {
            'title': info.get('title', 'Sin título'),
            'duration': duration,
            'thumbnail': info.get('thumbnail', ''),
            'uploader': info.get('uploader', 'Desconocido'),
            'view_count': view_count,
            'like_count': like_count,
            'upload_date': upload_date,
            'description': info.get('description', '')[:500] + '...' if info.get('description', '') else '',
            'formats': video_formats[:15],  # Más formatos disponibles
            'audio_formats': audio_formats[:8],
            'subtitles': subtitles[:15]  # Más subtítulos
        }

        logger.info(f"Info obtenida: {len(video_formats)} formatos de video, {len(audio_formats)} de audio, {len(subtitles)} subtítulos")
        return result

    except yt_dlp.DownloadError as e:
        logger.error(f"Error de yt-dlp: {e}")
        raise HTTPException(status_code=400, detail=f"Error al procesar el video: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/api/download")
async def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Inicia la descarga del video"""
    try:
        download_id = str(uuid.uuid4())[:8]  # ID más corto
        logger.info(f"Iniciando descarga {download_id} para: {request.url}")

        # Configurar nombre de archivo
        filename_template = f"{download_id}_%(title)s.%(ext)s"

        # Opciones base de yt-dlp con User-Agent
        ydl_opts = {
            'format': request.format_id,
            'outtmpl': str(DOWNLOAD_DIR / filename_template),
            'progress_hooks': [progress_hook],
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }

        # Si el formato es uno de los "best", asegurar que combine video y audio
        if request.format_id.startswith('best['):
            # Para formatos "best", yt-dlp automáticamente combina video y audio
            pass
        else:
            # Para formatos específicos, si es video-only, combinar con mejor audio
            # yt-dlp automáticamente detecta esto y descarga audio si es necesario
            pass

        # Configurar subtítulos
        if request.include_subtitles and request.subtitle_lang:
            ydl_opts.update({
                'writesubtitles': True,
                'subtitleslangs': [request.subtitle_lang],
                'subtitlesformat': 'vtt',
                'writeautomaticsub': True,  # También descargar subtítulos automáticos si están disponibles
            })

        # Configurar extracción de audio
        if request.audio_only:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        # Inicializar progreso
        download_progress[download_id] = {
            'status': 'starting',
            'percentage': 0,
            'downloaded': 0,
            'total': 0,
            'speed': 0,
            'eta': 0,
            'created_at': time.time()
        }

        def download_task():
            """Tarea de descarga en background"""
            try:
                logger.info(f"Ejecutando descarga {download_id}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([request.url])

                download_progress[download_id]['status'] = 'completed'
                download_progress[download_id]['percentage'] = 100
                logger.info(f"Descarga {download_id} completada")

            except Exception as e:
                logger.error(f"Error en descarga {download_id}: {e}")
                download_progress[download_id] = {
                    'status': 'error',
                    'error': str(e),
                    'percentage': 0
                }

        # Ejecutar descarga en background
        background_tasks.add_task(download_task)

        return {
            'download_id': download_id,
            'status': 'started',
            'message': 'Descarga iniciada correctamente'
        }

    except Exception as e:
        logger.error(f"Error iniciando descarga: {e}")
        raise HTTPException(status_code=500, detail=f"Error al iniciar descarga: {str(e)}")

@app.get("/api/download-progress/{download_id}")
async def get_download_progress(download_id: str):
    """Obtiene el progreso de una descarga"""
    if download_id not in download_progress:
        raise HTTPException(status_code=404, detail="Descarga no encontrada")

    progress = download_progress[download_id].copy()

    # Formatear velocidad y ETA
    if progress.get('speed'):
        speed_mb = progress['speed'] / (1024 * 1024)
        progress['speed_formatted'] = f"{speed_mb:.1f} MB/s"

    if progress.get('eta'):
        eta_min = progress['eta'] // 60
        eta_sec = progress['eta'] % 60
        progress['eta_formatted'] = f"{int(eta_min)}:{int(eta_sec):02d}"

    return progress

@app.get("/api/download-file/{download_id}")
async def download_file(download_id: str):
    """Descarga el archivo completado"""
    if download_id not in download_progress:
        raise HTTPException(status_code=404, detail="Descarga no encontrada")

    if download_progress[download_id]['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Descarga no completada")

    # Buscar archivo descargado
    for file_path in DOWNLOAD_DIR.glob(f"{download_id}_*"):
        if file_path.is_file():
            logger.info(f"Sirviendo archivo: {file_path}")
            return FileResponse(
                str(file_path),
                filename=file_path.name,
                media_type='application/octet-stream'
            )

    raise HTTPException(status_code=404, detail="Archivo no encontrado")

@app.delete("/api/cleanup")
async def cleanup_downloads():
    """Limpia archivos de descarga antiguos"""
    try:
        cleanup_old_files()
        return {"message": "Limpieza completada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en limpieza: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("Iniciando YouTube Downloader API...")
    print("API: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)
