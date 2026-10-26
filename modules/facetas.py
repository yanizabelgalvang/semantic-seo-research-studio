"""Agrupaciones exploratorias de consultas: lemas + TF-IDF + clustering, sin fingir intención SERP."""
import math
import re
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from .demanda import norm

STOP = set('a al algo ante bajo con contra como de del desde donde el ella en entre es esta este hay la las lo los mas mi mis o para por que se ser sin sobre su sus tu un una uno y ya mexico peru colombia argentina chile los las cual cuales donde cuando cuanto cuantos cuanto una uno mi tu su'.split())

def _lemmatize(text, nlp):
    doc=nlp(str(text))
    words=[]
    for t in doc:
        lemma=norm(t.lemma_ or t.text)
        if t.is_punct or t.is_space or t.is_stop or len(lemma)<3 or lemma in STOP:continue
        if re.fullmatch(r'[a-z0-9]+',lemma):words.append(lemma)
    return ' '.join(words)

def build(df, topic, nlp=None):
    """Devuelve filas y grupos; etiquetas son consultas representativas, NO clusters validados por SERP."""
    cols=['grupo','keywords','keywords_con_volumen','volumen_descriptivo','consultas_representativas']
    if df.empty:return pd.DataFrame(),pd.DataFrame(columns=cols)
    if nlp is None:
        from .spacy_nlp import model
        try: nlp=model()
        except OSError:
            import spacy
            nlp=spacy.blank("es")  # solo agrupación exploratoria; no reemplaza NER
    result=df.copy().reset_index(drop=True)
    # pipe permite procesar muchas consultas eficientemente.
    normalized=[]
    for doc in nlp.pipe(result.keyword.astype(str).tolist(),batch_size=128):
        words=[]
        for t in doc:
            lemma=norm(t.lemma_ or t.text)
            if not t.is_punct and not t.is_space and not t.is_stop and len(lemma)>2 and lemma not in STOP and re.fullmatch('[a-z0-9]+',lemma):words.append(lemma)
        normalized.append(' '.join(words))
    result['lemas']=normalized
    meaningful=[i for i,x in enumerate(normalized) if x.strip()]
    result['grupo']='Sin señal lingüística suficiente'
    if len(meaningful)>=6:
        texts=[normalized[i] for i in meaningful]
        tfidf=TfidfVectorizer(ngram_range=(1,2),min_df=2,max_df=0.9,sublinear_tf=True)
        try:
            X=tfidf.fit_transform(texts)
            k=min(16,max(3,round(math.sqrt(len(texts)/10))),len(texts)//3)
            if X.shape[1]<2 or k<2:raise ValueError('vocabulario insuficiente')
            model=MiniBatchKMeans(n_clusters=k,random_state=42,n_init=5,batch_size=256,max_iter=120)
            groups=model.fit_predict(X)
            for g in sorted(set(groups)):
                local=[j for j,v in enumerate(groups) if v==g]
                # Consulta central (cercanía al centro), evita etiquetar con un solo token.
                sims=X[local] @ model.cluster_centers_[g]
                import numpy as np
                best=local[int(np.asarray(sims).ravel().argmax())]
                label=f'Grupo {g+1}: {str(result.loc[meaningful[best],"keyword"])[:65]}'
                for j in local:result.loc[meaningful[j],'grupo']=label
        except ValueError:
            result.loc[meaningful,'grupo']='Agrupación no disponible'
    else:
        result.loc[meaningful,'grupo']='Muestra insuficiente para agrupar'
    result['relevancia_semilla']='por_revisar'
    topic_tokens=set(_lemmatize(topic,nlp).split())
    for i,text in enumerate(normalized):
        if topic_tokens and topic_tokens.intersection(text.split()):result.loc[i,'relevancia_semilla']='coincidencia_lexica'
    rows=[]
    for label,part in result.groupby('grupo',sort=False):
        positive=pd.to_numeric(part['volume'],errors='coerce')
        rows.append({'grupo':label,'keywords':len(part),'keywords_con_volumen':int(positive.gt(0).sum()),
                     'volumen_descriptivo':float(positive.fillna(0).sum()),
                     'consultas_representativas':' | '.join(part['keyword'].astype(str).head(3))})
    summary=pd.DataFrame(rows,columns=cols).sort_values('keywords',ascending=False)
    return result,summary
