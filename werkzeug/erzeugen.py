"""
Zeichnet alle Bilder dieser Profilseite nach bilder/, je einmal hell und einmal dunkel.

Die Bilder sehen aus wie InNoteBox: dieselben Farben, dieselbe Schrift, dieselben Karten.
Die Werte stehen unten in HELL und DUNKEL und folgen dem Farbschema der App.

Läuft ohne Zusatzpakete, nur mit Python. Die Schrift kommt als Umrisse aus glyphen.json,
die Bilder aus quellen/, der Stand der Projekte aus stand.json. Aufruf aus dem Projektordner:

    python werkzeug/erzeugen.py
"""

import base64
import json
import math
import os

WERKZEUG = os.path.dirname(os.path.abspath(__file__))
PROJEKT = os.path.dirname(WERKZEUG)
BILDER = os.path.join(PROJEKT, "bilder")

with open(os.path.join(WERKZEUG, "glyphen.json"), encoding="utf-8") as datei:
    SCHRIFT = json.load(datei)
with open(os.path.join(PROJEKT, "stand.json"), encoding="utf-8") as datei:
    STAND = json.load(datei)

DUNKEL = {
    "name": "dunkel",
    "hintergrund": "#001137",
    "leiste": "#011742",
    "flaeche_hoch": "#051D4B",
    "karte": "#000C2C",
    "linie": "#39476C",
    "text": "#DEE5FF",
    "nebentext": "#9CAAD5",
    "primaer": "#7AAFFF",
    "fab": "#5DA2FF",
    "auf_fab": "#002348",
    "gelb": ("#67531B", "#F4E6C0"),
    "blau": ("#1B4E67", "#C0E3F4"),
    "dunkellila": ("#571B67", "#E8C2F2"),
    "dunkelgruen": ("#1B673F", "#C0F4D9"),
    "leiste_invers": "#FAF8FF",
    "text_invers": "#46547A",
    "primaer_invers": "#005FB3",
}

HELL = {
    "name": "hell",
    "hintergrund": "#EEF0FF",
    "leiste": "#E2E7FF",
    "flaeche_hoch": "#DAE2FF",
    "karte": "#F6F6FF",
    "linie": "#9EACD7",
    "text": "#1F2D51",
    "nebentext": "#4D5A81",
    "primaer": "#005BAC",
    "fab": "#5DA2FF",
    "auf_fab": "#002348",
    "gelb": ("#F8E8BC", "#564004"),
    "blau": ("#BCE4F8", "#023B57"),
    "dunkellila": ("#E8C2F2", "#3E104A"),
    "dunkelgruen": ("#BCF8D9", "#07522B"),
    "leiste_invers": "#000C2C",
    "text_invers": "#8E9CC6",
    "primaer_invers": "#2F91FF",
}

GOLD = "#FFC107"
ANGEKOMMEN = "#4CAF50"

# Die Tagfarben der App (Palette des Google-Kalenders)
TAG = {
    "rot": "#D50000", "rosa": "#E67C73", "orange": "#F4511E", "gelb": "#F6BF26",
    "gruen": "#33B679", "dunkelgruen": "#0B8043", "tuerkis": "#00897B", "blau": "#039BE5",
    "indigo": "#3F51B5", "lavendel": "#7986CB", "lila": "#8E24AA", "braun": "#795548",
    "grau": "#616161",
}

ANIMATION = """
  .k { animation: ein .6s cubic-bezier(.2,.9,.3,1) both; }
  .z { animation: zeigen .08s linear both; }
  .weg { opacity: 0; animation: weg .25s ease-out both; }
  .blitz { opacity: 0; animation: blitz 1.6s ease-out both; }
  .blinken { animation: blinken 1.06s step-end infinite; }
  @keyframes ein { from { opacity: 0; transform: translateY(14px); } }
  @keyframes zeigen { from { opacity: 0; } }
  @keyframes weg { from { opacity: 1; } }
  @keyframes blitz { 0% { opacity: 0; } 20% { opacity: 1; } 100% { opacity: 0; } }
  @keyframes blinken { 50% { opacity: 0; } }
  @media (prefers-reduced-motion: reduce) {
    .k, .z, .weg, .blitz, .blinken { animation: none; }
  }
"""


def bild_daten(name, art):
    with open(os.path.join(WERKZEUG, "quellen", name), "rb") as datei:
        return "data:image/%s;base64,%s" % (art, base64.b64encode(datei.read()).decode("ascii"))


