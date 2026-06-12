"""Scoringsketen v2: van discussieboom naar theorie (verbeterplan fase 1).

Pure, stateless functies die de geloofwaardigheid en sterkte van het model afleiden uit
de onderliggende bewijslast. Geïmporteerd door zowel ``server.py`` (live herberekening) als
``scripts/generate_viz.py`` (statische snapshot in de visualisatie).

De keten kent drie lagen, plus vier dwarsmaatregelen uit het verbeterplan:

  Laag A   basiskracht τ per argument         -> argument_force()
  Boom     eindkracht σ per argument          -> DF-QuAD-propagatie (M1.1): replies
           dempen (ondergraving) of versterken hun parent; alleen ROOT-argumenten
           tellen voor het doel zelf.
  Laag B   afgeleide praktijkscore            -> instance_detail()   (relatie/entiteit)
  Laag C   theoriescore (rol/mechanisme/veld) -> theory_scores() / emergent_scores()

  M1.2  Bronclusters: binnen een cluster telt alleen het sterkste argument; combineren
        gebeurt over clusters. Argumenten zonder (echte) citatie delen per doel één
        pseudocluster — beweringen zonder bron zijn geen onafhankelijke bewijslijnen.
  M1.3  Onzekerheid: elk geloofwaardigheidscijfer krijgt een 95%-interval (Beta op de
        steun/tegen-massa's in laag B; bootstrap over instanties in laag C). Géén
        bewijs = score 0 zonder interval: de score meet onderbouwing, niet waarheid.
  M1.4  Tegenspraak-plafond: zonder overwogen tegenspraak (≥ 1 niet-verworpen
        contradicting-argument mét echte citatie) is de geloofwaardigheid gemaximeerd
        op CAP_ONWEERSPROKEN en draagt het element de vlag ``onweersproken``.
  M1.7  Invloed-as: aspect-argumenten met property='influence' verschuiven de afgeleide
        invloed; de handmatige kolom blijft de prior. Aspect-argumenten tellen nooit
        mee in de zekerheids-balans (twee assen, één bewijsstandaard).

Filosofie: pro-elite bias is een *emergente* eigenschap. Een theoretisch patroon wint aan
geloofwaardigheid naarmate (a) de literatuur het onderbouwt en (b) er meer en beter
onderbouwde concrete voorbeelden onder liggen. Geen enkele losse aanname is een "bewijs";
het geheel telt op — maar tien citaten uit hetzelfde boek zijn niet tien bewijzen.

Alle constanten staan hieronder en zijn bedoeld om bij te stellen;
``scripts/analyse_gevoeligheid.py`` (M1.6) rapporteert hoe gevoelig de conclusies ervoor zijn.

Naast de bewijslast levert ``compute_all_scores`` ook de *structurele* invloed-centraliteit
per entiteit (uit ``influence.py``) — geloofwaardigheid (bewijs) en invloedspositie
(topologie) zijn twee losse assen.
"""
from __future__ import annotations

import math
import random

import influence as influence_graph  # repo-root module: invloedsgraaf (topologie naast bewijslast)

# ── Instelbare constanten ────────────────────────────────────

# Hoe betrouwbaar weegt een brontype mee (Wikipedia-achtige hiërarchie).
RELIABILITY_WEIGHT = {
    "academisch": 1.00,            # peer-reviewed, proefschrift
    "primair": 0.95,              # origineel document, dataset, wetgeving
    "institutioneel": 0.85,       # WRR, CPB, ACM, SER
    "kwaliteitsjournalistiek": 0.70,
    "regulier": 0.50,             # dagblad, omroep, ANP
    "opinie": 0.35,               # column, essay
    "grijs": 0.20,                # blog, podcast, social media
    "eigen_synthese": 0.00,       # projectmateriaal: vindplaats, nooit bewijs (M1.2)
    "onbeoordeeld": 0.15,
}
DEFAULT_RELIABILITY = "onbeoordeeld"

# Verificatiestatus van een argument schaalt zijn bewijskracht.
STATUS_FACTOR = {
    "geverifieerd": 1.00,
    "ongecontroleerd": 0.50,
    "bronvermelding_nodig": 0.40,
    "verouderd": 0.40,
    "betwist": 0.25,
    "verworpen": 0.00,  # na review afgewezen: draagt geen bewijskracht meer
}
DEFAULT_STATUS_FACTOR = 0.50

