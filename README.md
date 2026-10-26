# Semantic SEO Research Studio — prototipo 0.1

Prototipo con 4 módulos Python + interfaz Streamlit. Fuente de demanda: **solo CSV manual de Semrush**, sin API de pago.

## Seguridad

**Esta versión NO tiene login ni almacenamiento persistente. NO desplegar públicamente ni cargar datos confidenciales en un despliegue abierto.** GitHub privado no protege por sí solo una aplicación web desplegada. El acceso privado con Google para tres usuarios y el almacenamiento persistente gratuito son una fase posterior, sujeta a verificar compatibilidad y límites del proveedor.

## Ejecutar localmente en Windows (PowerShell)

Recomendado Python 3.11 o 3.12:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download es_core_news_sm
streamlit run app.py
```

Abre http://localhost:8501 si no se abre automáticamente.

## Flujo

1. Selecciona país hispanohablante y escribe tema.
2. Adjunta uno o más CSV de Semrush Keyword Magic Tool.
3. Confirma manualmente que el país de los CSV coincide con el elegido.
4. Ejecuta NLP: descarga extractos de Wikipedia, usa spaCy para entidades y sintagmas, busca candidatos en Wikidata y literatura en OpenAlex.
5. Descarga CSV y ZIP con resultados.

## Limitaciones explícitas

- Prototipo de las cuatro capas; **no** es una reproducción completa de la metodología del artículo.
- Los QIDs de Wikidata son **candidatos**; requieren desambiguación antes de presentarse como verificados.
- No incluye SERP, corpus de competidores, jerarquía académica profunda, cruce completo facetas × demanda, scoring SEO ni briefs.
- Si el CSV no contiene país, el usuario debe confirmarlo. Las métricas de Semrush son estimaciones.
- Las consultas a Wikipedia, Wikidata y OpenAlex dependen de red y pueden tener límites.
- No hay persistencia en servidor: descarga tus resultados.
- Los archivos de origen no se incluyen en el ZIP generado; guarda tus exportaciones originales.

## Siguientes fases

1. Validar importación con un CSV real de Semrush (sin subirlo a GitHub).
2. Mejorar corpus, desambiguación y cruce facetas × demanda.
3. Incorporar Google OpenID Connect con allowlist de tres correos, almacenamiento privado y controles de acceso a datos.
4. Desplegar en un alojamiento que soporte privacidad, memoria para spaCy y cuotas gratuitas verificadas.
