import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from lan.scoring import Review,ranks,score
from lan.store import Store,snapshot

class TournamentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.s=Store(self.tmp.name)
        self.s.player(0,"p01","Alfa",["alpha"])
        self.rows=[{"nick":"alpha","stats":{"kills":2,"deaths":1}}]
    def write(self,slot="crossfire",**kw):
        return self.s.match(self.s.read()[0],"hl",slot,self.rows,["p01"],**kw)
    def test_excel_cells(self):
        self.assertEqual(score("hl","crossfire",{"kills":1,"deaths":1}),100)
        self.assertEqual(sum(score("cs",k,{"kills":2 if k=="map1a" else 1,"deaths":1}) for k in ["map1a","map1b","map2a","map2b","pool"]),700)
        self.assertEqual(score("wc","water",dict(unit_score=1,resource_score=1,hero_score=1,units_killed=1,heroes_killed=1,place=1)),2103)
        self.assertEqual(ranks({"a":3,"b":3,"c":1}),{"a":1,"b":1,"c":3})
    def test_negative_and_incomplete(self):
        self.assertEqual(score("hl","crossfire",{"kills":0,"deaths":2}),-200)
        for value in (True,None,-1,"3"):
            with self.assertRaises(Review):score("hl","crossfire",{"kills":value,"deaths":0})
        with self.assertRaises(Review):self.s.match(1,"hl","crossfire",self.rows,["p01","p02"])
    def test_conflict_and_dedupe(self):
        self.write(digests=["a"]);self.assertEqual(self.write(digests=["a"]),2)
        with self.assertRaises(Review):self.write("stalkyard",digests=["a"])
        self.rows[0]["stats"]["kills"]=6
        with self.assertRaises(Review):self.write()
        self.write(replace=True)
        self.assertEqual(snapshot(*self.s.read())["games"][0]["standings"][0]["value"],1100)
    def test_races(self):
        def add(slot):
            try:return self.s.match(1,"hl",slot,self.rows,["p01"])
            except Review:return None
        with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(list(pool.map(add,["crossfire","stalkyard"])).count(2),1)
    def test_alias_and_privacy(self):
        with self.assertRaises(Review):self.s.player(1,"p02","Other",["ALPHA"])
        self.write();d=snapshot(*self.s.read())
        self.assertNotIn("alpha",json.dumps(d))
        self.assertFalse(d["hasAwards"])
    def test_awards_and_undo(self):
        self.write()
        with self.assertRaises(Review):self.s.award(2,"hl",{"p01":3},"schváleno")
        self.write("stalkyard");self.s.award(3,"hl",{"p01":12},"Testovací schválení")
        self.assertEqual(snapshot(*self.s.read())["board"][0]["points"],12)
        self.s.cancel(4,"hl/crossfire");self.assertFalse(snapshot(*self.s.read())["hasAwards"])
        self.s.restore(5,4);self.assertEqual(snapshot(*self.s.read())["board"][0]["points"],12)
    def test_review_only(self):
        with self.assertRaises(Review):self.s.match(1,"cs","map1a",self.rows,["p01"])
    def test_placement_sums(self):
        for game,slots,values in [("wc",["water","fury","slalom","uther"],[1,1,1,12]),("fo",["race","common","derby"],[1,1,1])]:
            for slot,v in zip(slots,values):
                stats={"place":v}
                if game=="wc" and slot!="uther":stats.update(unit_score=1,resource_score=1,hero_score=1,units_killed=1,heroes_killed=1)
                self.s.match(self.s.read()[0],game,slot,[{"nick":"Alfa","stats":stats}],["p01"],manual=True)
            g=next(g for g in snapshot(*self.s.read())["games"] if g["id"]==game)
            self.assertEqual(g["standings"][0]["value"],sum(values))
            self.assertIsNone(g["standings"][0]["rank"])

if __name__=="__main__":unittest.main()
