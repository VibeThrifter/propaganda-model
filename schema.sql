-- Propaganda Model: Nederlandse Politiek & Media
-- Twee lagen: abstract theoretisch model + concrete instanties
-- Academische bronstructuur: argumenten → citaties → bronnen → locaties

--------------------------------------------------------------
-- LAAG 1: THEORETISCH MODEL (Chomsky-achtig, generiek)
-- Beschrijft de structuur: welke rollen en mechanismen bestaan er
--------------------------------------------------------------

CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,           -- bijv. 'mediaeigenaar', 'adverteerder', 'staatsinstelling'
    category TEXT NOT NULL CHECK(category IN (
        'eigendom',          -- 1e filter: eigendomsconcentratie
        'advertentie',       -- 2e filter: advertentie-inkomsten
        'sourcing',          -- 3e filter: afhankelijkheid van bronnen
        'flak',              -- 4e filter: disciplineringsmechanisme
        'ideologie',         -- 5e filter: ideologisch kader
        'systeemactor',      -- actoren die meerdere filters bedienen
        'overig'
    )),
    description TEXT NOT NULL,
    examples TEXT,                        -- generieke voorbeelden ter illustratie
    -- Temporeel (zie migrate_tijdsdimensie_theorielaag.py): ook de theorielaag is
    -- historisch contingent. NULL = onbegrensd voor zover bekend.
    active_from TEXT,
    active_until TEXT
);

CREATE TABLE mechanisms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,            -- bijv. 'advertentiedruk', 'draaideurpersoneel'
    filter TEXT NOT NULL CHECK(filter IN (
        'eigendom',
        'advertentie',
        'sourcing',
        'flak',
        'ideologie',
        'cross_filter',      -- mechanismen die meerdere filters verbinden
        'overig'
    )),
    mechanism_type TEXT NOT NULL CHECK(mechanism_type IN (
        'structureel',       -- ingebouwd in het systeem (eigendomsconcentratie)
        'procedureel',       -- via routines en processen (pakketjournalistiek)
        'psychologisch',     -- via cognitieve/sociale processen (groepsdenken)
        'economisch',        -- via financiële prikkels (advertentiedruk)
        'juridisch',         -- via recht en regelgeving (SLAPP)
        'technologisch',     -- via algoritmes en platforms
        'discursief'         -- via taal en framing (etikettering)
    )),
    description TEXT NOT NULL,            -- hoe werkt dit mechanisme
    effect TEXT NOT NULL,                 -- wat is het effect op de berichtgeving
    source_role_id INTEGER REFERENCES roles(id),  -- welke rol oefent dit uit
    target_role_id INTEGER REFERENCES roles(id),  -- welke rol ondergaat dit
    -- Aard van het mechanisme: is een instantie ervan een echt dyadisch invloedskanaal
    -- of een emergente/systemische eigenschap (halo)? Bepaalt viz én invloed-wiskunde.
    -- Leidend principe: een edge tussen twee nodes is 'direct'. Volledige uitleg + beslisgids:
    -- DOCUMENTATIE.md § "Aard: direct & systemisch" en CLAUDE.md. Visuele grammatica:
    -- pijlpunt = gericht; doorgetrokken = onmiddellijk.
    aard TEXT NOT NULL DEFAULT 'direct' CHECK(aard IN (
        'direct',             -- lokaal feit; oorzaak = de twee eindpunten — doorgetrokken pijl mét punt (LEVEND)
        'veld_eigenschap',    -- geen zinnige externe bron; eigenschap ván de getroffen node — halo (LEVEND)
        'indirect',           -- DEPRECATED/leeg: "een edge tussen twee nodes is direct"; teken de keten i.p.v. een stippelpijl. Tekent als directe edge.
        'veld_instantiatie'   -- DEPRECATED/leeg: was diffuse waaier; echte dyade → direct, systeemeigenschap → veld_eigenschap, anders verwijderen. Behouden voor migratie-replay.
    )),
    -- Temporeel: mechanismen zijn historisch contingent (kijkcijferdisciplinering
    -- vereist een kijkmeterpanel, sinds 1987). NULL = onbegrensd voor zover bekend.
    active_from TEXT,
    active_until TEXT
);

-- Twee-assen-categorisatie van mechanismen (zie enrich_filters_themas.py).
-- mechanisms.filter blijft het PRIMAIRE filter (lead-kleur); hieronder alle filter-tags.
CREATE TABLE mechanism_filters (
    mechanism_id INTEGER NOT NULL REFERENCES mechanisms(id) ON DELETE CASCADE,
    filter TEXT NOT NULL CHECK(filter IN (
        'eigendom', 'advertentie', 'sourcing', 'flak', 'ideologie', 'tegenmacht', 'overig'
    )),
    PRIMARY KEY (mechanism_id, filter)
);

