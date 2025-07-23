#!/bin/bash
echo "🚀 Iniciando YouTube Downloader completo..."

# Función para matar procesos al salir
cleanup() {
    echo "🛑 Deteniendo servidores..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Iniciar backend
echo "📡 Iniciando backend..."
cd backend
pip install -r requirements.txt > /dev/null 2>&1
python main.py &
BACKEND_PID=$!
cd ..

# Esperar un poco para que el backend inicie
sleep 3

# Iniciar frontend
echo "🌐 Iniciando frontend..."
cd frontend
npm install > /dev/null 2>&1
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Servidores iniciados:"
echo "   📡 Backend: http://localhost:8000"
echo "   🌐 Frontend: http://localhost:3000"
echo "   📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Presiona Ctrl+C para detener ambos servidores"

# Esperar a que terminen los procesos
wait
