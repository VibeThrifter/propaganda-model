"""Semantische dedup — stdlib-tussenlaag bovenop difflib (story A6).

Doel: bijna-duplicaat-claims herkennen ook als de bewoording verschilt
(herordening, synoniemarme parafrase) — precies wat
`difflib.SequenceMatcher` mist. Puur stdlib, geen dependency, geen netwerk.

Aanroeppunt voor de server::

    from dedup import gelijkenis
    score = gelijkenis(nieuwe_claim, bestaande_claim)   # 0.0 .. 1.0
    # kandidaat als max(difflib_ratio, score) >= DREMPEL

Aanbevolen drempel: **0.80** (zie `DREMPEL`). De server blokkeert hard op de
goedkope lagen (difflib 0.85 blijft, token-cosine 0.80); echte-embedding-dups
(een aparte, offline `scripts/embed_claims.py` — NIET deze module) worden
gevlagd, niet geblokkeerd.

De score combineert twee signalen die complementair falen:
  1. token-set-cosine over unigrammen na normalisatie — bag-of-words, dus
     woordvolgorde-invariant: vangt herordening en synoniemarme parafrase die
     `difflib` (sequentie-gebaseerd) juist mist;
  2. karakter-n-gram Jaccard (trigrammen) — vangt spelvarianten, verbuiging en
     stam-verschillen die de woord-laag als "ander woord" ziet.
De eindscore is een gewogen combinatie (woord-laag weegt zwaarder omdat
betekenis vooral in woorden zit; de karakter-laag is het robuustheidsvangnet).
Bewust géén geordende bigrammen in de kern-score: die zouden precies de
herordening bestraffen die we juist willen herkennen.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

# Aanbevolen drempel voor de server: max(difflib_ratio, gelijkenis) >= DREMPEL.
DREMPEL = 0.80

# Weging tussen de woord-cosine en de karakter-Jaccard.
_WOORD_GEWICHT = 0.65
_KARAKTER_GEWICHT = 0.35

# Nederlandse stopwoorden — bewust compact: lidwoorden, voegwoorden,
# voornaamwoorden, hulpwerkwoorden en veelvoorkomende functiewoorden. Te veel
# stopwoorden strippen betekenis; dit is de gangbare kernlijst.
_STOPWOORDEN = frozenset("""
de het een en of maar want dus als dan toen omdat zodat terwijl hoewel
van voor naar met bij uit over onder tussen tegen door om aan op in te
ten ter tot per sinds tijdens binnen buiten zonder
ik jij je hij zij ze wij we jullie u men die dat deze dit welke wie wat
mijn jouw zijn haar hun ons onze uw
is zijn ben bent was waren wordt worden werd werden word
heb hebt heeft hebben had hadden
zal zullen zou zouden kan kunnen kon konden mag mogen moet moeten
niet geen wel ook nog al reeds nu toen hier daar er
zeer heel erg meer meest veel weinig zo dan dus toch echter
""".split())

# Veelvoorkomende NL-uitgangen voor lichte stam-normalisatie. Volgorde =
# lang-naar-kort zodat de langste match eerst wint. Bewust conservatief: alleen
# echt frequente flexie-/afleidingsuitgangen, met een minimale stamlengte zodat
# korte woorden niet weggeknabbeld worden.
_UITGANGEN = (
    "heden", "ingen", "tie", "isch", "lijk", "baar", "loos",
    "ing", "en", "er", "st", "te", "de", "je", "es", "s", "e",
)
_MIN_STAM = 4


def _strip_accenten(tekst: str) -> str:
    genormaliseerd = unicodedata.normalize("NFKD", tekst)
    return "".join(c for c in genormaliseerd if not unicodedata.combining(c))


def _stam(woord: str) -> str:
    """Lichte, robuuste stam-normalisatie: knip één bekende uitgang af."""
    for uitgang in _UITGANGEN:
        if woord.endswith(uitgang) and len(woord) - len(uitgang) >= _MIN_STAM:
            return woord[: -len(uitgang)]
    return woord


def normaliseer(tekst: str) -> list[str]:
    """Lowercase → accenten weg → tokenizen → stopwoorden weg → stammen."""
    tekst = _strip_accenten(tekst.lower())
    # Houd letters en cijfers; alles anders wordt woordgrens.
    ruw = re.findall(r"[a-z0-9]+", tekst)
    tokens = [_stam(w) for w in ruw if w not in _STOPWOORDEN and len(w) > 1]
    return tokens


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    gemeen = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in gemeen)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _char_ngrams(tokens: list[str], n: int = 3) -> set[str]:
    """Karakter-n-grammen over de samengevoegde tokenstroom."""
    basis = " ".join(tokens)
    if len(basis) < n:
        return {basis} if basis else set()
    return {basis[i : i + n] for i in range(len(basis) - n + 1)}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def gelijkenis(a: str, b: str) -> float:
    """Semantische gelijkenis in [0.0, 1.0]; 1.0 = (na normalisatie) identiek.

    Combineert woord-set-cosine (herordening/parafrase) met karakter-trigram
    Jaccard (spel-/verbuigingsvarianten). Pure stdlib.
    """
    if a is None or b is None:
        return 0.0
    ta = normaliseer(a)
    tb = normaliseer(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0

    woord = _cosine(Counter(ta), Counter(tb))
    karakter = _jaccard(_char_ngrams(ta), _char_ngrams(tb))
    score = _WOORD_GEWICHT * woord + _KARAKTER_GEWICHT * karakter
    # Numerieke veiligheid: klem in [0, 1].
    return max(0.0, min(1.0, score))