-- Dwarsliggende thema's (families die meerdere filters overspannen), many-to-many.
CREATE TABLE mechanism_themes (
    mechanism_id INTEGER NOT NULL REFERENCES mechanisms(id) ON DELETE CASCADE,
    theme TEXT NOT NULL CHECK(theme IN (
        'draaideur', 'elite_netwerk', 'geldstromen', 'platform',
        'systemisch', 'omroepbestel', 'kennis_expertise', 'benoemingsketen'
    )),
    PRIMARY KEY (mechanism_id, theme)
);

-- Emergente effecten als HYPEREDGE: een systeemeigenschap die uit het samenspel van
-- MEERDERE rollen voortkomt en niet in een 1-op-1 relatie te vangen is (bv. 'fabricage
-- van consensus'). Geen bron→doel-pijl; het effect hoort bij de hele ledengroep.
-- Zie migrate_add_emergent_effects.py. In de viz: transparant veld rond de leden (theorie).
CREATE TABLE emergent_effects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,            -- machine-naam, bv. 'fabricage_van_consensus'
    label TEXT NOT NULL,                  -- weergavenaam, bv. 'Fabricage van consensus'
    category TEXT NOT NULL DEFAULT 'systeemactor' CHECK(category IN (
        'eigendom','advertentie','sourcing','flak','ideologie','systeemactor','overig'
    )),
    description TEXT NOT NULL,            -- wat is het emergente effect (uit welk samenspel)
    effect TEXT NOT NULL,                -- gevolg voor de berichtgeving
    active_from TEXT,                    -- temporeel; NULL = onbegrensd voor zover bekend
    active_until TEXT
);
CREATE TABLE emergent_effect_members (
    emergent_effect_id INTEGER NOT NULL REFERENCES emergent_effects(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    PRIMARY KEY (emergent_effect_id, role_id)
);

--------------------------------------------------------------
-- LAAG 2: INSTANTIEMODEL (concreet, met namen)
-- De echte entiteiten en relaties in Nederland
--------------------------------------------------------------

CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    -- PRINCIPE: `type` = de structurele VORM (wat is het?), niet de functie.
    -- Voor organisaties varieert die vorm echt (bedrijf, partij, stichting, omroep, ...);
    -- voor mensen bestaat er maar één soort: 'persoon'. De FUNCTIE/positie in het model
    -- hoort altijd in de rol (primary_role_id / entity_roles), niet in `type`.
    -- De rol-achtige type-waarden hieronder (politicus, adverteerder, mediaeigenaar, ...)
    -- zijn LEGACY: ze blijven toegestaan zodat de seed/enrich-scripts hun ruwe extractie
    -- kunnen invoeren, maar worden in de live DB samengevouwen tot hun structurele vorm
    -- door scripts/migrate_clean_entity_types.py. Gebruik voor NIEUWE data alleen de
    -- structurele types (de niet-legacy regels). Zie DOCUMENTATIE.md.
    type TEXT NOT NULL CHECK(type IN (
        -- Personen (structureel: gebruik 'persoon'; functie via rol)
        'persoon',               -- elke natuurlijke persoon of familie
        'politicus',             -- LEGACY -> persoon (rol 'politicus')
        'journalist',            -- LEGACY -> persoon (rol journalist/onderzoeksjournalist)
        'voorlichter',           -- LEGACY -> persoon (rol 'voorlichter')
        'lobbyist',              -- LEGACY -> persoon (rol 'lobbyist')
        'columnist',             -- LEGACY -> persoon (rol 'columnist_opiniemaker')
        'academicus',            -- LEGACY -> persoon (rol 'gezagsexpert')
        'mediaeigenaar',         -- LEGACY -> persoon (rol 'mediaeigenaar')
        'toezichthouder_persoon',-- LEGACY -> persoon (rol 'toezichthouder')
        'advocaat',              -- LEGACY -> persoon
        'klokkenluider',         -- LEGACY -> persoon (rol 'klokkenluider')

        -- Organisaties (structurele/juridische vormen)
        'partij',                -- politieke partij
        'mediaorganisatie',      -- krant, omroep, nieuwssite, tijdschrift
        'persbureau',            -- ANP, Reuters, etc.
        'bedrijf',               -- commercieel bedrijf
        'lobbygroep',            -- belangenorganisatie, branchevereniging
        'denktank',              -- onderzoeksinstituut, policy institute
        'overheidsinstelling',   -- ministerie, inspectie, uitvoeringsorganisatie
        'toezichthouder',        -- ACM, CvdM, AFM, etc.
        'ngo',                   -- maatschappelijke organisatie
        'vakbond',               -- werknemersorganisatie
        'omroep',                -- publieke omroep (NPO, NOS, etc.)
        'elite_netwerk',         -- Bilderberg, WEF, Trilaterale Commissie, ERT
        'vermogensbeheerder',    -- BlackRock, Vanguard, pensioenfonds
        'pr_bureau',             -- communicatie-/PR-bureau
        'platform',              -- digitaal platform (Google, Meta, TikTok)
        'rechterlijke_macht',    -- rechtbank, gerechtshof
        'onderwijsinstelling',   -- universiteit, journalistiekopleiding
        'burgerinitiatief',      -- burgerbeweging, actiegroep, gedupeerdengroep
        'stichting',             -- stichting, administratiekantoor (STAK), borgingsstichting
        'adverteerder'           -- LEGACY -> bedrijf (rol 'adverteerder')
    )),
    primary_role_id INTEGER REFERENCES roles(id),
    description TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Een entiteit kan meerdere rollen vervullen
CREATE TABLE entity_roles (
    entity_id INTEGER NOT NULL REFERENCES entities(id),
    role_id INTEGER NOT NULL REFERENCES roles(id),
    notes TEXT,
    PRIMARY KEY (entity_id, role_id)
);

CREATE TABLE relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES entities(id),
    target_id INTEGER NOT NULL REFERENCES entities(id),
    relation_type TEXT NOT NULL CHECK(relation_type IN (
        -- Eigendom & financiën
        'eigendom',              -- bezit, aandeelhouderschap
        'financiering',          -- geldstroom, subsidie, sponsoring
        'adverteerder',          -- betaalt voor advertentieruimte
        'donor',                 -- donatie, mecenaat
        'investering',           -- kapitaalbelang, deelneming

        -- Organisatorisch
        'lidmaatschap',          -- lid van netwerk, partij, groep
        'personeel',             -- werkgever-werknemer
        'bestuurder',            -- bestuurslid, commissaris, voorzitter
        'adviseur',              -- formeel of informeel advies
        'woordvoerder_van',      -- officiële voorlichter/woordvoerder
        'draaideur',             -- overstap tussen sectoren (revolving door)

        -- Informatiestromen
        'bron_van',              -- levert informatie aan (journalist, medium)
        'mediaplatform',         -- publiceert via dit medium
        'framing',               -- bepaalt het frame/narratief
        'citeert',               -- gebruikt als bron in berichtgeving

        -- Macht & druk
        'lobbyt',                -- lobbyt bij / oefent druk uit op
        'censuur',               -- onderdrukt informatie
        'flak',                  -- disciplineert via negatieve reacties
        'intimidatie',           -- bedreiging, SLAPP, juridische druk
        'regulering',            -- houdt toezicht op, reguleert
        'zelfcensuur',           -- interne terughoudendheid

        -- Politiek & ideologisch
        'alliantie',             -- strategisch bondgenootschap
        'oppositie',             -- tegengestelde belangen
        'beinvloeding',          -- generieke beïnvloeding
        'cooptatie',             -- incorporeren van kritiek
        'etikettering',          -- labelen/diskwalificeren (wappie, complotdenker)

        -- Algoritmisch
        'algoritmische_filtering' -- platformalgoritme bepaalt zichtbaarheid
    )),
    mechanism_id INTEGER REFERENCES mechanisms(id),
    description TEXT,
    certainty REAL CHECK(certainty BETWEEN 0.0 AND 1.0),
    influence REAL CHECK(influence BETWEEN 0.0 AND 1.0),
    bidirectional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------------------
-- KLASSE <-> INSTANTIE: theorie geïnstantieerd door praktijk
-- Maakt de koppeling expliciet (rol<->entiteit of mechanisme<->relatie) met een
-- exemplariteit-gewicht: hoe prototypisch is dit praktijkvoorbeeld voor de klasse?
-- Vormt de basis voor de bottom-up aggregatie van geloofwaardigheid/sterkte.
--------------------------------------------------------------

CREATE TABLE instantiations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id      INTEGER REFERENCES roles(id),
    mechanism_id INTEGER REFERENCES mechanisms(id),
    entity_id    INTEGER REFERENCES entities(id),
    relation_id  INTEGER REFERENCES relations(id),
    exemplarity  REAL DEFAULT 1.0 CHECK(exemplarity BETWEEN 0.0 AND 1.0),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- precies één klasse en precies één instantie; types moeten matchen
    CHECK ((role_id IS NOT NULL) + (mechanism_id IS NOT NULL) = 1),
    CHECK ((entity_id IS NOT NULL) + (relation_id IS NOT NULL) = 1),
    CHECK ((role_id IS NOT NULL AND entity_id IS NOT NULL)
        OR (mechanism_id IS NOT NULL AND relation_id IS NOT NULL))
);

