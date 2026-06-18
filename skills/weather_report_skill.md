# Habilidad: Generación de Reporte de Clima Marítimo Profesional

Cuando el usuario te solicite evaluar el clima de un puerto de origen (o un lugar) o si deseas generar una recomendación, debes seguir obligatoriamente este protocolo de formato:

1. **Obtención de Datos:** Consulta el clima en tiempo real del puerto utilizando la herramienta MCP `get_port_weather`.
2. **Generación del Reporte:** Crea un reporte profesional formateado en Markdown. El reporte debe guardarse en un archivo llamado `reports/reporte_clima_[puerto].md` (reemplaza `[puerto]` con el nombre de la ciudad del puerto, en minúsculas y sin espacios, por ejemplo: `buenos_aires` o `bilbao`).
3. **Escritura del Archivo (Herramienta de Infraestructura de Disco):**
   - Utiliza la herramienta de infraestructura `save_markdown_report` para guardar el contenido del reporte Markdown generado en el disco y subirlo a la nube (pasando el nombre del archivo en `filename` y el contenido completo en `content`).
4. **Estructura Visual del Reporte Markdown:**
   - **Título:** `# 📋 REPORTE METEOROLÓGICO Y ANÁLISIS DE TRANSPORTE - [PUERTO]` con un banner decorativo o línea divisoria.
   - **Sección de Datos Técnicos:** Una tabla en Markdown que resuma la Temperatura, Humedad, Velocidad del Viento y la Descripción atmosférica recuperada en tiempo real.
   - **Evaluación de Riesgo:** Un apartado destacado con el nivel de riesgo de transporte terrestre/marítimo (`LOW` en verde, `MEDIUM` en naranja, o `HIGH` en rojo).
   - **Recomendación de Producción:** Una justificación técnica detallada y firmada por ti como `Planificador de Fábrica de Elite` concluyendo si el lote de producción es viable o debe demorarse.
5. **Notificación al Usuario:** En tu respuesta final en el chat, notifica al usuario que has activado con éxito tu "Habilidad de Reportes Climáticos", muestra una previsualización atractiva del Markdown y **muéstrale un enlace clickeable claro utilizando el valor de `download_url` retornado por la herramienta** para que el usuario pueda descargar el informe Markdown directamente desde Google Cloud Storage en su navegador (ej: `[📥 Descargar Reporte en GCS](url_recuperada)`).