def verzoegerung(sekunden):
    return ' style="animation-delay:%.2fs"' % sekunden


class Bild:
    """Ein SVG im Aufbau. Merkt sich, welche Zeichen vorkommen, und legt nur die an."""

    def __init__(self, breite, hoehe, titel):
        self.breite = breite
        self.hoehe = hoehe
        self.titel = titel
        self.zeichen = set()
        self.teile = []

    def __iadd__(self, teil):
        self.teile.append(teil)
        return self

    @staticmethod
    def textbreite(text, groesse, gewicht=400):
        glyphen = SCHRIFT["gewichte"][str(gewicht)]
        return sum(glyphen[z][0] for z in text) * groesse / SCHRIFT["upm"]

    def text(self, text, x, y, groesse, farbe, gewicht=400, anker="start", je_zeichen=None):
        """Eine Zeile Text, y ist die Grundlinie. je_zeichen(i) gibt Attribute für das
        i-te Zeichen zurück, etwa eine Verzögerung zum Eintippen."""
        glyphen = SCHRIFT["gewichte"][str(gewicht)]
        if anker == "end":
            x -= self.textbreite(text, groesse, gewicht)
        elif anker == "middle":
            x -= self.textbreite(text, groesse, gewicht) / 2
        faktor = groesse / SCHRIFT["upm"]
        stuecke = []
        vor = 0
        for i, z in enumerate(text):
            breite, pfad = glyphen[z]
            if pfad:
                self.zeichen.add((gewicht, z))
                extra = je_zeichen(i) if je_zeichen else ""
                stuecke.append('<use href="#g%d-%d" x="%d"%s/>' % (gewicht, ord(z), vor, extra))
            vor += breite
        return '<g transform="translate(%.1f %.1f) scale(%.5f %.5f)" fill="%s">%s</g>' % (
            x, y, faktor, -faktor, farbe, "".join(stuecke))

    def absatz(self, text, x, y, breite, groesse, farbe, zeilenhoehe, gewicht=400):
        """Bricht Text an Leerzeichen um, gibt die Zeilen und die Höhe zurück."""
        zeilen, zeile = [], ""
        for wort in text.split(" "):
            probe = (zeile + " " + wort).strip()
            if zeile and self.textbreite(probe, groesse, gewicht) > breite:
                zeilen.append(zeile)
                zeile = wort
            else:
                zeile = probe
        zeilen.append(zeile)
        teile = [self.text(z, x, y + i * zeilenhoehe, groesse, farbe, gewicht)
                 for i, z in enumerate(zeilen)]
        return "".join(teile), len(zeilen) * zeilenhoehe

    def pille(self, text, x, y, farbe, textfarbe):
        """Ein Tag wie auf einer Karte der App: Tagfarbe mit 22 % Fläche und 50 % Rand."""
        breite = self.textbreite(text, 12.5, 500) + 18
        return breite, (
            '<rect x="%.1f" y="%.1f" width="%.1f" height="24" rx="8" fill="%s" fill-opacity=".22" '
            'stroke="%s" stroke-opacity=".5"/>%s'
            % (x + .5, y + .5, breite - 1, farbe, farbe, self.text(text, x + 9, y + 16.5, 12.5, textfarbe, 500)))

    def pillen(self, namen, x, y, breite, textfarbe, abstand=6):
        teile, links, oben = [], x, y
        for text, farbe in namen:
            b = self.textbreite(text, 12.5, 500) + 18
            if links > x and links + b > x + breite:
                links, oben = x, oben + 24 + abstand
            teile.append(self.pille(text, links, oben, farbe, textfarbe)[1])
            links += b + abstand
        return "".join(teile), oben + 24 - y

    def fertig(self, beschreibung):
        glyphen = []
        for gewicht, z in sorted(self.zeichen):
            pfad = SCHRIFT["gewichte"][str(gewicht)][z][1]
            glyphen.append('<path id="g%d-%d" d="%s"/>' % (gewicht, ord(z), pfad))
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
            'role="img" aria-label="%s">\n<title>%s</title>\n<style>%s</style>\n<defs>%s</defs>\n%s\n</svg>\n'
            % (self.breite, self.hoehe, self.breite, self.hoehe, beschreibung, beschreibung,
               ANIMATION, "".join(glyphen), "\n".join(self.teile)))


# Kleine Symbole im Stil der Material Symbols, als Pfade gezeichnet