--------------------------------------------------------------
-- BRONNEN (academisch)
-- Hiërarchie: bron → locaties (meerdere URLs/bestanden per bron)
--------------------------------------------------------------

CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                  -- "Manufacturing Consent" / "Aandacht voor media"
    author TEXT,                          -- "Herman, E.S. & Chomsky, N." / "WRR"
    source_type TEXT NOT NULL CHECK(source_type IN (
        'boek',
        'academisch_artikel',
        'rapport',
        'nieuwsartikel',
        'transcript',
        'interview',
        'dataset',
        'wetgeving',
        'persbericht',
        'website',
        'overig'
    )),
    publisher TEXT,                       -- "Pantheon Books" / "Boom Uitgevers"
    date_published DATE,
    language TEXT DEFAULT 'nl',
    summary TEXT,
    processed BOOLEAN DEFAULT FALSE,
    -- Bronkwaliteit: hoe betrouwbaar is dit type bron?
    -- Gebaseerd op Wikipedia's "reliable sources" hiërarchie
    reliability TEXT NOT NULL DEFAULT 'onbeoordeeld' CHECK(reliability IN (
        'primair',           -- origineel document, dataset, wetgeving (hoogste feitelijke waarde)
        'academisch',        -- peer-reviewed, proefschrift (hoogste analytische waarde)
        'institutioneel',    -- WRR, CPB, ACM, SER rapporten
        'kwaliteitsjournalistiek', -- onderzoeksjournalistiek, longread, FTM/De Groene
        'regulier',          -- dagblad, omroep, ANP
        'opinie',            -- column, essay, commentaar
        'grijs',             -- blog, podcast, social media, onafhankelijk
        'onbeoordeeld'       -- nog niet geclassificeerd
    )),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meerdere locaties per bron (URLs, lokale bestanden, DOI, ISBN)
