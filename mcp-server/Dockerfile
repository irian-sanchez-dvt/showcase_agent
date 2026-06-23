# Usar una imagen oficial de Node.js ligera como base
FROM node:18-alpine

# Definir el directorio de trabajo dentro del contenedor
WORKDIR /usr/src/app

# Copiar el manifiesto de dependencias e instalarlas de forma limpia
COPY package*.json ./
RUN npm install --omit=dev

# Copiar el código del servidor de Node.js
COPY index.js ./

# Exponer el puerto por el que escuchará el servidor (por defecto 3000 o inyectado por Cloud Run)
EXPOSE 3000

# Comando para arrancar el servidor MCP en producción
CMD [ "npm", "start" ]