def symbol_menue(x, y, farbe):
    return "".join('<rect x="%d" y="%d" width="18" height="2" rx="1" fill="%s"/>' % (x, y + d, farbe)
                   for d in (0, 6, 12))


def symbol_lupe(x, y, farbe):
    return ('<circle cx="%d" cy="%d" r="6.5" fill="none" stroke="%s" stroke-width="2"/>'
            '<path d="M%d %dl5.5 5.5" stroke="%s" stroke-width="2.2" stroke-linecap="round"/>'
            % (x, y, farbe, x + 5, y + 5, farbe))


def symbol_raster(x, y, farbe):
    return "".join('<rect x="%d" y="%d" width="7" height="7" rx="2" fill="none" stroke="%s" stroke-width="1.8"/>'
                   % (x + dx, y + dy, farbe) for dx in (0, 10) for dy in (0, 10))


def symbol_mehr(x, y, farbe):
    return "".join('<circle cx="%d" cy="%d" r="2" fill="%s"/>' % (x, y + d, farbe) for d in (-6, 0, 6))


def symbol_stern(mx, my, r, farbe):
    punkte = []
    for i in range(10):
        winkel = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * .45
        punkte.append("%.1f,%.1f" % (mx + rr * math.cos(winkel), my - rr * math.sin(winkel)))
    return '<polygon points="%s" fill="%s" stroke="%s" stroke-width="1.5" stroke-linejoin="round"/>' % (
        " ".join(punkte), farbe, farbe)


def kasten(x, y, farbe, grund, haken, verzoegert=None):
    """Ein Kästchen einer Liste. Mit haken erscheint es (verzögert) abgehakt."""
    leer = '<rect x="%.1f" y="%.1f" width="16" height="16" rx="3" fill="none" stroke="%s" stroke-width="2"/>' % (
        x + 1, y + 1, farbe)
    if not haken:
        return leer
    voll = ('<g class="z"%s><rect x="%.1f" y="%.1f" width="18" height="18" rx="4" fill="%s"/>'
            '<path d="M%.1f %.1fl3.6 3.6 7.2-7.4" fill="none" stroke="%s" stroke-width="2.2" '
            'stroke-linecap="round" stroke-linejoin="round"/></g>'
            % (verzoegerung(verzoegert) if verzoegert else "", x, y, farbe, x + 4, y + 9.2, grund))
    return leer + voll


def welle(anzahl):
    """Feste Höhen für eine Tonspur, die nach Sprache aussieht."""
    hoehen = []
    for i in range(anzahl):
        h = .5 + .3 * math.sin(i * .55) + .2 * math.sin(i * 1.7 + 1) + .15 * math.sin(i * .21)
        if i % 9 in (0, 1):
            h *= .35
        hoehen.append(max(.12, min(1, h)))
    return hoehen


def karte(x, y, breite, hoehe, fuellung, linie, klasse_verzoegerung, inhalt, rand=None):
    rahmen = rand or '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="16" fill="none" stroke="%s"/>' % (
        x + .5, y + .5, breite - 1, hoehe - 1, linie)
    return '<g class="k"%s><rect x="%d" y="%d" width="%d" height="%d" rx="16" fill="%s"/>%s%s</g>' % (
        verzoegerung(klasse_verzoegerung), x, y, breite, hoehe, fuellung, rahmen, inhalt)


# Das Kopfbild: der Eingang von InNoteBox, gefüllt mit Notizen über Cloaki

