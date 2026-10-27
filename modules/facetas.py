"""Agrupación de consultas por necesidad expresada, con subtemas exploratorios.
No sustituye un clustering basado en SERP ni verifica intención de búsqueda.
"""
import re
import unicodedata
import pandas as pd
from .demanda import norm

STOP = {'de','del','en','el','la','los','las','un','una','para','por','con','como','que','mi','tu','su','al','y','a','es','se','mexico','peru'}

def tokens(text):
    return {w for w in norm(text).split() if len(w)>2 and w not in STOP}

def intent_bucket(keyword):
    s=' '+norm(keyword)+' '
    # Prioridad explícita: la intención de contratar debe prevalecer sobre menciones generales.
    if re.search(r'\b(agencia|agencias|servicio|servicios|consultor|consultoria|experto|expertos|contratar|empresa seo|empresas seo|presupuesto|cotizacion|cotizar)\b',s):
        return 'Contratación y servicios'
    if re.search(r'\b(precio|precios|costo|costos|cuanto cuesta|tarifa|tarifas|barato|economico)\b',s):
        return 'Precios y comparación'
    if re.search(r'\b(curso|cursos|aprender|formacion|certificacion|capacitacion|tutorial)\b',s):
        return 'Aprendizaje y formación'
    if re.search(r'\b(herramienta|herramientas|software|programa|plugin|plugins|auditoria|analitica|search console|semrush)\b',s):
        return 'Herramientas y medición'
    if re.search(r'\b(local|cerca de mi|mapas|google maps|tijuana|monterrey|guadalajara|cdmx|ciudad de mexico)\b',s):
        return 'Búsqueda local'
    if re.search(r'\b(como|paso a paso|guia|consejos|estrategia|estrategias|mejorar|optimizar|posicionar)\b',s):
        return 'Procedimientos y estrategias'
    if re.search(r'\b(que es|significado|definicion|concepto|para que sirve|ejemplos)\b',s):
        return 'Conceptos y definiciones'
    return 'Intención por verificar'

def build(df, topic, nlp=None):
    cols=['grupo','keywords','keywords_con_volumen','volumen_descriptivo','consultas_representativas','advertencia']
    if df.empty:return pd.DataFrame(),pd.DataFrame(columns=cols)
    out=df.copy().reset_index(drop=True)
    seed=tokens(topic)
    # Sinónimos derivados del contexto, solo para relevancia, no para imponer un cluster.
    aliases={'seo','posicionamiento','buscador','buscadores','web','google','search engine optimization'} if seed & {'seo','posicionamiento','web'} else set()
    relevant=seed|aliases
    out['relevancia_semilla']=out.keyword.map(lambda x:'coincidencia_lexica' if tokens(x)&relevant else 'requiere_revision')
    out['grupo']=out.keyword.map(intent_bucket)
    out['intencion_validada_serp']=False
    # Etiquetas de necesidad son explicables; el resto se conserva para revisión humana.
    rows=[]
    for group,part in out.groupby('grupo',sort=False):
        volume=pd.to_numeric(part['volume'],errors='coerce')
        top=part.assign(_v=volume.fillna(-1)).sort_values('_v',ascending=False)
        rows.append({'grupo':group,'keywords':len(part),'keywords_con_volumen':int(volume.gt(0).sum()),
                     'volumen_descriptivo':float(volume.fillna(0).sum()),
                     'consultas_representativas':' | '.join(top.keyword.astype(str).head(4)),
                     'advertencia':'Agrupación heurística; requiere SERP para validar URLs'})
    return out,pd.DataFrame(rows,columns=cols).sort_values('keywords',ascending=False)
