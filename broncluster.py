"""Broncluster (M1.2): welke bronnen delen auteur, uitgever of onderliggende data.

Binnen één cluster telt in scoring.py alleen het sterkste argument. `cluster_key_voor`
leidt de sleutel af wanneer een nieuwe bron er geen meekrijgt (POST /api/sources en
scripts/register_source.py). De regel kwam uit de eenmalige migratie
migrate_scoring_v2.py (zie git-geschiedenis, vóór 2026-10-13). Stdlib-only.
"""
import re
import unicodedata

# Sleutel: genormaliseerde auteursnaam (of uitgever als auteur leeg is).
# OVERRIDES vangt varianten en bekende verwantschappen; alles wat hierbuiten valt
# clustert op de eigen genormaliseerde naam (en is dus zijn eigen cluster).
OVERRIDES = {
    # zelfde organisatie, andere schrijfwijze
    "acm": "acm",
    "autoriteit consument & markt": "acm",
    "eib": "eib",
    "europese investeringsbank": "eib",
    "follow the money": "follow_the_money",
    # de Rijksoverheid-familie: zelfde afzender (regering), zelfde belang
    "rijksoverheid": "rijksoverheid",
    "ministerie van algemene zaken / ministerie van financien": "rijksoverheid",
    "ministerie van financien": "rijksoverheid",
    "rutte, m. & de jonge, h.": "rijksoverheid",
    # wetgever apart van de regering
    "staten-generaal": "staten_generaal",
    # zelfde auteurschap/advocacy-lijn: Herman & Chomsky en Chomsky solo
    "herman, e.s. & chomsky, n.": "chomsky",
    "chomsky, n.": "chomsky",
    # NOS-berichten clusteren op het onderliggende onderzoek waar dat benoemd is
    "nos, naar onderzoek van nrc": "nrc",
    "nos, naar onderzoek van de volkskrant": "volkskrant",
    "anp / nos nieuws": "nos",
    "nos": "nos",
    # Boumans is (mede)auteur van beide sourcing-studies: zelfde onderliggende lijn
    "boumans, j.": "boumans",
    "boumans, j., trilling, d., vliegenthart, r. & boomgaarden, h.": "boumans",
    # RVS-rapport en -profielpagina
    "raad voor volksgezondheid & samenleving": "rvs",
}


def _normaliseer(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def _slug(s):
    s = _normaliseer(s)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or None


def cluster_key_voor(author, publisher):
    """Afleidregel voor de broncluster (sources.cluster_key) uit auteur of uitgever."""
    basis = _normaliseer(author) or _normaliseer(publisher)
    if not basis:
        return None
    if basis in OVERRIDES:
        return OVERRIDES[basis]
    # personen: cluster op de eerste auteursachternaam ("Vasterman, P." -> vasterman)
    if "," in basis and not basis.startswith(("ministerie", "raad ", "commissie")):
        eerste = basis.split("&")[0].split(",")[0]
        return _slug(eerste)
    return _slug(basis)