DEFAULT_WEIGHT = 0.50      # argument zonder expliciet gewicht
NO_CITATION_FACTOR = 0.30  # bronfactor-ondergrens als een argument geen citaties heeft

K_INSTANCE = 1.0   # demping voor de afgeleide praktijkscore (laag B)
K_LIT = 1.0        # demping voor de literatuurcomponent (laag C)
K_AGG = 5.0        # volume-verzadiging voor de praktijkaggregatie (laag C)
K_INFLUENCE = 2.0  # demping van de bewijslijn op de invloed-as (M1.7)

CAP_ONWEERSPROKEN = 0.70      # M1.4: plafond zonder overwogen tegenspraak
CAP_ZONDER_COMPOSITIE = 0.50  # M1.5: plafond voor een hyperedge zonder compositieclaim
BOOTSTRAP_N = 200             # M1.3: aantal bootstrap-replicaties (laag C)

# Pseudocluster voor voor/tegen-argumenten zonder echte citatie (M1.2): die zijn
# onderling niet onafhankelijk, dus per doel telt alleen het sterkste ervan.
ZONDER_BRON_CLUSTER = "_zonder_bron"

# Aspect-properties die NIET over het bestaan van het doel gaan en dus buiten de
# zekerheids-balans blijven: invloedsbewijs (M1.7), padclaims, compositieclaims (M1.5).
ASPECT_PROPERTIES = ("influence", "indirecte_invloed_op", "compositie")


# ── Laag A: basiskracht τ per argument ───────────────────────

def reliability_weight(reliability: str | None) -> float:
    """Gewicht van een brontype; valt terug op 'onbeoordeeld'."""
    return RELIABILITY_WEIGHT.get(reliability or DEFAULT_RELIABILITY, RELIABILITY_WEIGHT[DEFAULT_RELIABILITY])


def source_factor(citation_reliabilities) -> float:
    """Bronfactor van een argument op basis van zijn sterkste citaat.

    Geen citaties -> NO_CITATION_FACTOR. Anders 0.3 + 0.7 * (beste reliabilitygewicht),
    zodat een goed gestaafd argument richting 1.0 gaat en een ongestaafd toch een beetje
    meetelt. Een 'eigen_synthese'-citaat weegt 0 en telt dus als ongestaafd.
    """
    weights = [reliability_weight(r) for r in (citation_reliabilities or [])]
    if not weights:
        return NO_CITATION_FACTOR
    return NO_CITATION_FACTOR + (1.0 - NO_CITATION_FACTOR) * max(weights)


def argument_force(weight, status, citation_reliabilities=None) -> float:
    """Basiskracht τ van één argument: weight x statusfactor x bronfactor."""
    w = DEFAULT_WEIGHT if weight is None else float(weight)
    s = STATUS_FACTOR.get(status, DEFAULT_STATUS_FACTOR)
    return w * s * source_factor(citation_reliabilities)


# ── Boomsemantiek (M1.1): DF-QuAD-propagatie van blad naar wortel ──

def dfquad_strength(tau: float, support_sigmas, attack_sigmas) -> float:
    """Eindkracht σ van een argument onder zijn reacties (DF-QuAD, Rago/Toni e.a. 2016).

    De steunende en aanvallende kinderen worden elk geaggregeerd met de
    probabilistische som ``1 - ∏(1 - σ_i)``; daarna moduleert het verschil de
    basiskracht: aanvallers trekken σ richting 0, steuners richting 1, in balans
    blijft τ. Een blad (geen kinderen) houdt σ = τ — een platte boom reproduceert
    dus exact de oude per-argument-krachten (regressie-eis M1.1).
    """
    s = a = 1.0
    for x in support_sigmas:
        s *= (1.0 - x)
    for x in attack_sigmas:
        a *= (1.0 - x)
    s, a = 1.0 - s, 1.0 - a
    if a > s:
        return tau * (1.0 - (a - s))
    if s > a:
        return tau + (1.0 - tau) * (s - a)
    return tau


