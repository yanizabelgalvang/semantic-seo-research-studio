import unittest, io, csv, gzip
from modules.architecture import parse_sitemap

class TestSitemapCSV(unittest.TestCase):
    def test_extractor_columns(self):
        data=b'url,source,lastmod,changefreq,priority\nhttps://example.org/a,https://example.org/page-sitemap.xml,2026-10-26,,\n'
        df=parse_sitemap(data,'sitemap-urls.csv')
        self.assertEqual(len(df),1)
        self.assertEqual(df.iloc[0]['origen'],'csv_usuario')
        self.assertTrue(df.iloc[0]['source'].endswith('.xml'))
    def test_semicolon_and_duplicates(self):
        data=b'Address;lastmod\nhttps://example.org/a;2026-01-01\nhttps://example.org/a;2026-01-01\nnot-a-url;\n'
        df=parse_sitemap(data,'urls.csv')
        self.assertEqual(len(df),1)
        self.assertEqual(df.iloc[0]['lastmod'],'2026-01-01')
    def test_xml(self):
        xml=b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.org/</loc></url></urlset>'
        self.assertEqual(len(parse_sitemap(xml,'sitemap.xml')),1)
        self.assertEqual(len(parse_sitemap(gzip.compress(xml),'sitemap.xml.gz')),1)
    def test_index_not_pages(self):
        xml=b'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://example.org/a.xml</loc></sitemap></sitemapindex>'
        with self.assertRaisesRegex(ValueError,'índice'):
            parse_sitemap(xml,'sitemap.xml')

if __name__=='__main__':unittest.main()
