"""
Holt die neueste Veröffentlichung von InNoteBox und Solid Self und schreibt sie nach stand.json.

Läuft jeden Tag über den Workflow „Aktualisieren“, danach zeichnet erzeugen.py die Bilder neu.
Vorabversionen zählen mit, denn InNoteBox ist noch in der Alpha. Entwürfe zählen nicht.
"""

import json
import os
import urllib.request

PROJEKT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUELLEN = {
    "innotebox": ("Cloakyi/innotebox", "InNoteBox "),
    "solid_self": ("Cloakyi/solid-self", "Solid Self "),
}


def neueste(repo):
    anfrage = urllib.request.Request(
        "https://api.github.com/repos/%s/releases?per_page=10" % repo,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Cloakyi-Profil"},
    )
    schluessel = os.environ.get("GH_TOKEN")
    if schluessel:
        anfrage.add_header("Authorization", "Bearer " + schluessel)
    with urllib.request.urlopen(anfrage, timeout=30) as antwort:
        liste = json.loads(antwort.read().decode("utf-8"))
    liste = [r for r in liste if not r["draft"] and r.get("published_at")]
    return max(liste, key=lambda r: r["published_at"]) if liste else None


def main():
    pfad = os.path.join(PROJEKT, "stand.json")
    with open(pfad, encoding="utf-8") as datei:
        stand = json.load(datei)
    for kennung, (repo, vorsilbe) in QUELLEN.items():
        veroeffentlichung = neueste(repo)
        if veroeffentlichung is None:
            continue
        name = (veroeffentlichung["name"] or veroeffentlichung["tag_name"]).strip()
        if name.startswith(vorsilbe):
            name = name[len(vorsilbe):]
        stand[kennung] = {
            "fassung": name,
            "datum": veroeffentlichung["published_at"][:10],
            "adresse": veroeffentlichung["html_url"],
        }
    with open(pfad, "w", encoding="utf-8", newline="\n") as datei:
        json.dump(stand, datei, ensure_ascii=False, indent=2)
        datei.write("\n")


if __name__ == "__main__":
    main()
