#!/usr/bin/env python3
"""
Migratie: brede datering van de theorielaag (juni 2026).

Vervolg op migrate_tijdsdimensie_theorielaag.py en _techplatform.py: de
hele theorielaag is langsgelopen. Gedateerd wordt alleen wat een
verdedigbaar institutioneel of technologisch beginpunt heeft — het
moment waarop het mechanisme/de rol in Nederland kon ontstaan. Echt
tijdloze elementen (zelfcensuur, bron_afhankelijkheid, etikettering,
elite-netwerken, academische socialisatie, de meeste draaideuren en
eigendomsmechanismen, emergente lussen als fabricage_van_consensus)
blijven bewust NULL = onbegrensd voor zover bekend.

Ankerpunten (rationale per regel hieronder; "~" = circa/zachter anker):
1848 Grondwet Thorbecke (parlementaire controle), 1851 telegraaf-
persbureaus (Reuters), 1869 afschaffing dagbladzegel (massapers op
advertentiemodel), 1879 eerste moderne partij (ARP), 1884 NVJ-voorloper,
1920 ~opkomst PR-industrie, 1924 eerste ledenomroepen, 1930
Zendtijdenbesluit, 1934 ANP, 1944 Stichting Het Parool, 1945
RVD/wetenschappelijke bureaus, 1947 NRU (eerste omroepkoepel), 1948
Raad van Tucht voor de Journalistiek, 1949 BVD, 1951 ~televisietijdperk,
1954 Bilderberg, 1962 Nieuwspoort, 1965 STER, 1970 eerste
redactiestatuten, 1974 Bedrijfsfonds voor de Pers, 1980 WOB in werking,
1989 ~commerciele omroep, 1990 ~verdichte nieuwsconcurrentie, 2000
~voorlichtersovermacht, 2002 raad van bestuur publieke omroep, 2008
Mediawet 2.149/2.150, 2017 ~Mediahuis-TMG voltooit het duopolie.

Backup-then-migrate; idempotent; alleen NULL wordt gevuld, handmatig
gewijzigde datums blijven staan.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# (tabel, naam, active_from, rationale)
DATERINGEN = [
    # ── Advertentiemodel (1869: afschaffing dagbladzegel → massapers) ──
    ("mechanisms", "advertentiedruk", "1869", "afschaffing dagbladzegel: massapers op advertentiemodel"),
    ("mechanisms", "commerciele_afhankelijkheid", "1869", "afschaffing dagbladzegel: massapers op advertentiemodel"),
    ("mechanisms", "supportive_selling_environment", "1869", "advertentiemodel sinds afschaffing dagbladzegel"),
    ("mechanisms", "adverteren_als_belang", "1869", "advertentiemodel sinds afschaffing dagbladzegel"),
    ("roles", "adverteerder", "1869", "afschaffing dagbladzegel: massapers op advertentiemodel"),

    # ── Persbureaus (1851 Reuters/telegraafpersbureaus; 1934 ANP) ──
    ("mechanisms", "pakketjournalistiek", "1851", "telegraafpersbureaus (Reuters) bevoorraden kranten"),
    ("mechanisms", "persbureau_brongebondenheid", "1851", "telegraafpersbureaus (Reuters)"),
    ("mechanisms", "klantvraag_persbureau", "1851", "telegraafpersbureaus (Reuters)"),
    ("roles", "persbureau", "1851", "telegraafpersbureaus (Reuters)"),
    ("emergent_effects", "schijnpluriformiteit", "1934", "ANP als centrale leverancier van vrijwel alle titels"),

    # ── Politiek bestel (1848 Thorbecke; 1879 ARP) ──
    ("mechanisms", "parlementaire_controle", "1848", "Grondwet 1848: ministeriele verantwoordelijkheid + enqueterecht"),
    ("roles", "parlementair_controleur", "1848", "Grondwet 1848"),
    ("mechanisms", "partijlijn", "1879", "eerste moderne partij (ARP, 1879)"),
    ("mechanisms", "partijfinanciering", "1879", "eerste moderne partij (ARP, 1879)"),
    ("roles", "partij", "1879", "eerste moderne partij (ARP, 1879)"),

    # ── Journalistieke organisatie & borging ──
    ("mechanisms", "vakbond_bescherming", "1884", "Nederlandsche Journalisten-Kring (voorloper NVJ)"),
    ("roles", "vakbond_media", "1884", "Nederlandsche Journalisten-Kring (voorloper NVJ)"),
    ("mechanisms", "redactiestatuut_borging", "1970", "eerste redactiestatuten (NRC/de Volkskrant, ~1970)"),
    ("mechanisms", "redactieraad_instemming", "1970", "eerste redactiestatuten (~1970)"),
    ("roles", "borgingsstichting", "1944", "Stichting Het Parool als eerste borgingsstichting"),
    ("mechanisms", "projectfinanciering_journalistiek", "1974", "Bedrijfsfonds voor de Pers (nu SvdJ)"),

    # ── Toezicht (1948 Raad van Tucht; 1980 WOB) ──
    ("mechanisms", "toezicht_tandeloosheid", "1948", "Raad van Tucht voor de Journalistiek, later RvdJ/CvdM/ACM"),
    ("mechanisms", "toezichthouder_interventie", "1948", "Raad van Tucht voor de Journalistiek, later RvdJ/CvdM/ACM"),
    ("roles", "toezichthouder", "1948", "Raad van Tucht voor de Journalistiek, later RvdJ/CvdM/ACM"),
    ("mechanisms", "woo_obstructie", "1980", "WOB in werking (1980), sinds 2022 Woo"),

    # ── Voorlichting & PR (1920 ~PR-industrie; 1945 RVD) ──
    ("mechanisms", "pr_subsidie", "1920", "~opkomst van de professionele PR-industrie"),
    ("mechanisms", "pr_inhuur", "1920", "~opkomst van de professionele PR-industrie"),
    ("mechanisms", "voorlichter_informatiefilter", "1945", "Rijksvoorlichtingsdienst (1945/1947)"),
    ("mechanisms", "gecoordineerde_voorlichting", "1945", "Rijksvoorlichtingsdienst (1945/1947)"),
    ("mechanisms", "institutionele_voorlichting", "1945", "Rijksvoorlichtingsdienst (1945/1947)"),
    ("mechanisms", "woordvoerdersregie", "1945", "naoorlogs voorlichtingsapparaat"),
    ("roles", "voorlichter", "1945", "Rijksvoorlichtingsdienst (1945/1947)"),
    ("emergent_effects", "voorlichtingsovermacht", "2000", "~voorlichters overtreffen journalisten ruim in aantal"),

    # ── Denktanks (1945 wetenschappelijke bureaus/WBS) ──
    ("mechanisms", "denktank_financiering_bias", "1945", "wetenschappelijke bureaus/denktanks na WOII"),
    ("mechanisms", "denktank_naar_politiek", "1945", "wetenschappelijke bureaus/denktanks na WOII"),
    ("mechanisms", "denktank_levert_expert", "1945", "wetenschappelijke bureaus/denktanks na WOII"),
    ("mechanisms", "denktank_naar_persbureau", "1945", "wetenschappelijke bureaus/denktanks na WOII"),
    ("mechanisms", "academische_orthodoxie_denktank", "1945", "wetenschappelijke bureaus/denktanks na WOII"),
    ("roles", "denktank", "1945", "wetenschappelijke bureaus/denktanks na WOII"),

    # ── Omroepbestel (1924 ledenomroepen; 1930 Zendtijdenbesluit; ...) ──
    ("mechanisms", "omroepsignatuur", "1924", "eerste statutair gekleurde ledenomroepen (NCRV/KRO/VARA)"),
    ("roles", "ledenomroep", "1924", "eerste ledenomroepen (NCRV/KRO/VARA)"),
    ("mechanisms", "bestelsturing", "1930", "Zendtijdenbesluit 1930"),
    ("mechanisms", "ledeneis", "1930", "zendtijd naar ledental (A/B/C-stelsel, 1930)"),
    ("mechanisms", "erkenningverlening", "1930", "zendmachtigingen sinds Zendtijdenbesluit 1930"),
    ("roles", "omroepkoepel", "1947", "Nederlandse Radio Unie, later NTS/NOS/NPO"),
    ("mechanisms", "staatsreclame_exploitatie", "1965", "oprichting STER"),
    ("mechanisms", "politieke_benoeming_omroeptop", "2002", "raad van bestuur publieke omroep (benoeming door OCW)"),
    ("mechanisms", "intekensturing", "2008", "garantiebudgetten art. 2.149/2.150 Mediawet 2008"),

    # ── Televisielogica (1951 ~tv-tijdperk) ──
    ("mechanisms", "mediageniekheidsselectie", "1951", "~televisietijdperk: gastselectie op vorm en amusementswaarde"),
    ("mechanisms", "conflictregie", "1951", "~televisietijdperk"),

    # ── Staat & inlichtingen ──
    ("mechanisms", "inlichtingen_cooptatie", "1949", "oprichting BVD (nu AIVD)"),

    # ── Elite & Den Haag ──
    ("roles", "elite_forum", "1954", "Bilderberg-conferenties"),
    ("emergent_effects", "haagse_stam", "1962", "~Nieuwspoort institutionaliseert de Binnenhof-stam"),

    # ── Commercialisering & concentratie (zachtere ankers) ──
    ("mechanisms", "cross_media_eigendom", "1989", "~commerciele omroep maakt cross-media-eigendom mogelijk"),
    ("emergent_effects", "medialogica", "1989", "~commerciele omroep; wurggreep beschreven in RMO-rapport 2003"),
    ("emergent_effects", "mediahype", "1990", "~verdichte nieuwsconcurrentie (commerciele omroep, 24u-nieuws)"),
    ("mechanisms", "eigendomsconcentratie", "2017", "~Mediahuis-TMG-overname voltooit het beschreven duopolie"),
]


def backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = DB.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB, dst)
    print(f"backup -> {dst.name}")


def main():
    if not DB.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB}")
    backup()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    for table, name, van, rationale in DATERINGEN:
        row = cur.execute(
            f"SELECT id, active_from FROM {table} WHERE name=?", (name,)).fetchone()
        if row is None:
            print(f"WAARSCHUWING: niet gevonden in {table}: {name}")
            continue
        rid, huidig = row
        if huidig is None:
            cur.execute(f"UPDATE {table} SET active_from=? WHERE id=?", (van, rid))
            print(f"gedateerd: {table}.{name} [{van} - heden] ({rationale})")
        elif huidig == van:
            print(f"al gedateerd: {table}.{name} [{van} - heden]")
        else:
            print(f"OVERGESLAGEN (handmatig afwijkend): {table}.{name} "
                  f"[{huidig}], migratie wilde [{van}]")

    con.commit()
    for table in ("mechanisms", "roles", "emergent_effects"):
        n, tot = cur.execute(
            f"SELECT SUM(active_from IS NOT NULL), COUNT(*) FROM {table}").fetchone()
        print(f"{table}: {n} van {tot} gedateerd (rest = onbegrensd voor zover bekend)")
    con.close()
    print("\nklaar — draai scripts/generate_viz.py om de viz bij te werken")


if __name__ == "__main__":
    main()
