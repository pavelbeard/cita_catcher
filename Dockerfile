# Usa Python 3.12 como base
FROM ultrafunk/undetected-chromedriver

# Crea un directorio de trabajo
WORKDIR /app

# Copia los archivos del proyecto al contenedor
COPY ./src .
COPY reqs.txt .

# Instala las dependencias de Python
RUN pip install --upgrade pip \
    && pip install -r reqs.txt

# Comando por defecto
CMD ["python", "-m", "main"]