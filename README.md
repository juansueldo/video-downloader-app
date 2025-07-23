# 🎬 YouTube Downloader - Demo Completo

Una aplicación web moderna y completa para descargar videos de YouTube con opciones avanzadas.

## ✨ Características

- 🎥 **Múltiples calidades**: Desde 144p hasta 4K
- 🎵 **Solo audio**: Extracción de MP3 de alta calidad
- 📝 **Subtítulos**: Descarga en múltiples idiomas
- 📊 **Progreso en tiempo real**: Visualización del progreso de descarga
- 🎨 **Interfaz moderna**: Diseño responsivo con Tailwind CSS
- ⚡ **API robusta**: FastAPI con manejo de errores
- 🔄 **Limpieza automática**: Eliminación de archivos temporales

## 🚀 Inicio Rápido

### Opción 1: Script automático (Recomendado)
```bash
chmod +x start-all.sh
./start-all.sh
```

### Opción 2: Manual

#### Backend (Terminal 1)
```bash
cd backend
pip install -r requirements.txt
python main.py
```

#### Frontend (Terminal 2)
```bash
cd frontend
npm install
npm run dev
```

## 🌐 URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

## 📱 Uso

1. **Pega la URL** del video de YouTube
2. **Haz clic en "Analizar"** para obtener opciones
3. **Selecciona calidad, audio y subtítulos**
4. **Haz clic en "Descargar"**
5. **Observa el progreso** en tiempo real
6. **El archivo se descarga automáticamente**

## 🛠️ Tecnologías

### Frontend
- **Next.js 14** - Framework React
- **TypeScript** - Tipado estático
- **Tailwind CSS** - Estilos utilitarios
- **Axios** - Cliente HTTP
- **Lucide React** - Iconos

### Backend
- **FastAPI** - Framework web moderno
- **yt-dlp** - Descargador de videos
- **Uvicorn** - Servidor ASGI
- **Pydantic** - Validación de datos

## 📁 Estructura del Proyecto

```
youtube-downloader-demo/
├── backend/
│   ├── main.py              # Servidor FastAPI
│   ├── requirements.txt     # Dependencias Python
│   └── downloads/           # Archivos temporales
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css  # Estilos globales
│   │   │   ├── layout.tsx   # Layout principal
│   │   │   └── page.tsx     # Página principal
│   │   └── components/
│   │       └── VideoDownloader.tsx  # Componente principal
│   ├── package.json         # Dependencias Node.js
│   ├── tailwind.config.js   # Configuración Tailwind
│   ├── tsconfig.json        # Configuración TypeScript
│   └── next.config.js       # Configuración Next.js
├── start-all.sh             # Script de inicio automático
├── start-backend.sh         # Script solo backend
├── start-frontend.sh        # Script solo frontend
└── README.md               # Este archivo
```

## 🔧 Configuración Avanzada

### Variables de Entorno

Crea un archivo `.env.local` en el frontend:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Configuración de Producción

Para desplegar en producción, actualiza:
- `API_BASE` en `VideoDownloader.tsx`
- CORS origins en `main.py`
- Configuración de Next.js para tu dominio

## 🐛 Solución de Problemas

### Error: "yt-dlp not found"
```bash
pip install --upgrade yt-dlp
```

### Error: "Port already in use"
```bash
# Cambiar puerto del backend en main.py
uvicorn.run(app, host="0.0.0.0", port=8001)

# Cambiar puerto del frontend
npm run dev -- -p 3001
```

### Error: "CORS policy"
Verifica que el backend esté ejecutándose en el puerto correcto y que CORS esté configurado.

## ⚠️ Consideraciones Legales

- **Solo uso personal**: Esta herramienta es para uso educativo y personal
- **Respeta los derechos de autor**: No descargues contenido protegido sin permiso
- **Términos de servicio**: El uso puede violar los términos de YouTube
- **Responsabilidad**: Usa bajo tu propia responsabilidad

## 🤝 Contribuciones

Las contribuciones son bienvenidas:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es solo para fines educativos. Úsalo responsablemente.

## 🆘 Soporte

Si encuentras problemas:

1. Verifica que ambos servidores estén ejecutándose
2. Revisa la consola del navegador para errores
3. Verifica los logs del backend
4. Asegúrate de tener las dependencias instaladas

---

**¡Disfruta descargando videos de YouTube de manera fácil y rápida! 🎉**
