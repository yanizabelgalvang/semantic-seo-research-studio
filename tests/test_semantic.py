import io
import os
import sys
import zipfile
import pandas as pd
import spacy
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from modules.facetas import build
from modules.openalex import score_work
from modules.wikidata import lookup

def test_clustering_generic():
    words=['comprar usdt en peru','donde comprar usdt','comprar tether','precio usdt hoy','cotizacion de usdt','cambiar usdt a soles','vender usdt peru','como vender tether','retiro de usdt','wallet usdt segura','billetera usdt','custodia de usdt']
    df=pd.DataFrame({'keyword':words,'volume':[10]*len(words)})
    d,s=build(df,'usdt',nlp=spacy.blank('es'))
    assert len(d)==len(df) and s.keywords.sum()==len(df)
    assert len(s)>=2
    assert not any(x.startswith('Subtema: pagina') for x in s.grupo)

def test_openalex_rejects_unrelated():
    w={'display_name':'Posicionamiento web en Mallorca','type':'webpage','primary_topic':{'display_name':'Travel'}}
    assert score_work(w,'posicionamiento web','posicionamiento web')[1]=='descartado'

def test_openalex_accepted_is_still_candidate():
    w={'display_name':'Search engine optimization and posicionamiento web','type':'article','primary_topic':{'display_name':'Search engines'}}
    assert score_work(w,'posicionamiento web','posicionamiento web')[1]=='candidato_revisar'

def test_real_export_if_present():
    path='/mnt/data/semantic_research (1).zip'
    if not os.path.exists(path):return
    with zipfile.ZipFile(path) as z:df=pd.read_csv(io.BytesIO(z.read('keywords.csv')))
    detail,summary=build(df,'posicionamiento web',nlp=spacy.blank('es'))
    assert len(detail)==len(df)
    assert summary.keywords.sum()==len(df)
    assert len(summary)>=3
