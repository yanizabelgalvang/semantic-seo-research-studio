# Semantic SEO Research Studio — entrega Excel + PDF

Aplicación Streamlit con datos de demanda exclusivamente desde CSV de Semrush.

**Dos entregables separados:** (1) Excel completo con resumen y hojas de datos; (2) PDF editorial con brief preliminar y propuestas de arquitectura de URLs. La SERP y competidores son opcionales.

**Avisos:** la app aún no tiene acceso privado implementado. No cargues datos confidenciales en una URL pública. Los clusters, QIDs y publicaciones académicas siguen siendo candidatos y no se anuncian como verificados. Las URLs propuestas son hipótesis hasta analizar el sitio existente.

Para desplegar: subir el contenido a la raíz de GitHub; revisar los logs de instalación. El Excel se genera con `openpyxl`, disponible públicamente en PyPI.

## Corrección de despliegue
Se reemplazó `artifact-tool` por `openpyxl` y se añadió la importación faltante de los generadores Excel/PDF en `app.py`. La privacidad para 3 usuarios sigue pendiente; no cargar datos sensibles en una app pública.
