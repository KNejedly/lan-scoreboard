import os,tempfile,unittest
from unittest.mock import patch
from lan.store import Store,snapshot
from lan.vision import process,images,Review
from ocr_fixture import fixture

class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.s=Store(self.temp.name)
        self.s.player(0,"p01","ALFA",[]);self.s.player(1,"p02","BETA",[])
    def test_invalid(self):
        with self.assertRaises(Review):images(self.s,[b"not an image"])
    def test_schema_missing(self):
        with patch("lan.vision.openai_read",return_value={"rows":[]}):
            res=process(self.s,2,"hl","crossfire",["p01"],[fixture()],"openai")
            self.assertFalse(res["ok"]);self.assertEqual(self.s.read()[0],2)
    def test_null(self):
        with patch("lan.vision.openai_read",return_value={"game":"hl","stage":"crossfire","final":True,"uncertain":False,"rows":[{"nick":"ALFA","stats":{"kills":None,"deaths":3}}]}):
            res=process(self.s,2,"hl","crossfire",["p01"],[fixture()],"openai")
            self.assertFalse(res["ok"])
    @unittest.skipUnless(os.getenv("LAN_TEST_OCR")=="1","Zapněte LAN_TEST_OCR=1 pro skutečné neuronové OCR.")
    def test_real_model(self):
        res=process(self.s,2,"hl","crossfire",["p01","p02"],[fixture()])
        self.assertTrue(res["ok"],res)
        vals=[r["value"] for r in snapshot(*self.s.read())["games"][0]["standings"]]
        self.assertEqual(vals,[1700,800])
        self.assertFalse(process(self.s,3,"hl","crossfire",["p01","p02"],[fixture()])["ok"])