def kopfbild(f):
    B, H = 900, 500
    bild = Bild(B, H, "Cloaki")
    bild += '<clipPath id="rahmen"><rect width="%d" height="%d" rx="28"/></clipPath>' % (B, H)
    bild += '<g clip-path="url(#rahmen)">'
    bild += '<rect width="%d" height="%d" fill="%s"/>' % (B, H, f["hintergrund"])

    # Der Avatar steht links und sieht in den Eingang hinein
    bild += '<image href="%s" x="6" y="104" width="345" height="400" preserveAspectRatio="xMidYMax meet"/>' % (
        bild_daten("avatar.webp", "webp"))

    # Kopfzeile mit Suchleiste, in die sich der Name tippt
    bild += '<rect width="%d" height="72" fill="%s"/>' % (B, f["leiste"])
    bild += symbol_menue(26, 29, f["nebentext"])
    bild += '<rect x="64" y="14" width="820" height="44" rx="22" fill="%s"/>' % f["flaeche_hoch"]
    bild += symbol_lupe(91, 34, f["nebentext"])
    bild += '<g class="weg"%s>%s</g>' % (verzoegerung(.9), bild.text("In Notizen suchen", 116, 42, 16, f["nebentext"]))
    gruss = "Hallo, ich bin Cloaki."
    beginn, takt = 1.1, .075
    bild += bild.text(gruss, 116, 42, 16, f["text"],
                      je_zeichen=lambda i: ' class="z"%s' % verzoegerung(beginn + i * takt))
    stellen, links = [], 116
    for z in gruss:
        stellen.append(links)
        links += bild.textbreite(z, 16)
    stellen.append(links)
    zeiten = ";".join("%.4f" % (i / len(stellen)) for i in range(len(stellen)))
    bild += ('<rect x="116" y="27" width="2" height="20" rx="1" fill="%s" class="blinken">'
             '<animate attributeName="x" values="%s" keyTimes="%s" calcMode="discrete" '
             'begin="%.2fs" dur="%.3fs" fill="freeze"/></rect>'
             % (f["primaer"], ";".join("%.1f" % s for s in stellen), zeiten, beginn, takt * len(stellen)))
    bild += symbol_raster(818, 26, f["nebentext"])
    bild += symbol_mehr(860, 36, f["nebentext"])

    # Zwei Spalten wie das Raster der App
    a, b, sb = 362, 627, 258
    bild += '<g class="k"%s>%s</g>' % (verzoegerung(.15), bild.text("Favoriten", a + 4, 98, 14, f["primaer"], 500))

    # Favorit mit goldenem Rahmen und Stern
    inhalt = bild.text("Cloaki", a + 16, 140, 19, f["text"], 600)
    inhalt += symbol_stern(a + sb - 26, 133, 8, GOLD)
    absatz, hoehe = bild.absatz("Furry, Gamer und Streamer aus Deutschland. Ich baue Apps und Mods.",
                                a + 16, 166, sb - 32, 14.5, f["text"], 21)
    inhalt += absatz
    oben_pillen = 166 + hoehe - 2
    pillen, hoehe = bild.pillen([("Twitch", TAG["lila"]), ("YouTube", TAG["rot"]), ("TikTok", TAG["tuerkis"])],
                                a + 16, oben_pillen, sb - 32, f["text"])
    inhalt += pillen
    hoehe_karte = oben_pillen + hoehe + 16 - 112
    gold = '<rect x="%d" y="%d" width="%d" height="%d" rx="16" fill="none" stroke="%s" stroke-width="2"/>' % (
        a + 1, 113, sb - 2, hoehe_karte - 2, GOLD)
    bild += karte(a, 112, sb, hoehe_karte, f["karte"], f["linie"], .3, inhalt, rand=gold)

    # Sprachnotiz mit Tonspur, die abspielt
    y = 112 + hoehe_karte + 12
    inhalt = bild.text("Idee für den nächsten Stream", a + 16, y + 30, 15, f["text"], 500)
    inhalt += '<circle cx="%d" cy="%d" r="18" fill="%s" fill-opacity=".18"/>' % (a + 34, y + 66, f["text"])
    inhalt += '<path d="M%d %dl12 7-12 7z" fill="%s"/>' % (a + 30, y + 59, f["text"])
    hoehen = welle(31)
    balken = "".join('<rect x="%d" y="%.1f" width="3" height="%.1f" rx="1.5"/>' % (
        a + 62 + i * 5, y + 66 - h * 15, h * 30) for i, h in enumerate(hoehen))
    breite_welle = len(hoehen) * 5
    inhalt += '<g fill="%s" fill-opacity=".3">%s</g>' % (f["text"], balken)
    inhalt += ('<clipPath id="gespielt"><rect x="%d" y="%d" width="0" height="40">'
               '<animate attributeName="width" values="0;%d;%d" keyTimes="0;.85;1" dur="9s" begin="1.5s" '
               'repeatCount="indefinite"/></rect></clipPath>' % (a + 60, y + 46, breite_welle, breite_welle))
    inhalt += '<g fill="%s" clip-path="url(#gespielt)">%s</g>' % (f["text"], balken)
    inhalt += bild.text("0:42", a + sb - 16, y + 71, 12, f["text"], 500, anker="end")
    bild += karte(a, y, sb, 98, f["karte"], f["linie"], .45, inhalt)

    # Angeschnittene Karte unten, damit es nach mehr aussieht
    y += 98 + 12
    grund, schrift = f["dunkellila"]
    inhalt = bild.text("Discord", a + 16, y + 30, 15, schrift, 500)
    inhalt += bild.text("Server auf Deutsch und Englisch.", a + 16, y + 55, 14.5, schrift)
    bild += karte(a, y, sb, 120, grund, f["linie"], .6, inhalt)

    # Liste mit dem, woran Cloaki gerade sitzt; die Haken kommen nacheinander
    y = 112
    grund, schrift = f["gelb"]
    inhalt = bild.text("Gerade dran", b + 16, y + 30, 15, schrift, 500)
    eintraege = [("InNoteBox " + STAND["innotebox"]["fassung"], True), ("Solid Self für Minecraft 26", True),
                 ("Die nächste Alpha", False), ("Stream vorbereiten", False)]
    for i, (eintrag, erledigt) in enumerate(eintraege):
        zy = y + 50 + i * 30
        inhalt += kasten(b + 16, zy, schrift, grund, erledigt, 2.6 + i * .45)
        inhalt += bild.text(eintrag, b + 44, zy + 14, 14.5, schrift)
    blitz = '<rect x="%d" y="%d" width="%d" height="%d" rx="16" fill="none" stroke="%s" stroke-width="2.5" class="blitz"%s/>' % (
        b + 1, y + 1, sb - 2, 176, ANGEKOMMEN, verzoegerung(3.8))
    bild += karte(b, y, sb, 178, grund, f["linie"], .4, inhalt + blitz)

    # Werkzeuge als Tags
    y = 302
    grund, schrift = f["blau"]
    inhalt = bild.text("Womit ich baue", b + 16, y + 30, 15, schrift, 500)
    pillen, hoehe = bild.pillen(
        [("Kotlin", TAG["lila"]), ("Jetpack Compose", TAG["gruen"]), ("Java", TAG["orange"]),
         ("Fabric", TAG["gelb"]), ("Firebase", TAG["rot"]), ("VRChat", TAG["indigo"])],
        b + 16, y + 44, sb - 32, schrift)
    inhalt += pillen
    bild += karte(b, y, sb, 44 + hoehe + 16, grund, f["linie"], .55, inhalt)

    # Der große Plusknopf
    bild += ('<g class="k"%s><rect x="812" y="412" width="72" height="72" rx="22" fill="%s"/>'
             '<path d="M848 434v28M834 448h28" stroke="%s" stroke-width="3.2" stroke-linecap="round"/></g>'
             % (verzoegerung(.8), f["fab"], f["auf_fab"]))
    bild += "</g>"
    return bild.fertig("Cloaki: Furry, Gamer und Streamer aus Deutschland, gezeigt als Eingang der App InNoteBox")


