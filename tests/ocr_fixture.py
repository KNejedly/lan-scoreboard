"""Jednoznačně syntetická výsledkovka pro zkoušku čtení, bez skutečných hráčů."""
import io
from PIL import Image,ImageDraw,ImageFont

def fixture():
    from pathlib import Path
    reference=Path(__file__).with_name("synthetic-scoreboard.png")
    if reference.is_file():
        return reference.read_bytes()
    image=Image.new("RGB",(1100,590),"#11202c");d=ImageDraw.Draw(image)
    def font(size):
        for family in ("DejaVuSans.ttf","arial.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
            try:return ImageFont.truetype(family,size)
            except OSError:pass
        return ImageFont.load_default(size=size)
    d.text((45,25),"SYNTHETIC TEST",font=font(28),fill="#a4e3bd")
    d.text((45,90),"Half-Life   Crossfire",font=font(47),fill="white")
    d.text((45,170),"Final results",font=font(35),fill="white")
    for y,cells in [(275,["Player","Kills","Deaths"]),(365,["ALFA","10","3"]),(455,["BETA","6","4"])]:
        for x,text in zip([65,560,850],cells):d.text((x,y),text,font=font(40),fill="white")
    fp=io.BytesIO();image.save(fp,"PNG");return fp.getvalue()
