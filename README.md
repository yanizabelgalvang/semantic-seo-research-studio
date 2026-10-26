# Semantic SEO Research Studio — revisión técnica

Aplicación exploratoria Streamlit con **CSV manual de Semrush**, análisis lingüístico con spaCy, corpus Wikipedia, búsqueda de candidatos Wikidata y publicaciones OpenAlex.

## Limitaciones honestas
- **No es todavía un sistema SEO profesional completo**: no analiza SERP, competidores ni clusters editoriales validados.
- Wikidata muestra candidatos **no verificados**; OpenAlex muestra publicaciones **pendientes de revisión**.
- Las facetas son provisionales, derivadas de términos del CSV, no categorías definitivas ni predicciones de tráfico.
- **No hay autenticación.** No cargar CSV confidenciales en un despliegue público. GitHub privado no protege por sí mismo la URL de Streamlit.

## Despliegue
Subir el contenido de esta carpeta a la raíz del repositorio. Seleccionar `app.py` como entrada y Python 3.11. `requirements.txt` instala spaCy y el modelo español. Las consultas abiertas pueden sufrir bloqueos y límites de uso.

## Pruebas
`python -m unittest discover -s tests -v` (sin red). Para probar en local: `pip install -r requirements.txt` y `streamlit run app.py`.
