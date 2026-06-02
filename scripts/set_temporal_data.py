"""
Vul active_from, active_until en active in voor entiteiten en relaties.

Conventies:
- active_from: jaar (of datum) waarop entiteit/relatie begon
- active_until: jaar waarop het eindigde, NULL = nog actief
- active: TRUE als nu actief, FALSE als niet meer
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


# =============================================================================
# ENTITEITEN: (name, active_from, active_until, active)
# active_until=None means still active
# =============================================================================
ENTITY_PERIODS = {
    # --- Mediaorganisaties ---
    "DPG Media":                    ("2019", None, True),    # hernoemd van De Persgroep in 2019
    "Mediahuis":                    ("2013", None, True),    # fusie in 2013
    "AD (Algemeen Dagblad)":        ("1946", None, True),
    "de Volkskrant":                ("1919", None, True),
    "Trouw":                        ("1943", None, True),
    "Het Parool":                   ("1940", None, True),
    "NU.nl":                        ("1999", None, True),
    "RTL Nederland":                ("1989", None, True),
    "RTL Nieuws":                   ("1989", None, True),
    "De Telegraaf":                 ("1893", None, True),
    "NRC":                          ("1970", None, True),
    "NOS":                          ("1969", None, True),
    "ANP":                          ("1934", None, True),
    "De Correspondent":             ("2013", None, True),
    "De Morgen":                    ("1978", None, True),
    "Brandpunt":                    ("1962", "2017", False),  # gestopt in 2017
    "Gezond Verstand":              ("2020", None, True),     # opgericht tijdens corona
    "Metro":                        ("1999", "2020", False),  # gratis krant, gestopt 2020

    # --- Personen ---
    "Christian Van Thillo":         ("1962", None, True),     # geboortejaar
    "Thomas Leysen":                ("1960", None, True),
    "Familie Baert":                (None, None, True),
    "Familie Van Puijenbroek":      (None, None, True),
    "Chris Oomen":                  (None, None, True),
    "John de Mol":                  ("1955", None, True),
    "Maarten van Rossem":           ("1943", None, True),
    "Rob de Wijk":                  ("1954", None, True),     # geboortejaar, directeur HCSS
    "Ron Fresen":                   (None, None, True),
    "Willem Schinkel":              (None, None, True),
    "Peter R. de Vries":            ("1956", "2021", False),  # vermoord 2021
    # --- Politici ---
    "Pieter Omtzigt":               ("1974", None, True),
    "Renske Leijten":               ("1979", None, True),

    # --- Partijen ---
    "VVD":                          ("1948", None, True),
    "CDA":                          ("1980", None, True),
    "PVV":                          ("2006", None, True),
    "PvdA":                         ("1946", None, True),
    "SP":                           ("1972", None, True),
    "NSC (Nieuw Sociaal Contract)": ("2023", None, True),

    # --- Elite netwerken ---
    "Bilderberg Groep":             ("1954", None, True),
    "Trilaterale Commissie":        ("1973", None, True),
    "European Round Table of Industrialists": ("1983", None, True),
    "World Economic Forum":         ("1971", None, True),
    "European Publishers Council":  ("1991", None, True),

    # --- Bedrijven / Holdings ---
    "Groupe Bruxelles Lambert":     ("1902", None, True),
    "Epifin":                       (None, None, True),
    "VP Exploitatie":               (None, None, True),
    "Concentra":                    ("1880", None, True),     # Belgisch mediabedrijf (Hasselt)
    "Mediahuis Partners":           (None, None, True),
    "BlackRock":                    ("1988", None, True),
    "Vanguard":                     ("1975", None, True),
    "Talpa Network":                ("2004", None, True),
    "Shell":                        ("1907", None, True),
    "ING":                          ("1991", None, True),
    "ASML":                         ("1984", None, True),
    "Philips":                      ("1891", None, True),
    "dsm-firmenich":                ("2023", None, True),     # fusie 2023
    "KBC Groep":                    ("1998", None, True),
    "Umicore":                      ("1989", None, True),
    "McKinsey":                     ("1926", None, True),
    "Adidas":                       ("1949", None, True),
    "Imerys":                       ("1880", None, True),

    # --- Adverteerders ---
    "Albert Heijn":                 ("1887", None, True),
    "Lidl":                         ("1930", None, True),
    "Bol.com":                      ("1999", None, True),
    "Procter & Gamble":             ("1837", None, True),
    "Unilever":                     ("1929", None, True),
    "A.S. Watson (Kruidvat)":       ("1975", None, True),
    "Nederlandse Loterij":          ("2016", None, True),
    "Postcode Loterij":             ("1989", None, True),
    "Unibet":                       ("1997", None, True),

    # --- Techplatforms ---
    "Google":                       ("1998", None, True),
    "Meta (Facebook/Instagram)":    ("2004", None, True),
    "TikTok":                       ("2016", None, True),

    # --- Denktanks ---
    "Clingendael Instituut":        ("1983", None, True),
    "HCSS (The Hague Centre for Strategic Studies)": ("2007", None, True),
    "Nationale DenkTank":           ("2006", None, True),
    "Teldersstichting":             ("1954", None, True),
    "Wiardi Beckman Stichting":     ("1945", None, True),
    "UvA Journalistiek":            (None, None, True),

    # --- Overheidsinstanties ---
    "ACM (Autoriteit Consument & Markt)": ("2013", None, True),
    "WRR (Wetenschappelijke Raad voor het Regeringsbeleid)": ("1972", None, True),
    "CvdM (Commissariaat voor de Media)": ("1988", None, True),
    "Raad voor de Journalistiek":   ("1960", None, True),
    "Belastingdienst":              (None, None, True),
    "RIVM":                         ("1910", None, True),
    "CPB (Centraal Planbureau)":    ("1945", None, True),
    "Politie":                      (None, None, True),
    "Ministerie van Defensie":      ("1798", None, True),     # oprichting departement van Oorlog/Marine
    "Ministerie van Buitenlandse Zaken": ("1798", None, True),  # oprichting departement
    "Koningshuis":                  ("1815", None, True),     # Koninkrijk der Nederlanden
    "NAVO":                         ("1949", None, True),
    "OMT (Outbreak Management Team)": ("2020", "2023", False),  # opgeheven 2023
    "Tweede Kamer":                 ("1815", None, True),

    # --- NGO's ---
    "Free Press Unlimited":         ("2011", None, True),
    "NVJ (Nederlandse Vereniging van Journalisten)": ("1884", None, True),
    "BOinK":                        ("2001", None, True),

    # --- Historische bedrijven ---
    "PCM Uitgevers":                ("1965", "2009", False),  # opgegaan in DPG
    "Sanoma Nederland":             ("1999", "2020", False),  # overgenomen door DPG
    "VNU Media":                    ("1964", "2007", False),  # VNU opgericht 1964, overgenomen
    "TMG (Telegraaf Media Groep)":  ("1893", "2020", False),  # lijn De Telegraaf N.V., overgenomen door Mediahuis
    "NRC Media":                    ("2010", "2015", False),  # verzelfstandigd 2010, overgenomen door Mediahuis
    "De Persgroep":                 ("1945", "2019", False),  # hernoemd naar DPG Media

    # --- Overige bedrijven ---
    "KLM":                          ("1919", None, True),
    "Microsoft":                    ("1975", None, True),
    "KPMG":                         ("1987", None, True),     # fusie 1987
    "Ernst & Young":                ("1989", None, True),     # fusie 1989
    "Uber":                         ("2009", None, True),
    "Royal HaskoningDHV":           ("2012", None, True),     # fusie Royal Haskoning + DHV
    "Hill+Knowlton":                ("1927", None, True),

    # --- Overige politici / personen ---
    "Jan Peter Balkenende":         ("1956", None, True),     # geboortejaar
    "Neelie Kroes":                 ("1941", None, True),
    "Wouter Bos":                   ("1963", None, True),
    "Camiel Eurlings":              ("1973", None, True),
    "Hans Hillen":                  ("1947", None, True),
    "Frank Heemskerk":              ("1969", None, True),
    "Raymond Knops":                ("1971", None, True),
    "Eeke van der Veen":            ("1948", None, True),
    "Bart de Liefde":               ("1976", None, True),
    "Tijs van den Brink":           ("1976", None, True),
    "Jack de Vries":                ("1968", None, True),
    "Afke Schaart":                 ("1973", None, True),
}


# =============================================================================
# RELATIES: (source, target, relation_type, active_from, active_until, active)
# =============================================================================
RELATION_PERIODS = [
    # --- Historische eigendomsrelaties ---
    ("Chris Oomen", "ANP", "eigendom", "2021", None, True),
    ("Talpa Network", "ANP", "eigendom", "2014", "2021", False),  # verkocht aan Oomen
    ("John de Mol", "Talpa Network", "eigendom", "2004", None, True),

    # DPG overnames
    ("DPG Media", "PCM Uitgevers", "eigendom", "2009", None, True),  # PCM opgeslokt
    ("DPG Media", "Sanoma Nederland", "eigendom", "2020", None, True),
    ("DPG Media", "VNU Media", "eigendom", "2007", None, True),
    ("DPG Media", "RTL Nederland", "eigendom", "2023", None, True),  # recente overname
    ("PCM Uitgevers", "de Volkskrant", "eigendom", "1965", "2009", False),
    ("PCM Uitgevers", "Trouw", "eigendom", "1965", "2009", False),
    ("PCM Uitgevers", "AD (Algemeen Dagblad)", "eigendom", "1965", "2009", False),
    ("Sanoma Nederland", "NU.nl", "eigendom", "1999", "2020", False),
    ("TMG (Telegraaf Media Groep)", "De Telegraaf", "eigendom", None, "2020", False),

    # Mediahuis overnames
    ("Mediahuis", "TMG (Telegraaf Media Groep)", "eigendom", "2020", None, True),
    ("Mediahuis", "NRC Media", "eigendom", "2015", None, True),

    # Van Thillo → GBL
    ("Groupe Bruxelles Lambert", "Christian Van Thillo", "personeel", "2023", None, True),

    # Leysen posities
    ("Thomas Leysen", "dsm-firmenich", "personeel", "2023", None, True),
    ("Thomas Leysen", "KBC Groep", "personeel", None, "2020", False),  # voormalig
    ("Thomas Leysen", "Umicore", "personeel", None, "2019", False),    # voormalig

    # Bilderberg lidmaatschappen (Leysen is al lang lid)
    ("Bilderberg Groep", "Thomas Leysen", "lidmaatschap", None, None, True),
    ("Trilaterale Commissie", "Thomas Leysen", "lidmaatschap", None, None, True),
    ("European Round Table of Industrialists", "Thomas Leysen", "lidmaatschap", None, None, True),

    # Peter R. de Vries
    ("Peter R. de Vries", "NOS", "beinvloeding", "1956", "2021", False),
    ("Peter R. de Vries", "RTL Nederland", "beinvloeding", "1995", "2021", False),
    ("Peter R. de Vries", "De Telegraaf", "beinvloeding", None, "2021", False),
    ("Peter R. de Vries", "de Volkskrant", "beinvloeding", None, "2021", False),
    ("Peter R. de Vries", "AD (Algemeen Dagblad)", "beinvloeding", None, "2021", False),

    # Maarten van Rossem censuur (tijdelijk)
    ("NOS", "Maarten van Rossem", "censuur", "2003", "2010", False),  # na Irak tot ~2010

    # OMT (2020-2023)
    ("OMT (Outbreak Management Team)", "NOS", "beinvloeding", "2020", "2023", False),
    ("OMT (Outbreak Management Team)", "RTL Nederland", "beinvloeding", "2020", "2023", False),
    ("OMT (Outbreak Management Team)", "RIVM", "alliantie", "2020", "2023", False),
    ("RIVM", "NOS", "beinvloeding", "2020", "2022", False),  # corona peak
    ("RIVM", "RTL Nederland", "beinvloeding", "2020", "2022", False),
    ("RIVM", "DPG Media", "beinvloeding", "2020", "2022", False),

    # Irak-oorlog berichtgeving (2002-2003)
    ("CDA", "de Volkskrant", "beinvloeding", "2002", "2003", False),
    ("CDA", "De Telegraaf", "beinvloeding", "2002", "2003", False),
    ("CDA", "NRC", "beinvloeding", "2002", "2003", False),
    ("CDA", "NOS", "beinvloeding", "2002", "2003", False),

    # Omtzigt partijwissel
    ("CDA", "Pieter Omtzigt", "lidmaatschap", None, "2021", False),
    ("NSC (Nieuw Sociaal Contract)", "Pieter Omtzigt", "lidmaatschap", "2023", None, True),

    # Historische bedrijfsentiteiten
    ("De Persgroep", "DPG Media", "eigendom", "1945", "2019", False),

    # Ron Fresen bij NOS
    ("Ron Fresen", "NOS", "personeel", None, "2018", False),  # ging met pensioen ~2018

    # Brandpunt (gestopt 2017)
    # al in entity_periods

    # Metro (gestopt 2020)
    ("Mediahuis", "Metro", "eigendom", None, "2020", False),
    ("ANP", "Metro", "beinvloeding", None, "2020", False),
]


def update():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Update entities
    entity_updated = 0
    for name, (afrom, auntil, active) in ENTITY_PERIODS.items():
        cur.execute(
            "UPDATE entities SET active_from=?, active_until=?, active=? WHERE name=?",
            (afrom, auntil, active, name))
        if cur.rowcount > 0:
            entity_updated += 1

    # 2. Update relations
    # Build entity lookup
    cur.execute("SELECT id, name FROM entities")
    emap = {name: eid for eid, name in cur.fetchall()}

    rel_updated = 0
    for (src, tgt, rtype, afrom, auntil, active) in RELATION_PERIODS:
        sid = emap.get(src)
        tid = emap.get(tgt)
        if not sid or not tid:
            print(f"  WARN: {src} -> {tgt} niet gevonden")
            continue
        cur.execute(
            """UPDATE relations SET active_from=?, active_until=?, active=?
               WHERE source_id=? AND target_id=? AND relation_type=?""",
            (afrom, auntil, active, sid, tid, rtype))
        if cur.rowcount > 0:
            rel_updated += 1

    # 3. Afgeleide active_from voor resterende relaties zonder begindatum.
    #    Een relatie kan niet bestaan vóór beide betrokken entiteiten: neem het
    #    laatste (max) active_from van bron en doel. Overschrijft géén bestaande
    #    (handmatig gecureerde) waarden.
    cur.execute("""
        UPDATE relations
        SET active_from = (
            SELECT MAX(CAST(e.active_from AS INTEGER))
            FROM entities e
            WHERE e.id IN (relations.source_id, relations.target_id)
              AND e.active_from IS NOT NULL
        )
        WHERE active_from IS NULL
          AND (
            SELECT MAX(CAST(e.active_from AS INTEGER))
            FROM entities e
            WHERE e.id IN (relations.source_id, relations.target_id)
              AND e.active_from IS NOT NULL
          ) IS NOT NULL
    """)
    rel_derived = cur.rowcount

    conn.commit()

    # Stats
    cur.execute("SELECT COUNT(*) FROM entities WHERE active=0")
    inactive_e = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM relations WHERE active=0")
    inactive_r = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM entities WHERE active_from IS NOT NULL")
    dated_e = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM relations WHERE active_from IS NOT NULL")
    dated_r = cur.fetchone()[0]

    conn.close()

    print(f"\n{'='*60}")
    print(f"Temporele data ingevuld")
    print(f"{'='*60}")
    print(f"Entiteiten bijgewerkt:  {entity_updated}")
    print(f"Relaties bijgewerkt:    {rel_updated}")
    print(f"Relaties afgeleid:      {rel_derived}")
    print(f"{'='*60}")
    print(f"Entiteiten met datum:   {dated_e}")
    print(f"Relaties met datum:     {dated_r}")
    print(f"Inactieve entiteiten:   {inactive_e}")
    print(f"Inactieve relaties:     {inactive_r}")
    print(f"{'='*60}")


if __name__ == "__main__":
    update()
