# Usar una imagen base ligera de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar primero los requirements para aprovechar el cache
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de archivos del proyecto
COPY . .

# Exponer el puerto que Flask usará (Railway lo detecta)
EXPOSE 5001

# Establecer la variable de entorno para producción
ENV FLASK_ENV=production

# Comando de inicio del servidor Flask
CMD ["python", "app.py"]
