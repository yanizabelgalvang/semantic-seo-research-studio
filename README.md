# Semantic SEO Research Studio — revisión de calidad

Prototipo de investigación, **no un generador de clusters SEO validados**.

## Cambios
- Agrupación heurística por intención explícita; consultas ambiguas permanecen «Intención por verificar».
- Wikidata: candidatos incompatibles con el contexto se descartan; los restantes requieren comprobación humana de propiedades.
- OpenAlex: descarta tipos no académicos y títulos comerciales evidentes; los restantes son candidatos pendientes de lectura.
- Exportación CSV de Semrush exclusivamente. No utiliza API de Semrush.

## Verificación
Ejecutar `python -m pytest -q`. La suite local no prueba conexiones en vivo.

## Seguridad
**La aplicación no tiene autenticación integrada.** No subir CSV confidenciales a un despliegue público. No incluir datos privados ni secretos en GitHub.

## Limitaciones actuales
Sin SERP real, sin clusters por similitud de resultados orgánicos, sin verificación definitiva de QIDs, sin revisión del texto completo de artículos OpenAlex. La etiqueta «Intención por verificar» es deliberada; no debe confundirse con un fallo de importación. Los totales de volumen no equivalen a tráfico potencial.

## Despliegue
`app.py` en raíz, `modules/` y `requirements.txt`. Para el modelo spaCy español, requirements incluye el wheel es_core_news_sm 3.8.0.
