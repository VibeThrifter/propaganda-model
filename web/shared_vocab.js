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