CREATE TABLE source_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    location_type TEXT NOT NULL CHECK(location_type IN (
        'url',              -- weblink
        'file',             -- lokaal bestand in sources/
        'doi',              -- Digital Object Identifier
        'isbn',             -- boek-ISBN
        'arxiv',            -- arXiv preprint
        'handle',           -- HDHL/institutional repository
        'archive_url'       -- Wayback Machine / web.archive.org snapshot
    )),
    location TEXT NOT NULL,              -- de URL, het pad, de DOI, etc.
    accessed_at DATE,                    -- wanneer bezocht (voor URLs)
    notes TEXT
);

--------------------------------------------------------------
-- ARGUMENTEN & CITATIES
-- Hiërarchie: relatie → argumenten → citaties (→ bronnen)
--------------------------------------------------------------

-- Argumenten: discussieboom per relatie of entiteit
-- parent_argument_id = NULL → root-argument (direct op relatie/entiteit)
-- parent_argument_id = <id> → reactie op een ander argument
CREATE TABLE arguments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relation_id INTEGER REFERENCES relations(id),        -- optioneel: argument over een relatie (praktijk)
    entity_id INTEGER REFERENCES entities(id),            -- optioneel: argument over een entiteit (praktijk)
    role_id INTEGER REFERENCES roles(id),                 -- optioneel: literatuur-argument over een rol (theorie)
    mechanism_id INTEGER REFERENCES mechanisms(id),       -- optioneel: literatuur-argument over een mechanisme (theorie)
    parent_argument_id INTEGER REFERENCES arguments(id),  -- NULL = root, anders = reactie op parent
    -- Welk aspect wordt bediscussieerd? NULL = het bestaan/de kern van de relatie/entiteit
    property TEXT CHECK(property IN (
        'existence',         -- bestaat deze relatie/entiteit überhaupt?
        'active_from',       -- wanneer begon dit?
        'active_until',      -- wanneer eindigde dit?
        'certainty',         -- hoe zeker is dit?
        'influence',         -- hoe sterk is de invloed?
        'relation_type',     -- klopt het type relatie?
        'description',       -- klopt de beschrijving?
        'type',              -- klopt het entiteittype?
        'role'               -- klopt de toegewezen rol?
    )),
    property_value TEXT,     -- voorgestelde waarde (bijv. '2019' voor active_from)
    stance TEXT NOT NULL CHECK(stance IN (
        'supporting',       -- bevestigt de parent-bewering of relatie/entiteit
        'contradicting',    -- weerspreekt de parent-bewering of relatie/entiteit
        'contextual'        -- nuancering, noch voor noch tegen
    )),
    claim TEXT NOT NULL,                 -- de kernbewering, kort en bondig
    reasoning TEXT,                      -- uitgebreide redenering / toelichting
    weight REAL CHECK(weight BETWEEN 0.0 AND 1.0),  -- hoe sterk is dit argument
    -- Verificatie-status (Wikipedia-stijl)
    status TEXT NOT NULL DEFAULT 'ongecontroleerd' CHECK(status IN (
        'ongecontroleerd',   -- net toegevoegd, nog niet beoordeeld
        'bronvermelding_nodig', -- claim zonder voldoende citaties
        'betwist',           -- actief betwist door tegenargumenten
        'geverifieerd',      -- citaties gecontroleerd en bevestigd
        'verouderd'          -- informatie mogelijk niet meer actueel
    )),
    contributed_by TEXT,                 -- wie voegde dit toe (accountability)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Minstens één target verplicht: praktijk (relatie/entiteit) óf theorie (rol/mechanisme)
    CHECK (relation_id IS NOT NULL OR entity_id IS NOT NULL
        OR role_id IS NOT NULL OR mechanism_id IS NOT NULL)
);

