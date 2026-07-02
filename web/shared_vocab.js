// Gedeelde model-woordenschat — de ruggengraat van het model: de vijf filters
// (1 Eigendom … 5 Ideologie) plus tegenmacht/systeemactor/cross_filter/overig.
//
// EÉN bron van waarheid voor zowel de netwerkvisualisatie (web/template.html →
// index.html, ingelined door scripts/generate_viz.py) als de overlegpagina
// (web/overleg.html, geladen via <script src="/static/shared_vocab.js">). Zo hoeft
// een kleur- of labelwijziging niet op twee plekken — anders lopen de oppervlakken uiteen.
//
// LET OP: classic script, geen module. De const-bindingen zijn zichtbaar voor de
// inline scripts die hierna laden. Definieer ze hier dus NIET ook nog elders.
const FILTER_COLORS = {
  eigendom: '#e74c3c', advertentie: '#f0a030', sourcing: '#3498db',
  flak: '#9b59b6', ideologie: '#2ecc71',
  systeemactor: '#e8c547', cross_filter: '#fd79a8',
  tegenmacht: '#1abc9c',
  overig: '#7f8c9a',
};
const FILTER_LABELS = {
  eigendom: '1. Eigendom', advertentie: '2. Advertentie', sourcing: '3. Sourcing',
  flak: '4. Flak', ideologie: '5. Ideologie',
  systeemactor: 'Systeemactor', tegenmacht: 'Tegenmacht', cross_filter: 'Cross-filter',
  overig: 'Overig',
};

// ── Leesbare namen (W2.3) ─────────────────────────────────────────────────
// Rollen/mechanismen/entiteitstypen heten in de database snake_case (dat blijft
// de sleutel — API, scores en zoeklogica veranderen niet); de UI toont overal de
// weergavenaam. Automatische afleiding: underscores → spaties + beginhoofdletter.
// Alleen waar dat spelling of betekenis breekt (trema's, koppeltekens,
// afkortingen, richting) staat hier een uitzondering.
const NAAM_WEERGAVE = {
  // Rollen
  mediaeigenaar: 'Media-eigenaar',
  raad_van_commissarissen: 'Raad van commissarissen (RvC)',
  columnist_opiniemaker: 'Columnist / opiniemaker',
  elite_forum: 'Elite-forum',
  vakbond_media: 'Vakbond (media)',
  // Mechanismen — spelling (trema's, koppeltekens, afkortingen)
  commerciele_afhankelijkheid: 'Commerciële afhankelijkheid',
  continuiteitsborging: 'Continuïteitsborging',
  gecoordineerde_voorlichting: 'Gecoördineerde voorlichting',
  inlichtingen_cooptatie: 'Inlichtingen-coöptatie',
  pr_inhuur: 'PR-inhuur',
  pr_subsidie: 'PR-subsidie',
  woo_obstructie: 'Woo-obstructie',
  stak_stemzeggenschap: 'STAK-stemzeggenschap',
  cross_media_eigendom: 'Cross-media-eigendom',
  media_agendering: 'Media-agendering',
  intermedia_agendering: 'Intermedia-agendering',
  journalist_bronrelatie: 'Journalist-bronrelatie',
  // Mechanismen — elite-netwerkfamilie
  belang_elite_netwerk: 'Belanghebbende in elite-netwerk',
  mediaeigenaar_elite_netwerk: 'Media-eigenaar in elite-netwerk',
  politicus_elite_netwerk: 'Politicus in elite-netwerk',
  elite_media_netwerk: 'Elite-medianetwerk',
  elite_kennisnetwerk: 'Elite-kennisnetwerk',
  // Mechanismen — richting (draaideur is wederzijds, levering is gericht)
  draaideur_journalistiek_politiek: 'Draaideur journalistiek ↔ politiek',
  draaideur_journalistiek_voorlichting: 'Draaideur journalistiek ↔ voorlichting',
  draaideur_politiek_bedrijfsleven: 'Draaideur politiek ↔ bedrijfsleven',
  draaideur_politiek_institutie: 'Draaideur politiek ↔ institutie',
  draaideur_politiek_lobby: 'Draaideur politiek ↔ lobby',
  draaideur_politiek_media: 'Draaideur politiek ↔ media',
  denktank_naar_persbureau: 'Denktank → persbureau',
  denktank_naar_politiek: 'Denktank → politiek',
  lobbyist_naar_journalist: 'Lobbyist → journalist',
  lobbyist_naar_politicus: 'Lobbyist → politicus',
  // Mechanismen — variant tussen haakjes leest beter dan een woordreeks
  academische_socialisatie_hoofdredacteur: 'Academische socialisatie (hoofdredacteur)',
  academische_socialisatie_politiek: 'Academische socialisatie (politiek)',
  academische_orthodoxie_denktank: 'Academische orthodoxie (denktank)',
  academische_orthodoxie_instituut: 'Academische orthodoxie (instituut)',
  // Entiteitstypen
  pr_bureau: 'PR-bureau',
  ngo: 'NGO',
  elite_netwerk: 'Elite-netwerk',
};
function weergaveNaam(naam) {
  if (naam == null || naam === '') return '';
  const s = String(naam);
  if (Object.prototype.hasOwnProperty.call(NAAM_WEERGAVE, s)) return NAAM_WEERGAVE[s];
  const vlak = s.replace(/_/g, ' ').trim();
  return vlak.charAt(0).toUpperCase() + vlak.slice(1);
}
