"""
Liest die Umrisse der Schrift Google Sans Flex aus und schreibt sie nach werkzeug/glyphen.json.

Die Bilder dieser Seite zeichnen ihre Schrift als Pfade. Ein SVG, das GitHub als Bild zeigt,
darf keine Schrift nachladen, und eine eingebettete Schrift wäre in jedem Bild noch einmal
50 KB schwer. Pfade sehen überall gleich aus und brauchen nur die Zeichen, die vorkommen.

Nur nötig, wenn neue Zeichen oder Gewichte dazukommen. Braucht fontTools und die Schrift
(dieselbe Datei wie in der App, SIL Open Font License):

    python werkzeug/glyphen.py pfad/zu/google_sans_flex.ttf
"""

import json
import os
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ORDNER = os.path.dirname(os.path.abspath(__file__))
GEWICHTE = (400, 500, 600)
ZEICHEN = "".join(chr(c) for c in range(32, 127)) + "ÄÖÜäöüß·…„“’é"


def main():
    quelle = sys.argv[1]
    ergebnis = {"upm": None, "gewichte": {}}
    for gewicht in GEWICHTE:
        schrift = TTFont(quelle)
        achsen = {a.axisTag: a.defaultValue for a in schrift["fvar"].axes}
        achsen["wght"] = gewicht
        schrift = instancer.instantiateVariableFont(schrift, achsen)
        ergebnis["upm"] = schrift["head"].unitsPerEm
        tabelle = schrift.getBestCmap()
        glyphen = schrift.getGlyphSet()
        breiten = schrift["hmtx"]
        zeichen = {}
        for z in ZEICHEN:
            name = tabelle.get(ord(z))
            if name is None:
                continue
            stift = SVGPathPen(glyphen, ntos=lambda x: str(round(x)))
            glyphen[name].draw(stift)
            zeichen[z] = [breiten[name][0], stift.getCommands()]
        ergebnis["gewichte"][str(gewicht)] = zeichen
    with open(os.path.join(ORDNER, "glyphen.json"), "w", encoding="utf-8") as datei:
        json.dump(ergebnis, datei, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
