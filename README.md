# Semantic SEO Research Studio — Prototipo 0.2

Aplicación exploratoria con Streamlit para CSV manuales de Semrush y análisis de Wikipedia contextual, spaCy, Wikidata y OpenAlex.

## Despliegue

Subir el contenido de esta carpeta a la **raíz** del repositorio GitHub (reemplazar app.py, requirements.txt y modules/). En Streamlit Community Cloud usar `main` y `app.py`, preferentemente Python 3.11. El modelo `es_core_news_sm` se instala desde requirements.txt.

## Qué se corrigió

- Wikipedia: búsqueda contextual y rechazo de desambiguaciones obvias como "La Seo" (catedral) para temas SEO.
- spaCy: resultados separados y exclusión de ruido claramente ajeno.
- Wikidata: menos solicitudes, caché y reintentos ante 429; resultados **candidatos**, no QIDs confirmados.
- OpenAlex: identificadores, estado y pertinencia por revisar, sin atribuir validación científica.
- Facetas: cruce exploratorio de keywords con familias de conceptos; NO estima tráfico.
- Descarga: Markdown y ZIP con resultados y limitaciones.

## Seguridad

**Esta versión NO tiene autenticación.** No subir CSV confidenciales en despliegues públicos. Para uso de tres personas con Google Login debe añadirse una solución real de autenticación y control de acceso antes de tratar datos privados. No almacenar secretos en GitHub.

## Limitaciones

No implementa todavía clustering SEO basado en SERP, verificación automática de entidades Wikidata ni evaluación científica completa. La selección de Wikipedia está especialmente afinada para consultas de SEO; otros sectores pueden requerir vocabulario contextual específico. Las APIs abiertas pueden bloquear o limitar solicitudes y esos errores se muestran en las tablas.
