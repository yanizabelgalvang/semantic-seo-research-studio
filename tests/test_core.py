import io,unittest
import pandas as pd
from modules.demanda import load_semrush,number
from modules.facetas import build
class Uploaded:
    name='semrush.csv'
    def __init__(self,data):self.data=data.encode()
    def getvalue(self):return self.data
class Tests(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(number('1.234,50'),1234.5)
        self.assertEqual(number('1,234.50'),1234.5)
        self.assertTrue(pd.isna(number('N/A')))
    def test_import(self):
        df=load_semrush([Uploaded('Keyword,Volume,KD %,Intent,CPC\nseo,100,50,I,0.3\nseo,100,50,I,0.3\nposicionamiento web,0,,I,0')])
        self.assertEqual(len(df),2)
        self.assertEqual(int(df.volume.eq(0).sum()),1)
        self.assertEqual(int(df.volume.isna().sum()),0)
    def test_facets_are_generic(self):
        df=load_semrush([Uploaded('Keyword,Volume\ncomprar usdt,100\ncomprar bitcoin,80\nvender bitcoin,50\nvender usdt,40')])
        detail,summary=build(df,'comprar criptomonedas')
        self.assertEqual(len(detail),4)
        self.assertEqual(summary.keywords.sum(),4)
if __name__=='__main__':unittest.main()