-- Citaties per argument: verwijzingen naar specifieke bronpassages
CREATE TABLE citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    argument_id INTEGER NOT NULL REFERENCES arguments(id),
    source_id INTEGER NOT NULL REFERENCES sources(id),
    quote TEXT,                          -- letterlijk citaat
    page TEXT,                           -- pagina / paginabereik ("pp. 45-48")
    section TEXT,                        -- hoofdstuk / sectie ("Hoofdstuk 3: Sourcing")
    context TEXT,                        -- korte toelichting bij het citaat
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------------------
-- AUDIT LOG
-- Wie veranderde wat, wanneer, en waarom (Wikipedia-stijl versiebeheer)
--------------------------------------------------------------

CREATE TABLE edit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,             -- 'arguments', 'relations', 'entities', etc.
    record_id INTEGER NOT NULL,           -- id van het gewijzigde record
    action TEXT NOT NULL CHECK(action IN (
        'created',           -- nieuw record aangemaakt
        'updated',           -- bestaand record gewijzigd
        'deleted',           -- record verwijderd
        'verified',          -- status → geverifieerd
        'disputed'           -- status → betwist
    )),
    changed_by TEXT,                      -- wie (gebruikersnaam, e-mail, of systeem)
    old_value TEXT,                       -- vorige waarde (JSON)
    new_value TEXT,                       -- nieuwe waarde (JSON)
    reason TEXT,                          -- reden voor de wijziging
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------------------
-- ENTITY-BRON KOPPELINGEN
--------------------------------------------------------------

CREATE TABLE source_mentions (
    source_id INTEGER NOT NULL REFERENCES sources(id),
    entity_id INTEGER NOT NULL REFERENCES entities(id),
    context TEXT,
    PRIMARY KEY (source_id, entity_id)
);

--------------------------------------------------------------
-- INDEXEN
--------------------------------------------------------------

CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_role ON entities(primary_role_id);
CREATE INDEX idx_relations_source ON relations(source_id);
CREATE INDEX idx_relations_target ON relations(target_id);
CREATE INDEX idx_relations_type ON relations(relation_type);
CREATE INDEX idx_relations_mechanism ON relations(mechanism_id);
CREATE UNIQUE INDEX idx_inst_role_entity ON instantiations(role_id, entity_id) WHERE role_id IS NOT NULL;
CREATE UNIQUE INDEX idx_inst_mech_relation ON instantiations(mechanism_id, relation_id) WHERE mechanism_id IS NOT NULL;
CREATE INDEX idx_inst_role ON instantiations(role_id);
CREATE INDEX idx_inst_mechanism ON instantiations(mechanism_id);
CREATE INDEX idx_inst_entity ON instantiations(entity_id);
CREATE INDEX idx_inst_relation ON instantiations(relation_id);
CREATE INDEX idx_sources_type ON sources(source_type);
CREATE INDEX idx_source_locations_source ON source_locations(source_id);
CREATE INDEX idx_arguments_relation ON arguments(relation_id);
CREATE INDEX idx_arguments_entity ON arguments(entity_id);
CREATE INDEX idx_arguments_role ON arguments(role_id);
CREATE INDEX idx_arguments_mechanism ON arguments(mechanism_id);
CREATE INDEX idx_arguments_parent ON arguments(parent_argument_id);
CREATE INDEX idx_arguments_stance ON arguments(stance);
CREATE INDEX idx_citations_argument ON citations(argument_id);
CREATE INDEX idx_citations_source ON citations(source_id);
CREATE INDEX idx_mechanisms_filter ON mechanisms(filter);
CREATE INDEX idx_mechfilters_filter ON mechanism_filters(filter);
CREATE INDEX idx_mechthemes_theme ON mechanism_themes(theme);
CREATE INDEX idx_edit_log_table ON edit_log(table_name, record_id);
CREATE INDEX idx_edit_log_changed_by ON edit_log(changed_by);
CREATE INDEX idx_arguments_status ON arguments(status);
CREATE INDEX idx_sources_reliability ON sources(reliability);
CREATE INDEX idx_mechanisms_type ON mechanisms(mechanism_type);