# Die Karten der Projekte

def projektkarte(f, art):
    B, H = 440, 226
    bild = Bild(B, H, art)
    if art == "innotebox":
        grund, schrift, neben = f["karte"], f["text"], f["nebentext"]
        titel, unter = "InNoteBox", "Notizen-App für Android"
        chip = STAND["innotebox"]["fassung"]
        text = ("Eingang, Workspace und Archiv. Ohne Konto und ohne Server, KI nur auf dem Gerät, "
                "Abgleich über dein eigenes Google Drive.")
        tags = [("Kotlin", TAG["lila"]), ("Jetpack Compose", TAG["gruen"]), ("Material 3", TAG["indigo"])]
        lizenz, symbol = "GPL-3.0", bild_daten("innotebox.png", "png")
        rand = '<rect x="1" y="1" width="%d" height="%d" rx="16" fill="none" stroke="%s" stroke-width="2"/>' % (
            B - 2, H - 2, GOLD)
        rand += symbol_stern(B - 26, 30, 8, GOLD)
    else:
        grund, schrift = f["dunkelgruen"]
        neben = schrift
        titel, unter = "Solid Self", "Mod für Minecraft"
        chip = STAND["solid_self"]["fassung"]
        text = ("Mit Iris-Shadern sind Spieler wieder fest statt durchsichtig, und Umrisse in der Welt "
                "erfassen sie endlich auch.")
        tags = [("Java", TAG["orange"]), ("Fabric", TAG["gelb"]), ("Iris", TAG["lavendel"]), ("Mixin", TAG["blau"])]
        lizenz, symbol = "MIT", bild_daten("solid-self.png", "png")
        rand = '<rect x=".5" y=".5" width="%d" height="%d" rx="16" fill="none" stroke="%s"/>' % (B - 1, H - 1, f["linie"])
    bild += '<rect width="%d" height="%d" rx="16" fill="%s"/>' % (B, H, grund)
    bild += rand
    bild += '<clipPath id="symbol"><rect x="20" y="20" width="48" height="48" rx="13"/></clipPath>'
    bild += '<image href="%s" x="20" y="20" width="48" height="48" clip-path="url(#symbol)"/>' % symbol
    bild += bild.text(titel, 82, 42, 19, schrift, 600)
    bild += '<g opacity=".72">%s</g>' % bild.text(unter, 82, 63, 13.5, neben)
    absatz, _ = bild.absatz(text, 20, 102, B - 40, 14.5, schrift, 21)
    bild += absatz
    pillen, _ = bild.pillen(tags, 20, H - 44, B - 120, schrift)
    bild += pillen
    if chip:
        breite = bild.textbreite(chip, 12.5, 500) + 20
        x = B - 20 - breite
        bild += '<rect x="%.1f" y="%d" width="%.1f" height="24" rx="8" fill="%s"/>' % (x, H - 44, breite, f["fab"])
        bild += bild.text(chip, x + 10, H - 27.5, 12.5, f["auf_fab"], 500)
    else:
        bild += '<g opacity=".72">%s</g>' % bild.text(lizenz, B - 20, H - 27.5, 12.5, schrift, 500, anker="end")
    return bild.fertig("%s: %s. %s" % (titel, unter, text))