def propagate_sigma(taus: dict, parents: dict, stances: dict) -> dict:
    """σ voor alle argumenten: kinderen eerst (post-order), dan de parent.

    taus    : {arg_id: τ}
    parents : {arg_id: parent_id of None}
    stances : {arg_id: stance} — de stance van een reply is relatief aan zijn parent:
              supporting versterkt, contradicting ondergraaft, contextual doet niets.
    """
    children = {}
    for aid, pid in parents.items():
        if pid is not None:
            children.setdefault(pid, []).append(aid)

    sigma = {}

    def rekenen(aid, gezien):
        if aid in sigma:
            return sigma[aid]
        if aid in gezien:           # cykel (hoort niet te kunnen): val terug op τ
            return taus[aid]
        gezien.add(aid)
        sup, att = [], []
        for kind in children.get(aid, ()):
            ks = rekenen(kind, gezien)
            if stances.get(kind) == "supporting":
                sup.append(ks)
            elif stances.get(kind) == "contradicting":
                att.append(ks)
        sigma[aid] = dfquad_strength(taus[aid], sup, att)
        return sigma[aid]

    for aid in taus:
        rekenen(aid, set())
    return sigma


# ── Laag B: clusterbalans + interval per doel ────────────────

def balance_from_roots(roots, k: float) -> dict:
    """Steun/tegen-balans over de ROOT-argumenten van één doel, met clusteraggregatie.

    ``roots`` is een lijst dicts met 'stance', 'sigma', 'cluster', 'n_citaties' en
    'status'. Binnen een (stance, cluster)-paar telt alleen de sterkste σ (M1.2);
    de massa's combineren als steun / (steun + tegen + k). Contextual telt niet mee.

    Retourneert {score|None, steun, tegen, n_steun_clusters, n_tegen_clusters,
    n_voor, n_tegen, overwogen_tegenspraak}.
    """
    per_cluster = {}
    n_voor = n_tegen = 0
    overwogen = False
    for r in roots:
        stance = r.get("stance")
        if stance not in ("supporting", "contradicting"):
            continue
        if stance == "supporting":
            n_voor += 1
        else:
            n_tegen += 1
            # M1.4: een serieuze tegenwerping is niet verworpen en draagt een echte bron.
            if r.get("status") != "verworpen" and (r.get("n_citaties") or 0) > 0:
                overwogen = True
        key = (stance, r.get("cluster") or ZONDER_BRON_CLUSTER)
        per_cluster[key] = max(per_cluster.get(key, 0.0), float(r.get("sigma") or 0.0))

    steun = sum(v for (st, _), v in per_cluster.items() if st == "supporting")
    tegen = sum(v for (st, _), v in per_cluster.items() if st == "contradicting")
    return {
        "score": None if not (n_voor or n_tegen) else steun / (steun + tegen + k),
        "steun": steun,
        "tegen": tegen,
        "n_steun_clusters": sum(1 for (st, _) in per_cluster if st == "supporting"),
        "n_tegen_clusters": sum(1 for (st, _) in per_cluster if st == "contradicting"),
        "n_voor": n_voor,
        "n_tegen": n_tegen,
        "overwogen_tegenspraak": overwogen,
    }


# Onvolledige beta-functie (regularized) + kwantiel, puur stdlib (M1.3).