--------------------------------------------------------------
-- SEED DATA: ROLLEN (theoretisch model)
-- Gebaseerd op het propagandamodel en het rapport
--------------------------------------------------------------

-- Filter 1: Eigendom
INSERT INTO roles (name, category, description, examples) VALUES
('mediaeigenaar', 'eigendom', 'Bezitter of controlerende aandeelhouder van mediaconglomeraat. Bepaalt strategie, budget en benoemingen.', 'Familie Van Thillo (DPG), Familie Leysen (Mediahuis)'),
('institutionele_belegger', 'eigendom', 'Vermogensbeheerder die via aandelenbelangen en stemrecht de facto eigenaar is van grote bedrijven.', 'BlackRock, Vanguard, pensioenfondsen'),
('holding_bestuurder', 'eigendom', 'Bestuurder van holding of investeringsvehikel met belangen in media en andere sectoren.', 'GBL, Epifin, VP Exploitatie');

-- Filter 2: Advertentie
INSERT INTO roles (name, category, description, examples) VALUES
('adverteerder', 'advertentie', 'Bedrijf dat advertentieruimte koopt en daarmee invloed uitoefent op de redactionele omgeving.', 'Albert Heijn, Procter & Gamble, NLO');

-- Filter 3: Sourcing
INSERT INTO roles (name, category, description, examples) VALUES
('persbureau', 'sourcing', 'Centrale leverancier van nieuwsberichten aan alle mediaorganisaties. Homogeniseert het nieuwsaanbod.', 'ANP, Reuters, AFP'),
('voorlichter', 'sourcing', 'Woordvoerder of communicatieadviseur die de informatievoorziening namens een organisatie beheert en stuurt.', 'Rijksvoorlichtingsdienst, ministeriële woordvoerders'),
('lobbyist', 'sourcing', 'Professionele belangenbehartiger die informatie en frames aanlevert bij politici en journalisten.', 'Public affairs bureaus, brancheverenigingen'),
('denktank_expert', 'sourcing', 'Expert verbonden aan een denktank die analyses en beleidsvoorstellen levert en media-optredens doet.', 'HCSS, Clingendael, wetenschappelijke bureaus'),
('spin_doctor', 'sourcing', 'Politiek strateeg die het publieke narratief rond een politicus of partij vormgeeft.', 'Partijstrategen, campagneleiders'),
('pr_professional', 'sourcing', 'Communicatieprofessional die het beeld van een organisatie in de media beheert.', 'PR-bureaus, corporate communications');

-- Filter 4: Flak (geen rollen — flak produceren/ontvangen is een functie, geen identiteit)
-- Mechanismen in dit filter werken op bestaande rollen (politicus→journalist, etc.)

-- Filter 5: Ideologie
INSERT INTO roles (name, category, description, examples) VALUES
('organische_intellectueel', 'ideologie', 'Persoon die de belangen van de heersende klasse vertaalt naar universeel klinkende ideeën.', 'Invloedrijke columnisten, denktank-directeuren');

-- Systeemactoren (meerdere filters)
INSERT INTO roles (name, category, description, examples) VALUES
('journalist', 'systeemactor', 'Nieuwsproducent die opereert binnen alle vijf filters en zowel subject als object is van het systeem.', 'Parlementair verslaggevers, buitenlandcorrespondenten'),
('hoofdredacteur', 'systeemactor', 'Eindverantwoordelijke voor de redactionele lijn. Scharnierpunt tussen eigendom en journalistiek.', 'Hoofdredacteuren landelijke kranten'),
('columnist_opiniemaker', 'systeemactor', 'Publieke duider die het spectrum van toegestane mening mede definieert via regelmatige opiniestukken.', 'Vaste columnisten, talkshowgasten'),
('politicus_rol', 'systeemactor', 'Politiek actor die zowel bron, onderwerp als potentiële flak-producent is.', 'Kamerleden, ministers, partijleiders'),
('platformalgoritme', 'systeemactor', 'Algoritmisch systeem dat bepaalt welke content zichtbaar wordt. Nieuw type poortwachter.', 'Google News, Facebook Newsfeed, TikTok For You'),
('elite_netwerk_facilitator', 'systeemactor', 'Organisatie die bijeenkomsten faciliteert waar elite-consensus wordt gesmeed buiten het publieke oog.', 'Bilderberg, WEF Davos, Trilaterale Commissie, ERT');