# Die Knöpfe zu den Kanälen, wie die Chips der App

LINKS = [
    ("twitch", "Twitch", TAG["lila"]),
    ("youtube", "YouTube", TAG["rot"]),
    ("tiktok", "TikTok", TAG["tuerkis"]),
    ("discord", "Discord", TAG["indigo"]),
    ("instagram", "Instagram", TAG["rosa"]),
    ("x", "X", TAG["grau"]),
    ("telegram", "Telegram", TAG["blau"]),
    ("spotify", "Spotify", TAG["dunkelgruen"]),
    ("steam", "Steam", TAG["braun"]),
    ("vrchat", "VRChat", TAG["lavendel"]),
    ("modrinth", "Modrinth", TAG["gruen"]),
    ("cloaki", "cloaki.de", "#35A4FF"),
]


def chip(f, text, farbe):
    breite = Bild.textbreite(text, 14, 500) + 46
    bild = Bild(round(breite), 36, text)
    bild += '<rect width="%d" height="36" rx="8" fill="%s"/>' % (round(breite), f["flaeche_hoch"])
    bild += '<circle cx="18" cy="18" r="5" fill="%s"/>' % farbe
    bild += bild.text(text, 32, 23, 14, f["text"], 500)
    return bild.fertig(text)


# Die Leiste ganz unten, wie die Meldung der App nach dem Speichern

def meldung(f):
    B, H = 900, 52
    bild = Bild(B, H, "Neu")
    fassung = STAND["innotebox"]["fassung"]
    bild += '<g class="k"%s>' % verzoegerung(.6)
    bild += '<rect width="%d" height="%d" rx="8" fill="%s"/>' % (B, H, f["leiste_invers"])
    bild += bild.text("Neu: InNoteBox %s ist da." % fassung, 20, 31.5, 15, f["text_invers"])
    bild += bild.text("Ansehen", B - 20, 31.5, 14.5, f["primaer_invers"], 500, anker="end")
    bild += "</g>"
    return bild.fertig("Neu: InNoteBox %s ist da." % fassung)


def schreiben(name, inhalt):
    with open(os.path.join(BILDER, name), "w", encoding="utf-8", newline="\n") as datei:
        datei.write(inhalt)


def main():
    os.makedirs(BILDER, exist_ok=True)
    for f in (DUNKEL, HELL):
        schreiben("kopf-%s.svg" % f["name"], kopfbild(f))
        schreiben("innotebox-%s.svg" % f["name"], projektkarte(f, "innotebox"))
        schreiben("solid-self-%s.svg" % f["name"], projektkarte(f, "solid_self"))
        schreiben("neu-%s.svg" % f["name"], meldung(f))
        for kennung, text, farbe in LINKS:
            schreiben("link-%s-%s.svg" % (kennung, f["name"]), chip(f, text, farbe))


if __name__ == "__main__":
    main()
