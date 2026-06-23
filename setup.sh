#!/bin/bash
# ===========================================================================
# SCRIPT DE CONFIGURACIÓN PARA CLOUD SHELL EDITOR (factory-planner boilerplate)
# ===========================================================================
# Este script inicializa el entorno de desarrollo para los asistentes del taller.
# Instala 'uv', el 'google-agents-cli', configura credenciales
# y sincroniza todas las dependencias de Python.

set -e # Salir inmediatamente si algún comando falla (retorna un código distinto de cero).

echo "🚀 Iniciando la configuración del entorno para Cloud Shell..."

# 1. Instalar 'uv' (Gestor de paquetes moderno de Python)
if ! command -v uv &> /dev/null; then
    echo "📦 Instalando el gestor de paquetes 'uv'..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Cargar el entorno de uv para que esté disponible inmediatamente en este script
    source "$HOME/.local/bin/env"
else
    echo "✅ 'uv' ya está instalado."
fi

# Asegurar que uv esté en el PATH para el resto del script
export PATH="$HOME/.local/bin:$PATH"

# 2. Instalar 'google-agents-cli'
echo "🛠️ Instalando 'google-agents-cli'..."
uv tool install google-agents-cli --force

# 3. Copiar plantilla de variables de entorno
if [ ! -f .env ]; then
    echo "📝 Creando el archivo '.env' a partir de '.env.example'..."
    cp .env.example .env
    echo "⚠️  ¡Recuerda actualizar el archivo '.env' con tus configuraciones reales de Google Cloud!"
else
    echo "✅ El archivo '.env' ya existe."
fi

# 4. Sincronizar dependencias de Python utilizando el CLI oficial
echo "🐍 Instalando dependencias de Python del proyecto con 'agents-cli install'..."
agents-cli install

# 5. Autenticación de Credenciales por Defecto de GCP (ADC)
echo "🔐 Configurando las credenciales de Google Cloud..."
echo "Por favor, sigue las instrucciones a continuación para iniciar sesión en tu cuenta de Google Cloud."
echo "Esto es necesario para conectarte a los reasoning engines y servicios de GCS."
gcloud auth application-default login --no-launch-browser

echo ""
echo "==========================================================================="
echo "🎉 ¡CONFIGURACIÓN COMPLETADA CON ÉXITO!"
echo "==========================================================================="
echo "Para activar tu entorno virtual y comenzar a trabajar, ejecuta:"
echo "  source .venv/bin/activate"
echo ""
echo "Para probar tu agente de manera local, puedes usar el playground:"
echo "  agents-cli playground"
echo "==========================================================================="
