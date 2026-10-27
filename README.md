# Semantic SEO Research Studio — flujo de 10 pasos

Aplicación Streamlit experimental, sin APIs de pago de Semrush. Investigación en español para países hispanohablantes de Latinoamérica.

## Entradas
1. Consulta semilla y país.
2. CSV **Keywords** de Semrush Keyword Magic Tool (obligatorio).
3. CSV **Questions** de Semrush Keyword Magic Tool (obligatorio).
4. Sitemap XML/XML.GZ (recomendado; opcional para investigación, necesario para localizar URLs existentes).

No requiere exportación SERP ni análisis de competidores. La SERP puede utilizarse posteriormente como validación adicional de intención y canibalización, sin ser parte obligatoria del flujo de cuatro capas.

## Método
- Corpus contextual de Wikipedia y registro de fuentes descartadas.
- spaCy: entidades, lemas y sintagmas nominales.
- Wikidata: búsqueda de QIDs; el usuario puede aprobar o descartar candidatos. **Aprobar no sustituye la comprobación de propiedades y fuente**.
- OpenAlex: dominio, campo, subcampo y tema cuando están disponibles; publicaciones sin lectura del texto permanecen pendientes.
- Facetas × demanda: keywords y preguntas observadas diferenciadas, volúmenes descriptivos sin equipararlos a tráfico.
- Arquitectura: propuesta de PAI + candidatos de clúster, comparación léxica con sitemap; no es auditoría de contenido ni decisión definitiva de crear URLs.
- Brief: tabla **Bloque / Qué desarrolla / De dónde sale**, con enlaces de procedencia y estados de revisión. Sin redacción completa ni promesas de ranking.

## Entregables
- XLSX con pestañas de datos y matriz de brief.
- PDF independiente con mapa de páginas y tabla de encabezados con evidencia.
- ZIP técnico con CSV.

## Instalación
Usa Python 3.11 y `pip install -r requirements.txt`, luego `streamlit run app.py`.

## Seguridad
**Esta aplicación NO incluye autenticación.** Un repositorio privado no garantiza que el despliegue sea privado. No cargar CSV confidenciales en un despliegue público. Antes de uso real por tres personas, implementar y verificar control de acceso Google/OIDC y permisos de almacenamiento.

## Limitaciones conocidas
- La selección del corpus y los modelos de spaCy pueden producir falsos positivos.
- El análisis OpenAlex por metadatos no equivale a validar académicamente los artículos.
- El sitemap no indica títulos, H1, contenido ni canibalización; los índices de sitemap requieren descargar los XML hijos por separado.
- Las facetas son propuestas lingüísticas, no clusters finales por intención SERP.
- La revisión de QIDs es una decisión humana explícita y debe basarse en comprobación real.
- La arquitectura y los briefs son **borradores basados en evidencia disponible**, no sustituyen revisión SEO/editorial.

## Pruebas
`python -m pytest -q` (16 pruebas locales, incluidas generación XLSX y PDF; sin validación de APIs en vivo).


## Inventario de URLs en CSV
La aplicación acepta CSV de extractores de sitemap, XML y XML.GZ. Para CSV se requiere una columna `url` (también `loc`, `Address`, `Dirección`); reconoce `source`, `lastmod`, `changefreq` y `priority` como opcionales. El CSV se procesa sin llamadas a APIs de Semrush. El importador conserva URLs únicas HTTP/HTTPS y no interpreta la ausencia de una URL como prueba de que no existe. Los índices XML de sitemaps requieren exportar los sitemaps hijos o el CSV consolidado.
