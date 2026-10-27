import io
import pandas as pd
from modules.competidores import read_serp_csv
from modules.quality import curate_sources,curate_entities,research_status

def test_serp_import():
    df=read_serp_csv('URL,Position,Title\nhttps://example.org/a,1,Ejemplo\nhttps://example.org/a,2,Duplicado\ninvalid,3,Mal\n')
    assert len(df)==1 and df.iloc[0].posicion=='1'

def test_source_ambiguity():
    df=curate_sources(pd.DataFrame([{'titulo':'Anillo web'},{'titulo':'Posicionamiento en buscadores'}]),'posicionamiento web')
    assert df.revision_tematica.tolist()==['excluir_ambiguedad','pertinente']

def test_ner_noise():
    df=curate_entities(pd.DataFrame({'entidad':['Usualmente están','Google']}))
    assert df.revision_nlp.tolist()==['descartar_ruido','candidato']

def test_no_claims_of_verification():
    state=research_status(pd.DataFrame(),pd.DataFrame(),pd.DataFrame(),pd.DataFrame())
    assert state['serp']=='no_aportada' and state['wikidata']=='sin_ejecutar'
