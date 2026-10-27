import pandas as pd
from modules.facetas import build
from modules.wikidata import lookup
from modules.openalex import score_work

def test_intent_not_conflated():
    df=pd.DataFrame({'keyword':['agencia seo mexico','precio posicionamiento web','como posicionar una pagina web','como posicionar tu web en google','que es seo'],'volume':[100,80,50,40,200]})
    detail,summary=build(df,'posicionamiento web')
    assert detail.loc[0,'grupo']=='Contratación y servicios'
    assert detail.loc[1,'grupo']=='Precios y comparación'
    assert detail.loc[2,'grupo']==detail.loc[3,'grupo']=='Procedimientos y estrategias'
    assert detail.loc[4,'grupo']=='Conceptos y definiciones'
    assert detail['intencion_validada_serp'].eq(False).all()

def test_wikidata_rejects_unrelated(monkeypatch):
    import modules.wikidata as wd
    monkeypatch.setattr(wd,'_search',lambda term:([{'id':'Q1','label':'Seo','description':'catedral en Zaragoza'}, {'id':'Q2','label':'SEO','description':'optimización en buscadores web'}],'ok'))
    x=lookup(['SEO'],'posicionamiento web seo')
    assert x.iloc[0].estado=='descartado_fuera_contexto'
    assert x.iloc[1].estado=='candidato_contextual'

def test_openalex_rejects_commercial():
    assert score_work({'display_name':'Servicios Posicionamiento Web Mallorca','type':'article'},'posicionamiento web','posicionamiento web')[1]=='descartado'
    assert score_work({'display_name':'Marketing digital','type':'webpage'},'marketing digital','marketing')[1]=='descartado'
