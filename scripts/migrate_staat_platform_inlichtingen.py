#!/usr/bin/env python3
"""
Migratie: staat/EU als inhoudsmoderator + inlichtingen-cooptatie + EIB-geldstroom.

Voegt de geverifieerde verbanden toe die volgen uit het transcript "Meeswijs"
(juni 2026) na brononderzoek. Twee nieuwe mechanismen (theorielaag) en negen
entiteiten met bijbehorende relaties, verfijningen, bronnen en argumenten
(praktijklaag). Alleen wat de toets doorstaat is opgenomen; de scores coderen de
resterende onzekerheid (lage influence waar het kanaal bestaat maar de
berichtgeving niet aantoonbaar stuurt).

Conform repo-conventie: eerst backup (data/propaganda_model_backup_<ts>.db),
dan muteren. Idempotent op naam (entities/mechanisms/sources uniek per naam/titel).
"""
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "onderzoek-meeswijs-2026-06"


def backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = DB.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB, dst)
    print(f"backup -> {dst.name}")


def main():
    backup()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    def role_id(name):
        r = cur.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
        if not r:
            raise SystemExit(f"rol ontbreekt: {name}")
        return r[0]

    def mech_id(name):
        r = cur.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
        return r[0] if r else None

    def entity_id(name):
        r = cur.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()
        return r[0] if r else None

    # ---- THEORIELAAG: twee nieuwe mechanismen ------------------------------
    def add_mechanism(name, prim_filter, mtype, desc, effect, src_role, tgt_role,
                      aard, filters, themes):
        if mech_id(name):
            print(f"mechanisme bestaat al: {name}")
            return mech_id(name)
        cur.execute(
            """INSERT INTO mechanisms
               (name, filter, mechanism_type, description, effect,
                source_role_id, target_role_id, aard)
               VALUES (?,?,?,?,?,?,?,?)""",
            (name, prim_filter, mtype, desc, effect,
             role_id(src_role), role_id(tgt_role), aard),
        )
        mid = cur.lastrowid
        for f in filters:
            cur.execute("INSERT OR IGNORE INTO mechanism_filters VALUES (?,?)", (mid, f))
        for t in themes:
            cur.execute("INSERT OR IGNORE INTO mechanism_themes VALUES (?,?)", (mid, t))
        print(f"+ mechanisme {name} (filter={prim_filter}, aard={aard})")
        return mid

    add_mechanism(
        "statelijke_inhoudsmoderatie", "flak", "procedureel",
        "Een overheids- of supranationaal gezagsinstituut zet techplatforms onder "
        "druk om legale maar 'ongewenste' content te modereren, demoten of "
        "verwijderen — via trusted-flagger-status, verkiezingsoverleggen en "
        "'borderline content'-handboeken. Raakt Flak (disciplinering van publieke "
        "uitingen) en Ideologie (spectrumbewaking).",
        "Bepaalde uitingen (o.a. anti-elite, populistisch, electoraal) bereiken het "
        "publiek beperkter; de grens van het zegbare verschuift buiten de redactie "
        "om, op platformniveau.",
        "gezagsinstituut", "techplatform", "direct",
        ["flak", "ideologie"], ["platform"],
    )

    add_mechanism(
        "inlichtingen_cooptatie", "sourcing", "structureel",
        "Een inlichtingen-/veiligheidsdienst benadert of werft journalisten als "
        "bron of agent. Compromitteert de onafhankelijkheid van de bronvergaarder "
        "(Sourcing) en disciplineert/ondermijnt de geloofwaardigheid van het vak "
        "(Flak).",
        "Vervlechting van pers en staatsapparaat; journalisten worden (deels) "
        "instrument van staatsbelang, wat zelfcensuur en bronafhankelijkheid "
        "versterkt.",
        "gezagsinstituut", "journalist", "direct",
        ["sourcing", "flak"], [],
    )

    # ---- PRAKTIJKLAAG: nieuwe entiteiten -----------------------------------
    def add_entity(name, etype, prim_role, desc, meta=None, active_from=None):
        eid = entity_id(name)
        if eid:
            print(f"entiteit bestaat al: {name}")
        else:
            cur.execute(
                """INSERT INTO entities
                   (name, type, primary_role_id, description, metadata, active_from)
                   VALUES (?,?,?,?,?,?)""",
                (name, etype, role_id(prim_role), desc,
                 json.dumps(meta or {"bron": CONTRIB}), active_from),
            )
            eid = cur.lastrowid
            print(f"+ entiteit {name} ({etype}/{prim_role})")
        # rol-koppeling + instantiation (rol<->entiteit)
        rid = role_id(prim_role)
        cur.execute("INSERT OR IGNORE INTO entity_roles (entity_id, role_id) VALUES (?,?)",
                    (eid, rid))
        have = cur.execute(
            "SELECT 1 FROM instantiations WHERE role_id=? AND entity_id=?",
            (rid, eid)).fetchone()
        if not have:
            cur.execute(
                "INSERT INTO instantiations (role_id, entity_id, exemplarity, notes) "
                "VALUES (?,?,?,?)", (rid, eid, 0.7, CONTRIB))
        return eid

    add_entity("Europese Commissie", "overheidsinstelling", "gezagsinstituut",
        "Uitvoerend orgaan van de EU. Coordineert via de Code of Practice on "
        "Disinformation en het EU Internet Forum platformmoderatie, met "
        "intensivering rond verkiezingen (100+ overleggen 2022-2024).")
    add_entity("Ministerie van Binnenlandse Zaken", "overheidsinstelling", "gezagsinstituut",
        "NL-ministerie (BZK). Heeft 'trusted flagger'-status bij vijf platforms: "
        "Facebook/Meta en Twitter sinds 2019, Google/TikTok/Snapchat sinds 2021. "
        "Volgens de minister 'met grote terughoudendheid' en alleen rond "
        "verkiezingen ingezet.")
    add_entity("AIVD", "overheidsinstelling", "gezagsinstituut",
        "Algemene Inlichtingen- en Veiligheidsdienst. NRC/Volkskrant-onderzoek "
        "(2024): diensten benaderden journalisten als bron/agent; intern "
        "AIVD-document noemde 8 journalisten onder 21 'bronnen en agenten'.")
    add_entity("MIVD", "overheidsinstelling", "gezagsinstituut",
        "Militaire Inlichtingen- en Veiligheidsdienst. Benadert journalisten/"
        "correspondenten in voor de dienst relevante regio's (NRC/Volkskrant 2024).")
    add_entity("X (Twitter)", "platform", "techplatform",
        "Microbloggingplatform (voorheen Twitter). Een van de vijf platforms met "
        "BZK trusted-flagger-status (sinds 2019).")
    add_entity("Snapchat", "platform", "techplatform",
        "Berichten-/socialmediaplatform. Een van de vijf platforms met BZK "
        "trusted-flagger-status (sinds 2021).")
    add_entity("Open Society Foundations", "ngo", "belanghebbende",
        "Filantropisch netwerk van George Soros (aard: ideologisch). Cofinancierde "
        "in 2016 met Stichting Democratie en Media een programma tegen structurele "
        "discriminatie van moslims (OSF Initiative for Europe).")
    add_entity("ECB (Europese Centrale Bank)", "overheidsinstelling", "gezagsinstituut",
        "Eurosysteem. Veruit grootste institutionele opkoper van EIB-obligaties "
        "(~EUR 100 mld; EIB = >40% van QE-waardig supranationaal schuldpapier). "
        "Geen aandeelhouder maar systemische financier achter de EIB-leencapaciteit.")
    add_entity("Sinan Can", "persoon", "journalist",
        "Documentairemaker/journalist (o.a. conflictregio's). Sprak publiek over "
        "benadering door een inlichtingendienst (NRC/Volkskrant 2024).")

    # ---- PRAKTIJKLAAG: nieuwe relaties -------------------------------------
    def find_relation(src, tgt, rel_type=None, mech=None):
        q = "SELECT id FROM relations WHERE source_id=? AND target_id=?"
        p = [entity_id(src), entity_id(tgt)]
        if rel_type:
            q += " AND relation_type=?"; p.append(rel_type)
        if mech:
            q += " AND mechanism_id=?"; p.append(mech_id(mech))
        r = cur.execute(q, p).fetchone()
        return r[0] if r else None

    def add_relation(src, tgt, rel_type, mech, desc, certainty, influence,
                     active_from=None):
        if find_relation(src, tgt, rel_type, mech):
            print(f"relatie bestaat al: {src} -> {tgt} ({rel_type})")
            return find_relation(src, tgt, rel_type, mech)
        cur.execute(
            """INSERT INTO relations
               (source_id, target_id, relation_type, mechanism_id, description,
                certainty, influence, active_from)
               VALUES (?,?,?,?,?,?,?,?)""",
            (entity_id(src), entity_id(tgt), rel_type, mech_id(mech), desc,
             certainty, influence, active_from),
        )
        rid = cur.lastrowid
        if mech:
            cur.execute(
                "INSERT INTO instantiations (mechanism_id, relation_id, exemplarity, notes) "
                "VALUES (?,?,?,?)", (mech_id(mech), rid, 0.7, CONTRIB))
        print(f"+ relatie {src} -> {tgt} ({rel_type}/{mech or '-'}) "
              f"cert={certainty} infl={influence}")
        return rid

    # EU-Commissie -> platforms (statelijke inhoudsmoderatie)
    r_ec_tt = add_relation("Europese Commissie", "TikTok", "censuur",
        "statelijke_inhoudsmoderatie",
        "EU Internet Forum 'borderline content'-handboek (2023) + 100+ overleggen "
        "2022-2024. TikTok rapporteerde >45.000 verwijderde 'misinformatie'-items "
        "rond de EU-verkiezingen 2024.", 0.80, 0.45)
    add_relation("Europese Commissie", "Meta (Facebook/Instagram)", "censuur",
        "statelijke_inhoudsmoderatie",
        "Coordinatie platformmoderatie via Code of Practice/EU Internet Forum.",
        0.78, 0.45)
    add_relation("Europese Commissie", "Google", "censuur",
        "statelijke_inhoudsmoderatie",
        "Coordinatie platformmoderatie (Google/YouTube) via Code of Practice.",
        0.72, 0.40)
    add_relation("Europese Commissie", "X (Twitter)", "censuur",
        "statelijke_inhoudsmoderatie",
        "Coordinatie platformmoderatie; X trok zich in 2023 terug uit de "
        "vrijwillige Code of Practice.", 0.65, 0.40)

    # BZK -> de gedocumenteerde vijf platforms (trusted flagger)
    r_bzk_meta = add_relation("Ministerie van Binnenlandse Zaken", "Meta (Facebook/Instagram)",
        "censuur", "statelijke_inhoudsmoderatie",
        "Trusted-flagger-status sinds 2019. Inzet 'met grote terughoudendheid', "
        "alleen rond verkiezingen, alleen procesverstorende desinformatie "
        "(stemdatum/locatie/stemwijze).", 0.82, 0.30, active_from="2019-01-01")
    add_relation("Ministerie van Binnenlandse Zaken", "X (Twitter)", "censuur",
        "statelijke_inhoudsmoderatie", "Trusted-flagger-status sinds 2019 (Twitter).",
        0.82, 0.30, active_from="2019-01-01")
    add_relation("Ministerie van Binnenlandse Zaken", "Google", "censuur",
        "statelijke_inhoudsmoderatie", "Trusted-flagger-status sinds 2021.",
        0.78, 0.28, active_from="2021-01-01")
    add_relation("Ministerie van Binnenlandse Zaken", "TikTok", "censuur",
        "statelijke_inhoudsmoderatie", "Trusted-flagger-status sinds 2021.",
        0.78, 0.28, active_from="2021-01-01")
    add_relation("Ministerie van Binnenlandse Zaken", "Snapchat", "censuur",
        "statelijke_inhoudsmoderatie", "Trusted-flagger-status sinds 2021.",
        0.78, 0.25, active_from="2021-01-01")

    # AIVD/MIVD -> journalist (cooptatie); attributie per dienst onzeker
    r_aivd = add_relation("AIVD", "Sinan Can", "cooptatie", "inlichtingen_cooptatie",
        "Publiek besproken benadering door een inlichtingendienst; attributie "
        "AIVD/MIVD niet zeker. Past in patroon uit intern AIVD-document (8 "
        "journalisten).", 0.45, 0.35)
    add_relation("MIVD", "Sinan Can", "cooptatie", "inlichtingen_cooptatie",
        "Correspondent in voor de MIVD relevante conflictregio's; attributie "
        "onzeker (kan ook AIVD zijn).", 0.40, 0.35)

    # Open Society <-> SDM (cofinanciering; lage influence op berichtgeving)
    r_osf = add_relation("Open Society Foundations", "Stichting Democratie en Media",
        "alliantie", None,
        "Cofinanciering 2016-programma tegen discriminatie van moslims (OSF "
        "Initiative for Europe). Geen aanwijzing voor inhoudelijke sturing van "
        "Volkskrant/Trouw; SDM's mediarol is onafhankelijkheidsborging.",
        0.70, 0.25)

    # Geldstroom achter de EIB-lening: ECB + BlackRock (op EIB-niveau, niet DPG)
    r_ecb = add_relation("ECB (Europese Centrale Bank)", "EIB (Europese Investeringsbank)",
        "financiering", None,
        "Eurosysteem grootste opkoper van EIB-obligaties (~EUR 100 mld). "
        "Systemische financier, geen aandeelhouder; monetair beleid, diffuus — "
        "stuurt geen berichtgeving. Corrigeert de transcript-claim 'grootste "
        "aandeelhouder'.", 0.85, 0.20)
    add_relation("BlackRock", "EIB (Europese Investeringsbank)", "investering",
        "systemisch_eigenaarschap",
        "Groot houder van EIB/supranationaal papier (passief systemisch). "
        "'Grootste' onbevestigd.", 0.55, 0.12)
    r_blk_ec = add_relation("BlackRock", "Europese Commissie", "adviseur", None,
        "ESG-adviescontract 2020 (EUR 280k); Europese Ombudsman zag risico op "
        "belangenverstrengeling. Eerder ECB-ABS-programma-advies (~2014).",
        0.80, 0.30)

    # ---- VERFIJNINGEN bestaande relaties (Laag 1 + EIB) --------------------
    def upd(rid, **kw):
        if not rid:
            return
        sets = ", ".join(f"{k}=?" for k in kw)
        cur.execute(f"UPDATE relations SET {sets} WHERE id=?", (*kw.values(), rid))

    # DPG -> RTL: nu gedocumenteerd feit (ACM 27-6-2025, geeffectueerd 1-7-2025)
    upd(find_relation("DPG Media", "RTL Nederland", mech="eigendomsconcentratie"),
        certainty=0.97, active_from="2025-07-01",
        description="DPG bezit RTL Nederland. ACM-vergunning 27-6-2025, "
                    "geeffectueerd 1-7-2025, EUR 1,1 mld cash.")
    upd(find_relation("DPG Media", "RTL Nederland", mech="winstmaximalisatie"),
        certainty=0.92, active_from="2025-07-01")

    # ACM -> DPG/RTL: afgedwongen borging als overnamevoorwaarde (tegenmacht)
    am = mech_id("afgedwongen_borging")
    for tgt, rid in (("DPG Media", find_relation("ACM (Autoriteit Consument & Markt)", "DPG Media")),
                     ("RTL Nederland", find_relation("ACM (Autoriteit Consument & Markt)", "RTL Nederland"))):
        if rid:
            upd(rid, relation_type="regulering", mechanism_id=am, certainty=0.90,
                influence=0.55,
                description="ACM-voorwaarden 2025: uitgebreid SDM-veto (geen "
                            "verkoop/opheffing landelijke titel zonder SDM), "
                            "Handvest DPG, gratis nieuws, gescheiden redacties "
                            "RTL Nieuws/NU.nl.")
            if not cur.execute("SELECT 1 FROM instantiations WHERE mechanism_id=? AND relation_id=?",
                               (am, rid)).fetchone():
                cur.execute("INSERT INTO instantiations (mechanism_id, relation_id, exemplarity, notes) "
                            "VALUES (?,?,?,?)", (am, rid, 0.8, CONTRIB))
            print(f"~ verfijnd ACM -> {tgt} (afgedwongen_borging)")

    # SDM -> DPG: bestaande onafhankelijkheidsborging optillen + continuiteitsveto erbij
    upd(find_relation("Stichting Democratie en Media", "DPG Media", mech="onafhankelijkheidsborging"),
        certainty=0.70)
    r_sdm_cont = add_relation("Stichting Democratie en Media", "DPG Media", "eigendom",
        "continuiteitsborging",
        "Sinds 2025 (ACM-voorwaarde) uitgebreid veto: DPG kan geen landelijke "
        "nieuwstitel verkopen of beeindigen zonder goedkeuring van SDM.",
        0.90, 0.55, active_from="2025-07-01")
    add_relation("Stichting Democratie en Media", "NU.nl", "eigendom",
        "continuiteitsborging",
        "Post-2025: SDM-veto strekt zich uit tot alle landelijke titels incl. "
        "NU.nl; aparte onafhankelijke stichting voor NU.nl als borging.",
        0.85, 0.45, active_from="2025-07-01")

    # EIB -> DPG: bedrag/duiding aanscherpen (100M 2022 + 120M 2025 = 220M)
    upd(find_relation("EIB (Europese Investeringsbank)", "DPG Media"),
        description="EIB-groeileningen aan DPG: EUR 100 mln (2022) + EUR 120 mln "
                    "(2025) = EUR 220 mln. Deel van EUR 392 mln 'digital "
                    "acceleration'; ~EUR 50 mln voor DPG's eigen advertentie"
                    "platform 'Trusted Web'. FTM stelt kritische vragen.")

    # ---- BRONNEN -----------------------------------------------------------
    def add_source(title, author, stype, publisher, date, reliability, url, summary=""):
        r = cur.execute("SELECT id FROM sources WHERE title=? AND author IS ?",
                        (title, author)).fetchone()
        if r:
            return r[0]
        cur.execute(
            """INSERT INTO sources (title, author, source_type, publisher,
               date_published, reliability, summary, processed)
               VALUES (?,?,?,?,?,?,?,1)""",
            (title, author, stype, publisher, date, reliability, summary))
        sid = cur.lastrowid
        cur.execute("INSERT INTO source_locations (source_id, location_type, location, accessed_at) "
                    "VALUES (?,?,?,?)", (sid, "url", url, "2026-06-08"))
        return sid

    S = {}
    S["acm"] = add_source(
        "DPG Media krijgt vergunning voor overname RTL Nederland (eindmededeling)",
        "ACM", "persbericht", "Autoriteit Consument & Markt", "2025-06-27",
        "institutioneel", "https://www.acm.nl/nl/publicaties/dpg-media-krijgt-vergunning-voor-overname-rtl-nederland-eindmededeling")
    S["eib"] = add_source(
        "DPG Media signs new loan agreement with EIB", "EIB", "persbericht",
        "Europese Investeringsbank", "2025-02-12", "institutioneel",
        "https://www.eib.org/en/press/all/2025-076-dpg-media-signs-new-loan-agreement-with-eib")
    S["ftm"] = add_source(
        "In de strijd tegen Big Tech misbruikt uitgever DPG Europese miljoenen",
        "Follow the Money", "nieuwsartikel", "Follow the Money", "2025-02-01",
        "kwaliteitsjournalistiek", "https://www.ftm.nl/artikelen/dpg-media-en-europese-subsidies")
    S["nrc"] = add_source(
        "AIVD en MIVD rekruteerden journalisten als agent", "NRC / de Volkskrant",
        "nieuwsartikel", "NRC", "2024-07-01", "kwaliteitsjournalistiek",
        "https://nos.nl/l/2448413")
    S["kamer"] = add_source(
        "Beantwoording Kamervragen AIVD/MIVD rekruteerden journalisten", "Rijksoverheid",
        "rapport", "Tweede Kamer", "2024-08-15", "institutioneel",
        "https://www.rijksoverheid.nl/documenten/kamerstukken/2024/08/15/beantwoording-vragen-van-houwelingen-fvd-over-het-artikel-aivd-en-mivd-rekruteerden-journalisten-als-agent")
    S["bb"] = add_source(
        "Rijksoverheid al jaren 'trusted flagger' bij social media", "Binnenlands Bestuur",
        "nieuwsartikel", "Binnenlands Bestuur", "2023-01-01", "kwaliteitsjournalistiek",
        "https://www.binnenlandsbestuur.nl/digitaal/terughoudendheid-over-desinformatie-door-trusted-flagger-overheid")
    S["gifct"] = add_source(
        "Borderline Content: Understanding the Gray Zone", "GIFCT", "rapport",
        "GIFCT", "2023-06-29", "grijs",
        "https://gifct.org/2023/06/29/borderline-content-understanding-the-gray-zone/")
    S["house"] = add_source(
        "The Foreign Censorship Threat, Part II", "US House Judiciary Committee",
        "rapport", "US House Judiciary Committee", "2026-02-03", "opinie",
        "https://judiciary.house.gov/sites/evo-subsites/republicans-judiciary.house.gov/files/2026-02/THE-FOREIGN-CENSORSHIP-THREAT-PART-II-2-3-26.pdf")
    S["bsignal"] = add_source(
        "Big tech deboosted millions of posts during EU elections", "Brussels Signal",
        "nieuwsartikel", "Brussels Signal", "2024-09-01", "kwaliteitsjournalistiek",
        "https://brusselssignal.eu/2024/09/big-tech-deboosted-millions-of-posts-during-eu-elections/")
    S["sdm_wiki"] = add_source(
        "Stichting Democratie en Media", "Wikipedia", "website", "Wikipedia", None,
        "grijs", "https://nl.wikipedia.org/wiki/Stichting_Democratie_en_Media")
    S["pm"] = add_source(
        "The purchase of EIB bonds by the Eurosystem", "Positive Money Europe",
        "rapport", "Positive Money", None, "grijs",
        "https://positivemoney.org/eu/archive/real-safe-asset-eib-bonds/")
    S["omb"] = add_source(
        "European Ombudsman opens inquiry into BlackRock ESG advisory contract",
        "Central Banking", "nieuwsartikel", "Central Banking", "2020-08-01",
        "kwaliteitsjournalistiek",
        "https://www.centralbanking.com/central-banks/financial-stability/7653841/european-ombudsman-opens-inquiry-into-blackrock-esg-advisory-contract")

    # ---- ARGUMENTEN + CITATIES --------------------------------------------
    def add_arg(stance, claim, reasoning, weight, citations, relation_id=None,
                entity_id=None, role_id=None, mechanism_id=None, status="ongecontroleerd"):
        cur.execute(
            """INSERT INTO arguments (relation_id, entity_id, role_id, mechanism_id,
               stance, claim, reasoning, weight, status, contributed_by)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (relation_id, entity_id, role_id, mechanism_id, stance, claim,
             reasoning, weight, status, CONTRIB))
        aid = cur.lastrowid
        for sid, quote, ctx in citations:
            cur.execute("INSERT INTO citations (argument_id, source_id, quote, context) "
                        "VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        return aid

    m_mod = mech_id("statelijke_inhoudsmoderatie")
    m_coopt = mech_id("inlichtingen_cooptatie")

    add_arg("supporting",
        "EU Internet Forum publiceerde (2023) een 'borderline content'-handboek dat "
        "o.a. anti-elite, populistische, anti-EU en meme-content als te monitoren/"
        "demoten aanmerkt.",
        "Bevestigt dat de moderatiecoordinatie expliciet legale, politieke spraak "
        "(incl. anti-elite) bestrijkt — niet alleen illegale content.",
        0.65, [(S["gifct"], "borderline content ... largely legal speech within democratic frameworks",
                "neutrale provenance van de categorieenlijst"),
               (S["house"], "populist rhetoric, anti-government/anti-EU, anti-elite content, political satire ... meme subculture",
                "partijdige (Republikeinse) bron; gebruikt voor de letterlijke opsomming")],
        mechanism_id=m_mod)

    add_arg("supporting",
        "TikTok rapporteerde >45.000 verwijderde 'misinformatie'-items rond de "
        "EU-verkiezingen 2024 (incl. politieke spraak over migratie/klimaat/"
        "veiligheid/LGBTQ).",
        "Onderbouwt schaal en electorale timing van de platformmoderatie.",
        0.70, [(S["bsignal"], "TikTok ... censored over 45,000 pieces of alleged misinformation ahead of the 2024 EU elections",
                "platform-eigen rapportage onder de Code of Practice")],
        relation_id=r_ec_tt)

    add_arg("supporting",
        "BZK heeft trusted-flagger-status bij vijf platforms (Meta/Twitter sinds "
        "2019; Google/TikTok/Snapchat sinds 2021).",
        "Bevestigt het kanaal staat -> platform.",
        0.70, [(S["bb"], "Rijksoverheid ... trusted flagger ... sinds 2019 ... sinds 2021 Google, TikTok en Snapchat",
                "")], relation_id=r_bzk_meta)
    add_arg("contradicting",
        "De status wordt 'met grote terughoudendheid' en alleen rond verkiezingen "
        "gebruikt, alleen voor procesverstorende desinformatie.",
        "Begrenst de influence: geen bewijs dat individuen 'van het internet "
        "verdwijnen'; weerlegt de magnitude-claim uit het transcript.",
        0.55, [(S["bb"], "alleen rond verkiezingen ... met grote terughoudendheid",
                "ministeriele duiding")], relation_id=r_bzk_meta)

    add_arg("supporting",
        "NRC/Volkskrant (2024): van 32 benaderde redacteuren/correspondenten meldde "
        "~de helft een verzoek; intern AIVD-document noemde 8 journalisten onder 21 "
        "'bronnen en agenten'.",
        "Sterke onderbouwing van het mechanisme inlichtingen_cooptatie.",
        0.75, [(S["nrc"], "ronselen journalisten ... 32 ... ongeveer de helft",
                "onderzoeksjournalistiek"),
               (S["kamer"], "intern AIVD-document ... acht journalisten", "")],
        mechanism_id=m_coopt)
    add_arg("contextual",
        "Ministers Uitermark (BZK) en Brekelmans (Defensie) weigerden het aantal "
        "gerekruteerde journalisten aan de Kamer vrij te geven.",
        "Falende parlementaire controle; bevestigt het transcript-detail dat de "
        "minister wel bevestigt maar details achterhoudt.",
        0.50, [(S["kamer"], "houdt aantal door AIVD gerekruteerde journalisten geheim", "")],
        mechanism_id=m_coopt)

    add_arg("supporting",
        "SDM cofinancierde in 2016 met OSF Initiative for Europe een programma tegen "
        "structurele discriminatie van moslims.",
        "Bevestigt de openlijke samenwerking SDM <-> Open Society.",
        0.55, [(S["sdm_wiki"], "in samenwerking met de Open Society Foundations Initiative for Europe",
                "")], relation_id=r_osf)
    add_arg("contradicting",
        "Geen bewijs dat de OSF-samenwerking zich vertaalt in redactionele sturing "
        "van Volkskrant/Trouw; SDM's mediarol is onafhankelijkheidsborging (tegenmacht).",
        "Verklaart de lage influence-score: zeker kanaal, marginale invloed op "
        "berichtgeving.",
        0.55, [], relation_id=r_osf)

    add_arg("supporting",
        "Het Eurosysteem is de grootste institutionele opkoper van EIB-obligaties "
        "(~EUR 100 mld; EIB >40% van QE-waardig supranationaal papier).",
        "Herkadert de transcript-claim 'grootste aandeelhouder ECB' correct: "
        "obligatiehouder/financier, niet aandeelhouder, en op EIB- niet DPG-niveau.",
        0.60, [(S["pm"], "the Eurosystem had bought approximately EUR 100bn of EIB bonds",
                "")], relation_id=r_ecb)

    add_arg("supporting",
        "De EU-Commissie gaf BlackRock in 2020 een ESG-adviescontract; de Europese "
        "Ombudsman zag risico op belangenverstrengeling.",
        "Onderbouwt het verband BlackRock -> regelgever (regulatory-capture-flavor).",
        0.60, [(S["omb"], "European Ombudsman ... legitimate concerns as to a conflict of interest",
                "")], relation_id=r_blk_ec)

    add_arg("supporting",
        "ACM verleende 27-6-2025 vergunning (geeffectueerd 1-7-2025, EUR 1,1 mld) "
        "onder voorwaarden: uitgebreid SDM-veto, Handvest DPG, gratis nieuws, "
        "gescheiden redacties.",
        "Dezelfde concentratie die het transcript aanvoert, dwong ook tegenmacht af.",
        0.75, [(S["acm"], "DPG Media mag RTL Nederland onder voorwaarden overnemen",
                "")], relation_id=r_sdm_cont)

    add_arg("supporting",
        "EIB-leningen aan DPG: EUR 100 mln (2022) + EUR 120 mln (2025) = EUR 220 mln; "
        "deels voor DPG's eigen advertentieplatform 'Trusted Web'.",
        "Bevestigt het bedrag uit het transcript en de F1/F2-duiding.",
        0.70, [(S["eib"], "DPG Media signs new loan agreement with EIB",
                "EUR 120 mln-tranche 2025"),
               (S["ftm"], "DPG ... Europese miljoenen ... Trusted Web", "kritische duiding")],
        relation_id=find_relation("EIB (Europese Investeringsbank)", "DPG Media"))

    con.commit()

    # ---- SAMENVATTING ------------------------------------------------------
    for label, q in (
        ("entities", "SELECT COUNT(*) FROM entities"),
        ("relations", "SELECT COUNT(*) FROM relations"),
        ("mechanisms", "SELECT COUNT(*) FROM mechanisms"),
        ("arguments", "SELECT COUNT(*) FROM arguments"),
        ("citations", "SELECT COUNT(*) FROM citations"),
        ("sources", "SELECT COUNT(*) FROM sources"),
    ):
        print(f"{label:12s}: {cur.execute(q).fetchone()[0]}")
    con.close()
    print("klaar.")


if __name__ == "__main__":
    main()
