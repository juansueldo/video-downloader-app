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
import requests
import random
import string

COOKIES_DIR = Path("cookies")
COOKIES_DIR.mkdir(exist_ok=True)
COOKIES_FILE = COOKIES_DIR / "cookies.txt"

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

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

def generate_session_data():
    """Genera datos de sesión aleatorios pero realistas"""
    session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    visitor_id = ''.join(random.choices(string.ascii_letters + string.digits, k=11))
    client_id = ''.join(random.choices(string.digits, k=19))
    
    return {
        'session_id': session_id,
        'visitor_id': visitor_id,
        'client_id': client_id
    }

def create_youtube_cookies():
    """Crea un archivo de cookies básico para YouTube"""
    try:
        session_data = generate_session_data()
        
        # Cookies básicas de YouTube (formato Netscape)
        cookies_content = f"""# Netscape HTTP Cookie File
# This file contains the HTTP cookies for YouTube
# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}

.youtube.com	TRUE	/	FALSE	{int(time.time()) + 31536000}	VISITOR_INFO1_LIVE	{session_data['visitor_id']}
.youtube.com	TRUE	/	FALSE	{int(time.time()) + 31536000}	YSC	{session_data['session_id']}
.youtube.com	TRUE	/	TRUE	{int(time.time()) + 31536000}	CONSENT	YES+cb.20210328-17-p0.en+FX+{random.randint(100, 999)}
.youtube.com	TRUE	/	FALSE	{int(time.time()) + 31536000}	GPS	1
.youtube.com	TRUE	/	FALSE	{int(time.time()) + 86400}	ST-{random.randint(1000000, 9999999)}	{session_data['client_id']}
"""
        
        with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
            f.write(cookies_content)
            
        logger.info(f"Cookies creadas en: {COOKIES_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando cookies: {e}")
        return False

def refresh_cookies():
    """Actualiza las cookies haciendo una request a YouTube"""
    try:
        # Hacer request a YouTube para obtener cookies frescas
        session = requests.Session()
        session.headers.update(BROWSER_HEADERS)
        
        # Request inicial a la página principal
        response = session.get('https://www.youtube.com', timeout=10)
        
        if response.status_code == 200:
            # Convertir cookies de requests a formato Netscape
            cookies_lines = [
                "# Netscape HTTP Cookie File",
                f"# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}",
                ""
            ]
            
            for cookie in session.cookies:
                # Formato: domain, domain_specified, path, secure, expires, name, value
                domain = cookie.domain if cookie.domain.startswith('.') else f'.{cookie.domain}'
                domain_specified = "TRUE" if cookie.domain_specified else "FALSE"
                path = cookie.path or "/"
                secure = "TRUE" if cookie.secure else "FALSE"
                expires = str(int(cookie.expires)) if cookie.expires else str(int(time.time()) + 31536000)
                
                cookie_line = f"{domain}\t{domain_specified}\t{path}\t{secure}\t{expires}\t{cookie.name}\t{cookie.value}"
                cookies_lines.append(cookie_line)
            
            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(cookies_lines))
                
            logger.info("Cookies actualizadas desde YouTube")
            return True
        else:
            logger.warning(f"Response code: {response.status_code}")
            return create_youtube_cookies()  # Fallback
            
    except Exception as e:
        logger.error(f"Error actualizando cookies: {e}")
        return create_youtube_cookies()  # Fallback

def ensure_cookies_exist():
    """Asegura que existan cookies válidas"""
    if not COOKIES_FILE.exists():
        logger.info("No hay cookies, creando nuevas...")
        return refresh_cookies()
    
    # Verificar si las cookies son muy antiguas (más de 24 horas)
    try:
        file_age = time.time() - COOKIES_FILE.stat().st_mtime
        if file_age > 86400:  # 24 horas
            logger.info("Cookies antiguas, actualizando...")
            return refresh_cookies()
    except:
        return refresh_cookies()
    
    return True

# Agregar estos endpoints a tu FastAPI app existente

@app.get("/api/cookies/status")
async def get_cookies_status():
    """Verifica el estado de las cookies"""
    try:
        exists = COOKIES_FILE.exists()
        if exists:
            stat = COOKIES_FILE.stat()
            age = time.time() - stat.st_mtime
            size = stat.st_size
            
            return {
                "exists": True,
                "file_size": size,
                "age_hours": round(age / 3600, 1),
                "path": str(COOKIES_FILE),
                "needs_refresh": age > 86400
            }
        else:
            return {
                "exists": False,
                "needs_refresh": True
            }
    except Exception as e:
        return {"error": str(e), "exists": False}