def _betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-12, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def _betai(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_bt = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1.0 - x))
    bt = math.exp(ln_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def _beta_ppf(q, a, b):
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if _betai(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def beta_interval(steun: float, tegen: float, k: float) -> tuple:
    """95%-geloofwaardigheidsinterval voor de steunratio (M1.3).

    De steun/tegen-massa's zijn pseudo-tellingen voor een Beta-posterior met
    Jeffreys-achtige smoothing (+0,5); de demping k telt als tegenmassa, conform
    de puntscore steun/(steun+tegen+k). Weinig massa = breed interval.
    """
    a = steun + 0.5
    b = tegen + k + 0.5
    return (round(_beta_ppf(0.025, a, b), 4), round(_beta_ppf(0.975, a, b), 4))


def instance_detail(roots, prior_certainty=None, k: float = K_INSTANCE) -> dict:
    """Afgeleide geloofwaardigheid van een praktijk-instantie, met interval en vlaggen.

    Zonder voor/tegen-rootargumenten valt de score terug op de handmatige certainty
    (prior, bron='prior') of 0.0 (bron='geen'); het tegenspraak-plafond (M1.4) geldt
    óók voor de prior — een onweersproken aanname is niet zekerder dan 0,70.
    """
    bal = balance_from_roots(roots, k)
    if bal["score"] is None:
        score = float(prior_certainty) if prior_certainty is not None else 0.0
        lo = hi = score
        bron = "prior" if prior_certainty is not None else "geen"
    else:
        score = bal["score"]
        lo, hi = beta_interval(bal["steun"], bal["tegen"], k)
        bron = "bewijs"

    onweersproken = not bal["overwogen_tegenspraak"]
    capped = onweersproken and score > CAP_ONWEERSPROKEN
    if capped:
        score = CAP_ONWEERSPROKEN
        hi = score
    lo = min(lo, score)

    return {
        "score": round(score, 4),
        "lo": round(lo, 4),
        "hi": round(hi, 4),
        "bron": bron,
        "onweersproken": onweersproken,
        "capped": capped,
        "spof": bal["n_voor"] > 0 and bal["n_steun_clusters"] <= 1,
        "n_voor": bal["n_voor"],
        "n_tegen": bal["n_tegen"],
        "n_steun_clusters": bal["n_steun_clusters"],
    }


# ── Invloed-as (M1.7): bewijs verschuift de prior ────────────

def derived_influence(prior, influence_roots) -> dict:
    """Afgeleide invloed: handmatige kolom als prior, verschoven door aspect-argumenten.

    Een supporting-argument op property='influence' is bewijs dat de invloed sterk is,
    een contradicting-argument bewijs dat ze zwak is. De balans trekt de prior naar
    zich toe met gewicht massa/(massa + K_INFLUENCE) — weinig bewijs verschuift weinig.
    """
    bal = balance_from_roots(influence_roots, K_INSTANCE)
    if bal["score"] is None:
        return {"score": round(float(prior or 0.0), 4), "verschoven": False, "n_args": 0}
    massa = bal["steun"] + bal["tegen"]
    w = massa / (massa + K_INFLUENCE)
    basis = float(prior) if prior is not None else bal["score"]
    return {
        "score": round(basis * (1.0 - w) + bal["score"] * w, 4),
        "verschoven": True,
        "n_args": bal["n_voor"] + bal["n_tegen"],
    }


# ── Laag C: theoriescore per rol/mechanisme ──────────────────

def _noisy_or(a: float, b: float) -> float:
    """Twee onafhankelijke bewijslijnen versterken elkaar, verzadigend naar 1."""
    return 1.0 - (1.0 - a) * (1.0 - b)


def _praktijk_score(instances) -> float:
    """Geloofwaardigheid-gewogen aggregatie met volume-verzadiging (laag C)."""
    n_eff = sum(float(i.get("exemplarity", 1.0)) for i in instances)
    if n_eff <= 0:
        return 0.0
    weighted = sum(float(i.get("exemplarity", 1.0)) * float(i.get("certainty", 0.0))
                   for i in instances)
    return (weighted / n_eff) * (n_eff / (n_eff + K_AGG))


def _sterkte_score(instances) -> float:
    n_eff = sum(float(i.get("exemplarity", 1.0)) for i in instances)
    if n_eff <= 0:
        return 0.0
    denom = sum(float(i.get("exemplarity", 1.0)) * float(i.get("certainty", 0.0))
                for i in instances)
    if denom > 0:
        return sum(float(i.get("exemplarity", 1.0)) * float(i.get("certainty", 0.0))
                   * float(i.get("influence", 0.0)) for i in instances) / denom
    # Geen geloofwaardige instanties: val terug op exemplariteit-gewogen invloed
    return sum(float(i.get("exemplarity", 1.0)) * float(i.get("influence", 0.0))
               for i in instances) / n_eff


def theory_scores(literature_roots, instances, seed=0) -> dict:
    """Geloofwaardigheid en sterkte van een theoretisch element (rol/mechanisme).

    literature_roots : ROOT-argumenten (met σ/cluster) die direct op het element hangen.
    instances        : lijst dicts met 'exemplarity', 'certainty' (laag B) en 'influence'.

    Twee onafhankelijke lijnen (literatuur, praktijk) combineren met een noisy-OR.
    Het interval (M1.3) combineert het Beta-interval van de literatuurlijn met een
    bootstrap over de instanties; zonder bewijs op een lijn telt die lijn als 0
    zonder onzekerheid (de score meet onderbouwing, niet waarheid). Het
    tegenspraak-plafond (M1.4) kijkt naar de literatuurlijn van het element zelf.
    """
    bal = balance_from_roots(literature_roots, K_LIT)
    lit = bal["score"] or 0.0
    lit_lo, lit_hi = (beta_interval(bal["steun"], bal["tegen"], K_LIT)
                      if bal["score"] is not None else (0.0, 0.0))

    praktijk = _praktijk_score(instances)
    sterkte = _sterkte_score(instances)

    if instances:
        rng = random.Random(f"bootstrap:{seed}")
        samples = []
        for _ in range(BOOTSTRAP_N):
            steekproef = [instances[rng.randrange(len(instances))] for _ in instances]
            samples.append(_praktijk_score(steekproef))
        samples.sort()
        pr_lo = samples[int(0.025 * (BOOTSTRAP_N - 1))]
        pr_hi = samples[int(0.975 * (BOOTSTRAP_N - 1))]
    else:
        pr_lo = pr_hi = 0.0

    score = _noisy_or(lit, praktijk)
    lo = _noisy_or(lit_lo, pr_lo)
    hi = _noisy_or(lit_hi, pr_hi)

    onweersproken = not bal["overwogen_tegenspraak"]
    capped = onweersproken and score > CAP_ONWEERSPROKEN
    if capped:
        score = CAP_ONWEERSPROKEN
        hi = score
    lo = min(lo, score)

    return {
        "geloofwaardigheid": round(score, 4),
        "lo": round(lo, 4),
        "hi": round(hi, 4),
        "sterkte": round(sterkte, 4),
        "literatuur_geloofw": round(lit, 4),
        "praktijk_geloofw": round(praktijk, 4),
        "n_instanties": len(instances),
        "n_bronnen": bal["n_voor"] + bal["n_tegen"],
        "onweersproken": onweersproken,
        "capped": capped,
        "spof": bal["n_voor"] > 0 and bal["n_steun_clusters"] <= 1,
        "n_steun_clusters": bal["n_steun_clusters"],
    }


def emergent_scores(literature_roots, compositie_roots) -> dict:
    """Score van een emergent effect (hyperedge) uit twee bewijslijnen (M1.5).

    Literatuur op het effect zelf, plus — analoog aan padclaims — de verplichte
    COMPOSITIECLAIM (property='compositie'): bewijs dat het *samenspel* bestaat, niet
    alleen dat de leden bestaan. Zonder compositieclaim is de geloofwaardigheid
    gemaximeerd op CAP_ZONDER_COMPOSITIE en draagt het veld een zichtbare vlag.
    Een veld heeft geen praktijk-instanties; zijn praktijk leeft in de mechanismen
    en rollen eronder.
    """
    lit_bal = balance_from_roots(literature_roots, K_LIT)
    comp_bal = balance_from_roots(compositie_roots, K_LIT)
    lit = lit_bal["score"] or 0.0
    comp = comp_bal["score"] or 0.0
    lit_lo, lit_hi = (beta_interval(lit_bal["steun"], lit_bal["tegen"], K_LIT)
                      if lit_bal["score"] is not None else (0.0, 0.0))
    comp_lo, comp_hi = (beta_interval(comp_bal["steun"], comp_bal["tegen"], K_LIT)
                        if comp_bal["score"] is not None else (0.0, 0.0))

    score = _noisy_or(lit, comp)
    lo = _noisy_or(lit_lo, comp_lo)
    hi = _noisy_or(lit_hi, comp_hi)

    zonder_compositie = comp_bal["score"] is None
    onweersproken = not (lit_bal["overwogen_tegenspraak"] or comp_bal["overwogen_tegenspraak"])
    capped = False
    if onweersproken and score > CAP_ONWEERSPROKEN:
        score, hi, capped = CAP_ONWEERSPROKEN, CAP_ONWEERSPROKEN, True
    if zonder_compositie and score > CAP_ZONDER_COMPOSITIE:
        score, hi, capped = CAP_ZONDER_COMPOSITIE, CAP_ZONDER_COMPOSITIE, True
    lo = min(lo, score)

    n_steun_clusters = lit_bal["n_steun_clusters"] + comp_bal["n_steun_clusters"]
    n_voor = lit_bal["n_voor"] + comp_bal["n_voor"]
    return {
        "geloofwaardigheid": round(score, 4),
        "lo": round(lo, 4),
        "hi": round(hi, 4),
        "literatuur_geloofw": round(lit, 4),
        "compositie_geloofw": round(comp, 4),
        "n_bronnen": lit_bal["n_voor"] + lit_bal["n_tegen"],
        "n_compositie": comp_bal["n_voor"] + comp_bal["n_tegen"],
        "zonder_compositieclaim": zonder_compositie,
        "onweersproken": onweersproken,
        "capped": capped,
        "spof": n_voor > 0 and n_steun_clusters <= 1,
    }


# ── DB-aggregatie: alle afgeleide scores in één keer ────────

def compute_all_scores(conn, exclude_cluster=None) -> dict:
    """Bereken de volledige scoringsketen uit een SQLite-connectie.

    Retourneert (gekeyd op id):
      relations / entities                : kale afgeleide zekerheid (compat met de viz)
      relations_detail / entities_detail  : score + interval + vlaggen (M1.2–M1.4)
      relations_influence(_detail)        : afgeleide invloed per relatie (M1.7)
      roles / mechanisms                  : theoriescores (laag C) + interval + vlaggen
      emergent_effects                    : hyperedge-scores (M1.5)
      argument_scores                     : {id: {tau, sigma}} (M1.1, voor de viz)
      entity_influence* / role_influence* : structurele centraliteit (influence.py)

    ``exclude_cluster`` laat alle citaties uit één broncluster weg — de basis van de
    leave-one-cluster-out-analyse (scripts/analyse_gevoeligheid.py, M1.6).

    Gedeeld door scripts/generate_viz.py (statische snapshot) en de /api/scores-endpoint
    (live herberekening), zodat de aggregatielogica op één plek staat.
    """
    # Citaties per argument: (reliability, cluster). NULL-cluster = eigen cluster per bron.
    cites_by_arg = {}
    for arg_id, reliability, cluster, source_id in conn.execute("""
            SELECT c.argument_id, s.reliability, s.cluster_key, s.id
            FROM citations c JOIN sources s ON c.source_id = s.id"""):
        key = cluster or f"bron{source_id}"
        if exclude_cluster is not None and key == exclude_cluster:
            continue
        cites_by_arg.setdefault(arg_id, []).append((reliability, key))

    # Alle argumenten: τ berekenen en de boom opzetten (M1.1)
    taus, parents, stances, meta = {}, {}, {}, {}
    for (aid, rel_id, ent_id, role_id, mech_id, eff_id, parent_id,
         prop, stance, weight, status) in conn.execute("""
            SELECT id, relation_id, entity_id, role_id, mechanism_id, emergent_effect_id,
                   parent_argument_id, property, stance, weight, status FROM arguments"""):
        cites = cites_by_arg.get(aid, [])
        taus[aid] = argument_force(weight, status, [r for r, _ in cites])
        parents[aid] = parent_id
        stances[aid] = stance
        # Cluster van het argument: dat van zijn zwaarste échte citatie (gewicht > 0);
        # zonder echte citatie deelt het het pseudocluster (M1.2).
        echte = [(reliability_weight(r), cl) for r, cl in cites if reliability_weight(r) > 0]
        cluster = max(echte)[1] if echte else ZONDER_BRON_CLUSTER
        meta[aid] = {"relation_id": rel_id, "entity_id": ent_id, "role_id": role_id,
                     "mechanism_id": mech_id, "emergent_effect_id": eff_id,
                     "property": prop, "stance": stance, "status": status,
                     "cluster": cluster, "n_citaties": len(echte)}

    sigma = propagate_sigma(taus, parents, stances)
    argument_scores = {aid: {"tau": round(taus[aid], 4), "sigma": round(sigma[aid], 4)}
                       for aid in taus}

    # ROOT-argumenten groeperen per doel en per lijn (zekerheid / invloed / compositie)
    by_relation, by_rel_influence = {}, {}
    by_entity, by_role, by_mech, by_mech_influence = {}, {}, {}, {}
    by_eff, by_eff_comp = {}, {}
    for aid, m in meta.items():
        if parents[aid] is not None:      # replies tellen alleen via de boom (M1.1)
            continue
        payload = {"stance": m["stance"], "sigma": sigma[aid], "cluster": m["cluster"],
                   "n_citaties": m["n_citaties"], "status": m["status"]}
        prop = m["property"]
        if m["relation_id"]:
            if prop == "influence":
                by_rel_influence.setdefault(m["relation_id"], []).append(payload)
            elif prop not in ASPECT_PROPERTIES:
                by_relation.setdefault(m["relation_id"], []).append(payload)
        if m["entity_id"] and prop not in ASPECT_PROPERTIES:
            by_entity.setdefault(m["entity_id"], []).append(payload)
        if m["role_id"] and prop not in ASPECT_PROPERTIES:
            # Padclaims (property 'indirecte_invloed_op') onderbouwen een afgeleide
            # pijl rol ⇢ rol, niet de rol zelf — buiten de rolscore houden.
            by_role.setdefault(m["role_id"], []).append(payload)
        if m["mechanism_id"]:
            if prop == "influence":
                by_mech_influence.setdefault(m["mechanism_id"], []).append(payload)
            elif prop not in ASPECT_PROPERTIES:
                by_mech.setdefault(m["mechanism_id"], []).append(payload)
        if m["emergent_effect_id"]:
            if prop == "compositie":
                by_eff_comp.setdefault(m["emergent_effect_id"], []).append(payload)
            elif prop not in ASPECT_PROPERTIES:
                by_eff.setdefault(m["emergent_effect_id"], []).append(payload)

    # Laag B: afgeleide praktijkscore + afgeleide invloed per relatie
    rel_rows = conn.execute(
        "SELECT id, source_id, target_id, certainty, influence FROM relations").fetchall()
    rel_detail, rel_infl_detail = {}, {}
    ent_cert_acc, ent_infl_acc = {}, {}
    for rid, src, tgt, certainty, influence in rel_rows:
        detail = instance_detail(by_relation.get(rid, []), prior_certainty=certainty)
        rel_detail[rid] = detail
        infl = derived_influence(influence, by_rel_influence.get(rid, []))
        rel_infl_detail[rid] = infl
        for eid in (src, tgt):
            ent_cert_acc.setdefault(eid, []).append(detail["score"])
            ent_infl_acc.setdefault(eid, []).append(infl["score"])
    ent_infl = {eid: (sum(v) / len(v) if v else 0.0) for eid, v in ent_infl_acc.items()}

    # Afgeleide geloofwaardigheid per entiteit (prior = gem. zekerheid van haar relaties)
    entity_detail = {}
    for (eid,) in conn.execute("SELECT id FROM entities"):
        rel_cert = ent_cert_acc.get(eid)
        prior = (sum(rel_cert) / len(rel_cert)) if rel_cert else None
        entity_detail[eid] = instance_detail(by_entity.get(eid, []), prior_certainty=prior)

    # Instanties per klasse uit de koppeltabel (invloed = afgeleide invloed, M1.7)
    role_instances, mech_instances = {}, {}
    for role_id, mech_id, ent_id, rel_id, exemplarity in conn.execute(
            "SELECT role_id, mechanism_id, entity_id, relation_id, exemplarity FROM instantiations"):
        ex = exemplarity if exemplarity is not None else 1.0
        if role_id and ent_id:
            role_instances.setdefault(role_id, []).append({
                "exemplarity": ex, "certainty": entity_detail.get(ent_id, {}).get("score", 0.0),
                "influence": ent_infl.get(ent_id, 0.0)})
        elif mech_id and rel_id:
            mech_instances.setdefault(mech_id, []).append({
                "exemplarity": ex, "certainty": rel_detail.get(rel_id, {}).get("score", 0.0),
                "influence": rel_infl_detail.get(rel_id, {}).get("score", 0.0)})

    roles = {role_id: theory_scores(by_role.get(role_id, []),
                                    role_instances.get(role_id, []), seed=f"rol{role_id}")
             for (role_id,) in conn.execute("SELECT id FROM roles")}
    mechs = {}
    for (mech_id,) in conn.execute("SELECT id FROM mechanisms"):
        scores = theory_scores(by_mech.get(mech_id, []),
                               mech_instances.get(mech_id, []), seed=f"mech{mech_id}")
        # M1.7: invloedsbewijs op het mechanisme zelf verschuift de sterkte
        # (zo krijgt ook halo-sterkte een eigen bewijslijn, M1.5).
        infl = derived_influence(scores["sterkte"], by_mech_influence.get(mech_id, []))
        scores["sterkte"] = infl["score"]
        scores["sterkte_bewijs_args"] = infl["n_args"]
        mechs[mech_id] = scores

    # Emergente velden (M1.5): eersteklas theorie-elementen met eigen discussieboom.
    effs = {}
    if conn.execute("SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name='emergent_effects'").fetchone():
        effs = {eff_id: emergent_scores(by_eff.get(eff_id, []), by_eff_comp.get(eff_id, []))
                for (eff_id,) in conn.execute("SELECT id FROM emergent_effects")}

    # Structurele invloed-centraliteit (topologie, los van de bewijslast):
    #   - entiteiten: relatiegraaf, gewicht = influence.
    #   - rollen: mechanismegraaf, gewicht = sterkte van het mechanisme (theorie-laag).
    # Twee varianten: 'clean' (exclude) = schone dyadische graaf (default-view in de viz, toggle
    # uit); 'collapse' = eerlijk met veld-effecten, fan-out gedempt (toggle aan, en de API-default).
    entity_influence = influence_graph.compute_influence(conn, field_mode="collapse")
    entity_influence_clean = influence_graph.compute_influence(conn, field_mode="exclude")

    role_ids = [r[0] for r in conn.execute("SELECT id FROM roles")]
    mech_edges = []
    for mid, src_role, tgt_role, flt, aard in conn.execute(
            "SELECT id, source_role_id, target_role_id, filter, aard FROM mechanisms"):
        if flt == "tegenmacht":     # tegenkracht: geen pro-elite invloedskanaal
            continue
        mech_edges.append((src_role, tgt_role,
                           mechs.get(mid, {}).get("sterkte", 0.0), aard or "direct"))

    def _role_ids(*role_names):
        ids = set()
        for rn in role_names:
            row = conn.execute("SELECT id FROM roles WHERE name = ?", (rn,)).fetchone()
            if row:
                ids.add(row[0])
        return ids

    target_role_sets = {}
    if (pub := _role_ids("publiek")):
        target_role_sets["public"] = pub
    if (pol := _role_ids("politicus", "partij")):
        target_role_sets["politiek"] = pol
    role_influence = influence_graph.compute_role_influence(
        role_ids, mech_edges, target_role_sets=target_role_sets, field_mode="collapse")
    role_influence_clean = influence_graph.compute_role_influence(
        role_ids, mech_edges, target_role_sets=target_role_sets, field_mode="exclude")

    return {
        "relations": {rid: d["score"] for rid, d in rel_detail.items()},
        "relations_detail": rel_detail,
        "relations_influence": {rid: d["score"] for rid, d in rel_infl_detail.items()},
        "relations_influence_detail": rel_infl_detail,
        "entities": {eid: d["score"] for eid, d in entity_detail.items()},
        "entities_detail": entity_detail,
        "entity_influence": entity_influence,
        "entity_influence_clean": entity_influence_clean,
        "role_influence": role_influence,
        "role_influence_clean": role_influence_clean,
        "roles": roles,
        "mechanisms": mechs,
        "emergent_effects": effs,
        "argument_scores": argument_scores,
    }


# ── CLI-sanity ───────────────────────────────────────────────

def _cli():  # pragma: no cover - handmatige inspectie
    import sqlite3
    from pathlib import Path

    db = Path(__file__).parent / "data" / "propaganda_model.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    scores = compute_all_scores(conn)

    print("== Afgeleide praktijkscore (laag B) voor enkele relaties ==")
    for r in conn.execute("SELECT id, certainty FROM relations LIMIT 5"):
        d = scores["relations_detail"][r["id"]]
        vlag = " [onweersproken]" if d["onweersproken"] else ""
        print(f"  relatie {r['id']:>4}: handmatig {r['certainty']}  ->  "
              f"afgeleid {d['score']:.3f} [{d['lo']:.2f}-{d['hi']:.2f}]{vlag}")

    print("\n== Theoriescore (laag C) voor top-mechanismen ==")
    rows = conn.execute("""
        SELECT m.id, m.name, COUNT(r.id) n FROM mechanisms m
        JOIN relations r ON r.mechanism_id = m.id
        GROUP BY m.id ORDER BY n DESC LIMIT 5
    """).fetchall()
    for m in rows:
        s = scores["mechanisms"][m["id"]]
        vlag = " [onweersproken]" if s["onweersproken"] else ""
        spof = " [1 broncluster]" if s["spof"] else ""
        print(f"  {m['name']:<28} n={m['n']:>2}  geloofw={s['geloofwaardigheid']:.3f} "
              f"[{s['lo']:.2f}-{s['hi']:.2f}]  sterkte={s['sterkte']:.3f}{vlag}{spof}")

    print("\n== Emergente effecten (M1.5) ==")
    for e in conn.execute("SELECT id, label FROM emergent_effects ORDER BY id"):
        s = scores["emergent_effects"][e["id"]]
        comp = ("zonder compositieclaim" if s["zonder_compositieclaim"]
                else f"compositie {s['compositie_geloofw']:.2f}")
        print(f"  {e['label']:<40} geloofw={s['geloofwaardigheid']:.3f} ({comp})")

    conn.close()


if __name__ == "__main__":
    _cli()
