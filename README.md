# Semantic SEO Research Studio — actualización del motor semántico

Aplicación exploratoria Streamlit. Fuente de demanda: **solo CSV manuales de Semrush**. Selección de países hispanohablantes de Latinoamérica. Incluye análisis lingüístico con spaCy, corpus Wikipedia, candidatos Wikidata y recuperación de metadatos OpenAlex.

## Cambios

- `modules/facetas.py`: grupos exploratorios basados en lemas spaCy + TF-IDF y MiniBatchKMeans. Las etiquetas proceden de consultas representativas, **no son clusters SEO validados por SERP**. Se mantiene el volumen agregado solo como descripción, no como tráfico esperado.
- `modules/spacy_nlp.py`: filtros conservadores para algunos falsos positivos; las entidades siguen pendientes de revisión.
- `modules/wikidata.py`: ranking contextual de candidatos, manejo de 429 y reintentos. Ningún QID se declara verificado automáticamente.
- `modules/openalex.py`: distingue artículos académicos candidatos, coincidencias parciales y resultados descartados según tipo y metadatos. No valida contenido académico.
- `app.py`: mensajes y advertencias acordes con las limitaciones.
- `requirements.txt`: scikit-learn; se conserva el modelo spaCy español.

## Instalar localmente (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Pruebas

```powershell
python -m pytest -q
```

Las pruebas requieren `pytest` (instalar con `python -m pip install pytest`). Las 7 pruebas se ejecutaron en el entorno de desarrollo; el modelo `es_core_news_sm` no estaba instalado en ese entorno, por lo que la prueba de agrupación utiliza un pipeline español básico. En Streamlit Cloud se instala mediante `requirements.txt`.

## Despliegue

Subir el contenido de esta carpeta a la **raíz** del repositorio, conservando `modules/`, `tests/`, `.streamlit/` y `requirements.txt`. Streamlit Cloud usa `app.py` en la rama `main`. No cargar datos confidenciales hasta disponer de control de acceso comprobado. Un repositorio público y una app sin autenticación **no** constituyen una plataforma privada.

## Límites

- No incluye análisis SERP, clustering editorial validado, diagnóstico de canibalización ni decisiones sobre URLs.
- La relevancia de entidades y trabajos científicos sigue requiriendo revisión.
- La clasificación automática es exploratoria; se deben examinar las consultas representativas.
- Las APIs públicas pueden devolver errores o aplicar límites; las llamadas en vivo desde Streamlit Cloud aún deben comprobarse.
