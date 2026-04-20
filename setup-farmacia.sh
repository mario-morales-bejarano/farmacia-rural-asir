#!/bin/bash

# ==============================================================================
# Script de Despliegue Automático - Sistema Kiosko Farmacia Rural
# Descripción: Automatiza la instalación de dependencias, entorno virtual y permisos.
# ==============================================================================

# Salir inmediatamente si algún comando falla
set -e

# Definición de colores para los mensajes de consola
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Definición del usuario del sistema y directorios
SYS_USER="farmacia-santaeufemia"
PROJECT_DIR="/home/$SYS_USER/proyecto_farmacia"
BACKUP_DIR="/home/$SYS_USER/backups"

echo -e "${YELLOW}[*] Iniciando el despliegue automatizado del Sistema Farmacia...${NC}"

# 1. Actualización del sistema
echo -e "${YELLOW}[1/5] Actualizando repositorios y paquetes del sistema operativo...${NC}"
sudo apt-get update -y
sudo apt-get upgrade -y

# 2. Instalación de dependencias del sistema
echo -e "${YELLOW}[2/5] Instalando dependencias base (Python3, MariaDB, UFW)...${NC}"
sudo apt-get install -y python3 python3-venv python3-pip mariadb-server ufw gzip tar

# 3. Creación de directorios y asignación de permisos
echo -e "${YELLOW}[3/5] Configurando directorios y permisos de seguridad...${NC}"
mkdir -p "$PROJECT_DIR"
mkdir -p "$BACKUP_DIR"

# Asignar propiedad al usuario dedicado y permisos restrictivos
sudo chown -R $SYS_USER:$SYS_USER "$PROJECT_DIR"
sudo chown -R $SYS_USER:$SYS_USER "$BACKUP_DIR"
sudo chmod 755 "$PROJECT_DIR"
sudo chmod 700 "$BACKUP_DIR" # Máxima restricción para backups

# 4. Configuración del Entorno Virtual de Python
echo -e "${YELLOW}[4/5] Creando entorno virtual de Python (venv)...${NC}"
cd "$PROJECT_DIR"
python3 -m venv venv

# 5. Instalación de librerías de Python dentro del venv
echo -e "${YELLOW}[5/5] Instalando dependencias de la aplicación (Flask, Gunicorn)...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install flask gunicorn mysql-connector-python
deactivate

echo -e "${GREEN}[✔] ¡Despliegue completado con éxito!${NC}"
echo -e "${GREEN}El entorno virtual y las dependencias están listas en: $PROJECT_DIR${NC}"