@app.post("/api/cookies/refresh")
async def refresh_cookies_endpoint():
    """Actualiza las cookies manualmente"""
    try:
        success = refresh_cookies()
        if success:
            return {
                "success": True,
                "message": "Cookies actualizadas correctamente",
                "file_path": str(COOKIES_FILE)
            }
        else:
            raise HTTPException(status_code=500, detail="Error actualizando cookies")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/api/cookies/clear")
async def clear_cookies():
    """Elimina las cookies existentes"""
    try:
        if COOKIES_FILE.exists():
            COOKIES_FILE.unlink()
            return {"success": True, "message": "Cookies eliminadas"}
        else:
            return {"success": True, "message": "No había cookies que eliminar"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Modificar tu función cleanup_old_files para incluir esto:
def ensure_cookies_on_startup():
    """Asegura que hay cookies al iniciar la aplicación"""
    logger.info("Verificando cookies al iniciar...")
    if ensure_cookies_exist():
        logger.info("Cookies listas")
    else:
        logger.warning("No se pudieron crear cookies, algunos videos podrían fallar")
        
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
ensure_cookies_on_startup() 

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
            'cookiefile': 'cookies/cookies.txt',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)

        if not info:
            raise HTTPException(status_code=400, detail="No se pudo obtener información del video")

        # Procesar formatos de video
        video_formats = []
        audio_formats = []
        seen_video = set()
        seen_audio = set()

        for fmt in info.get('formats', []):
            # Formatos de video (con audio)
            if fmt.get('vcodec') != 'none':
                height = fmt.get('height', 0)
                if height and height >= 144:  # Filtrar calidades muy bajas
                    quality = f"{height}p"
                    ext = fmt.get('ext', 'mp4')
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    fps = fmt.get('fps', 30)

                    format_key = f"{quality}_{ext}_{fps}"
                    if format_key not in seen_video:
                        video_formats.append({
                            'format_id': fmt['format_id'],
                            'quality': quality,
                            'ext': ext,
                            'filesize': filesize,
                            'fps': fps,
                            'note': fmt.get('format_note', ''),
                            'vcodec': fmt.get('vcodec', ''),
                            'acodec': fmt.get('acodec', ''),
                            'type': 'video'
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
                    if format_key not in seen_audio and len(audio_formats) < 5:
                        audio_formats.append({
                            'format_id': fmt['format_id'],
                            'quality': quality,
                            'ext': ext,
                            'filesize': filesize,
                            'abr': abr,
                            'acodec': fmt.get('acodec', ''),
                            'type': 'audio'
                        })
                        seen_audio.add(format_key)

        # Ordenar formatos
        video_formats.sort(key=lambda x: x.get('fps', 0), reverse=True)
        video_formats.sort(key=lambda x: int(x['quality'].replace('p', '')), reverse=True)
        audio_formats.sort(key=lambda x: x.get('abr', 0), reverse=True)

        # Procesar subtítulos
        subtitles = []
        if info.get('subtitles'):
            for lang, subs in info['subtitles'].items():
                if subs:  # Verificar que hay subtítulos disponibles
                    subtitles.append({
                        'lang': lang,
                        'name': lang.upper(),
                        'formats': [sub.get('ext', 'vtt') for sub in subs]
                    })

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
            'formats': video_formats[:10],  # Limitar a 10 formatos
            'audio_formats': audio_formats[:5],
            'subtitles': subtitles[:10]  # Limitar subtítulos
        }

        logger.info(f"Info obtenida: {len(video_formats)} formatos de video, {len(audio_formats)} de audio")
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

        # Opciones base de yt-dlp
        ydl_opts = {
            'format': request.format_id,
            'outtmpl': str(DOWNLOAD_DIR / filename_template),
            'progress_hooks': [progress_hook],
            'no_warnings': True,
            'cookiefile': 'cookies/cookies.txt',
        }

        # Configurar subtítulos
        if request.include_subtitles and request.subtitle_lang:
            ydl_opts.update({
                'writesubtitles': True,
                'subtitleslangs': [request.subtitle_lang],
                'subtitlesformat': 'vtt',
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
    port = int(os.environ.get("PORT", 8000))  
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
