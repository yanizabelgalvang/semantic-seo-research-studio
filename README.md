# Semantic SEO Research Studio — investigación semántica

Aplicación Streamlit para **CSV manuales de Semrush**, Python/spaCy, Wikipedia, Wikidata y OpenAlex. **SERP y competidores opcionales**; no son requisito del núcleo de cuatro capas.

## Instalación

`pip install -r requirements.txt` y `streamlit run app.py`.

## Alcance y límites

La investigación ofrece facetas e hipótesis; no sustituye el análisis de intención y de resultados de búsqueda para decidir URLs. Wikidata y OpenAlex pueden devolver candidatos ambiguos. El reporte ejecutivo evita incluir textos completos de terceros. Los CSV completos se mantienen como respaldo.

## Privacidad

**No se ha implementado autenticación.** No subas CSV confidenciales ni publiques la app como herramienta privada para el equipo hasta protegerla con acceso autorizado.