--------------------------------------------------------------
-- SEED DATA: MECHANISMEN
-- Concrete technieken beschreven in het rapport
--------------------------------------------------------------

-- Filter 1: Eigendom
INSERT INTO mechanisms (name, filter, mechanism_type, description, effect) VALUES
('eigendomsconcentratie', 'eigendom', 'structureel', 'Extreme marktconcentratie waarbij twee conglomeraten >90% van de commerciële nieuwsmarkt bezitten.', 'Drastische vermindering van pluriformiteit op eigenaarsniveau.'),
('transnationale_elite_verwevenheid', 'eigendom', 'structureel', 'Media-eigenaren zijn lid van dezelfde transnationale netwerken als politieke en economische elite.', 'Belangen en wereldbeeld van de TCC worden de impliciete norm voor de berichtgeving.'),
('benoemingspolitiek', 'eigendom', 'procedureel', 'Eigenaar benoemt hoofdredacteur en bepaalt daarmee indirect de redactionele koers.', 'Redactionele lijn weerspiegelt voorkeuren van de eigenaar zonder expliciete instructies.'),
('budgetcontrole', 'eigendom', 'economisch', 'Eigenaar bepaalt het redactiebudget en beslist over bezuinigingen.', 'Minder middelen voor diepgravende, kritische journalistiek.');

-- Filter 2: Advertentie
INSERT INTO mechanisms (name, filter, mechanism_type, description, effect) VALUES
('supportive_selling_environment', 'advertentie', 'economisch', 'Media creëren een redactionele omgeving die bevorderlijk is voor de commerciële boodschap van adverteerders.', 'Structurele voorkeur voor content die het consumentistische wereldbeeld bevestigt.'),
('adverteerder_gevoeligheid', 'advertentie', 'economisch', 'Redacties vermijden berichtgeving die grote adverteerders kan schaden of irriteren.', 'Systeemkritiek op retail, FMCG of gokindustrie wordt vermeden.'),
('stakeholder_capitalism_frame', 'advertentie', 'discursief', 'Het WEF-concept stakeholder capitalism wordt als progressief gepresenteerd maar legitimeert de corporate elite.', 'Belangen van het grootbedrijf worden gepresenteerd als congruent met het algemeen belang.');

-- Filter 3: Sourcing
INSERT INTO mechanisms (name, filter, mechanism_type, description, effect) VALUES
('pakketjournalistiek', 'sourcing', 'procedureel', 'Grootschalig overnemen van ANP-berichten door gekrompen redacties, zonder eigen verificatie of aanvulling.', 'Homogenisering van het nieuwsbeeld; keuzes van één persbureau bepalen het landelijke nieuws.'),
('haagse_stam', 'sourcing', 'psychologisch', 'Politici, voorlichters, lobbyisten en journalisten in Den Haag functioneren als één stam met gedeelde codes.', 'Journalisten volgen de agenda van de politieke macht; fundamentele kritiek leidt tot uitsluiting.'),
('bronafhankelijkheid', 'sourcing', 'structureel', 'Journalisten zijn voor primeurs en achtergrond afhankelijk van de goodwill van machtige bronnen.', 'Zelfcensuur uit angst de bron te verliezen; berichtgeving volgt het frame van de bron.'),
('draaideurpersoneel', 'sourcing', 'structureel', 'Overstap van journalisten naar politiek/PR en vice versa creëert gedeelde referentiekaders.', 'Kritische distantie tussen journalistiek en macht wordt ondermijnd.'),
('denktank_als_bron', 'sourcing', 'procedureel', 'Door elites gefinancierde denktanks leveren schijnbaar objectieve analyses die door media worden overgenomen.', 'Beleidsvoorstellen die corporate belangen dienen krijgen een aureool van wetenschappelijke legitimiteit.'),
('woo_obstructie', 'sourcing', 'juridisch', 'Overheid handelt Woo-verzoeken traag en onwillig af, waardoor diepgravend onderzoek wordt gefrustreerd.', 'Journalisten worden afhankelijker van door de overheid zelf verstrekte informatie.');

