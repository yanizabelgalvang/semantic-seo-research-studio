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

## Actualización: evidencia SERP y competidores

- El usuario puede adjuntar un CSV SERP con columna `URL` y opcionalmente `Position`, `Title`, `Query`. No se llama a APIs de pago.
- El sistema conserva la SERP como **aportada por el usuario, no verificada de forma independiente**.
- Se intenta recuperar el contenido de hasta cinco páginas HTML. Bloqueos, captchas o contenido insuficiente se registran y no se inventa texto.
- Wikipedia: se identifican páginas ambiguas, sin afirmar que el resto está verificado automáticamente.
- spaCy: entidades ruidosas conocidas se etiquetan para descarte; las demás siguen siendo candidatos.
- Wikidata y OpenAlex: candidatos, no confirmación científica o de identidad. La validación definitiva requiere inspeccionar fuentes y propiedades.
- No hay clustering validado por coincidencia de SERP, porque el CSV puede contener una sola consulta. Los grupos son hipótesis.
- La aplicación **no tiene autenticación**. No cargar CSV confidenciales mientras el acceso sea público.

### Ejemplo CSV SERP

```csv
URL,Position,Title,Query
https://example.org/articulo,1,Título de ejemplo,posicionamiento web
```

## Validación

`python -m pytest -q` (14 pruebas locales aprobadas en la entrega).
