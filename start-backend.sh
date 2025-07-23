#!/bin/bash
echo "🚀 Iniciando YouTube Downloader Backend..."
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo "🔥 Iniciando servidor FastAPI..."
python main.py