-- Filter 4: Flak
INSERT INTO mechanisms (name, filter, mechanism_type, description, effect) VALUES
('etikettering', 'flak', 'discursief', 'Kritiek wordt gediskwalificeerd door de boodschapper te labelen: wappie, complotdenker, Poetin-versteher.', 'Legitieme vragen worden op één hoop gegooid met extreme complottheorieën en buiten het debat geplaatst.'),
('slapp_rechtszaken', 'flak', 'juridisch', 'Strategische rechtszaken om kritische journalisten financieel uit te putten en af te schrikken.', 'Afschrikwekkend effect; redacties worden risicomijdender bij gevoelige onderwerpen.'),
('uitsluiting_expert', 'flak', 'procedureel', 'Experts met afwijkende meningen worden niet meer uitgenodigd als commentator.', 'Afwijkende analyses verdwijnen uit het publieke debat (voorbeeld: Van Rossem na Irak-kritiek).'),
('onevenwichtige_debattafel', 'flak', 'procedureel', 'Eén criticus wordt geplaatst tegenover een overmacht van consensus-stemmen in talkshows.', 'Schijn van open debat terwijl de criticus structureel wordt geïsoleerd en overweldigd.'),
('morele_chantage', 'flak', 'discursief', 'Critici worden in het kamp van de vijand geplaatst: wie kritiek heeft op NAVO-beleid is een Kremlin-propagandist.', 'Debat over fundamentele premissen wordt onmogelijk gemaakt door morele druk.'),
('online_haatcampagne', 'flak', 'technologisch', 'Gecoördineerde online intimidatie, doxing en bedreigingen gericht op journalisten.', '61% van journalisten heeft te maken gehad met intimidatie; versterkt zelfcensuur.'),
('politieke_aanval_op_media', 'flak', 'discursief', 'Politieke partijen maken journalisten en mediaorganisaties actief zwart.', 'Ondermijning van publiek vertrouwen in de media; vijandig werkklimaat voor journalisten.');

-- Filter 4 (intern): Zelfcensuur
INSERT INTO mechanisms (name, filter, mechanism_type, description, effect) VALUES
('conformisme', 'flak', 'psychologisch', 'Normatieve en informationele sociale invloed: afwijkende mening wordt in het brein verwerkt als foutsignaal.', 'Journalisten passen hun standpunten aan de groepsnorm aan zonder externe druk.'),
('groepsdenken', 'flak', 'psychologisch', 'Sociologisch homogene redacties ontwikkelen een gedeeld, onuitgesproken referentiekader met blinde vlekken.', 'Grote delen van de samenleving blijven onderbelicht; systeemkritiek past niet in de redactiecultuur.'),
('hierarchische_zelfcensuur', 'flak', 'psychologisch', 'Journalisten leren snel welke onderwerpen gevoelig liggen en welke invalshoeken gewaardeerd worden.', 'Vermijding van controversiële verhalen uit angst voor professionele repercussies.');

-- Filter 5: Ideologie
INSERT INTO mechanisms (name, filter, mechanism_type, description, effect) VALUES
('neoliberaal_gezond_verstand', 'ideologie', 'discursief', 'Pro-markt, pro-elite, pro-Atlantisch denkkader wordt gepresenteerd als objectieve realiteit.', 'Alternatieve visies (degrowth, vermogensherverdeling, neutraliteit) worden als onrealistisch afgedaan.'),
('culturele_hegemonie', 'ideologie', 'psychologisch', 'De heersende klasse handhaaft macht door instemming te creëren via civil society-instituties.', 'Belangen van de elite worden geïnternaliseerd als de natuurlijke orde der dingen.'),
('spectrum_van_toegestane_opinie', 'ideologie', 'discursief', 'Levendig debat wordt toegestaan, maar alleen binnen strikt gedefinieerde, onuitgesproken grenzen.', 'Discussie over details is welkom, maar fundamentele premissen blijven buiten schot.'),
('naturalisering_van_elitebelangen', 'ideologie', 'discursief', 'Beurskoersen, economische groei en concurrentiepositie worden als de enige relevante parameters gepresenteerd.', 'Belangen van de TCC worden genaturaliseerd tot het algemeen belang.');

-- Cross-filter mechanismen
INSERT INTO mechanisms (name, filter, mechanism_type, description, effect) VALUES
('algoritmische_aandachtseconomie', 'cross_filter', 'technologisch', 'Platformalgoritmes maximaliseren engagement via emotionele content, niet journalistieke waarden.', 'Fragmentatie, polarisatie; media passen content aan aan algoritmische logica.'),
('emergente_bias', 'cross_filter', 'structureel', 'Pro-elite bias ontstaat als emergente eigenschap van het systeem zonder centraal commando.', 'Duizenden individuele keuzes op basis van dezelfde prikkels produceren uniform, statusquo-bevestigend nieuws.'),
('homeostase', 'cross_filter', 'structureel', 'Het systeem heeft een sterke neiging om terug te keren naar de evenwichtstoestand die de elite dient.', 'Enorme hoeveelheid tegenbewijs en maatschappelijke druk nodig om het narratief duurzaam te veranderen.');

