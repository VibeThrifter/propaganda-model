// Gedeelde UI-laag voor alle pagina's — hoort bij huisstijl.css. Laden via:
//   <script src="/static/huisstijl.js"></script>
// Levert zes dingen (classic script, geen module — bindingen zijn zichtbaar
// voor inline scripts die hierna laden, net als shared_vocab.js):
//   1. Topbal-navigatie: vult <header class="topbal" data-actief="…"> met het
//      merk, de paginalinks (Beheer alleen maintainer, na login)
//      en de account-chip. Pagina-eigen knoppen zet je in <div class="topbal-slot">.
//   2. melding(tekst, soort) — toast rechtsonder, vervangt alert().
//   3. bevestig(vraag, opties) / vraagTekst(vraag, opties) — nette dialogen,
//      vervangen confirm() en prompt(); geven een Promise terug.
//   4. Uitleg-popover: <button class="uitleg" data-uitleg="…">ⓘ</button> opent
//      op klik een popover (Esc/klik-buiten sluit) — uitleg die óók op touch en
//      toetsenbord bereikbaar is, waar een title-tooltip dat niet is.
//   5. Actie-menu: hsMenu(ankerKnop, items) — één ⋯-menu per element i.p.v. een
//      rij actieknoppen (W3.2); Esc sluit met focus terug, pijltjes ↑/↓.
//   6. Toetsenbord-bedienbaarheid: elk [onclick]-element krijgt automatisch
//      tabindex + role="button" en reageert op Enter/spatie.
//   7. Advertentie-consent (B6): op ad-dragende pagina's (<body data-ads>) een
//      lichte cookie-consent-banner die de ad-tag pas ná toestemming laadt.
//      Standaard UIT (AD_CLIENT leeg) — dan geen banner en niets extern.

// ── Merk (B2) — ÉÉN bron van waarheid voor de weergavenaam ──────────────
// Eigenaar-verwisselbaar: pas alleen deze twee strings aan om de héle voorkant
// (login/account/beheer/werkbank/overleg-topbal + de gedeelde voettekst) te
// hernoemen. De viz heeft z'n eigen topbar (web/template.html) en de <title>/OG-
// meta staan in de HTML — die spiegelen deze naam, dus verander ze mee. Sleutels,
// API en DB blijven ongewijzigd (puur een weergavelaag, zoals weergaveNaam()).
const HS_MERK = 'Propagandamodel';
const HS_MERK_SUB = 'Nederlandse politiek & media';

// ── Identiteit (één keer opgehaald, gedeeld met de pagina) ──────────────
let _hsMePromise = null;
function hsMe() {
  if (!_hsMePromise) {
    _hsMePromise = fetch('/api/me')
      .then(r => (r.ok ? r.json() : null))
      .catch(() => null);
  }
  return _hsMePromise;
}

function hsEsc(s) {
  return String(s ?? '').replace(/[&<>"]/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

// ── Topbal ──────────────────────────────────────────────────────────────
async function hsBouwTopbal() {
  const bal = document.querySelector('header.topbal');
  if (!bal || bal.dataset.gevuld) return;
  bal.dataset.gevuld = '1';
  const actief = bal.dataset.actief || '';

  const merk = document.createElement('a');
  merk.className = 'topbal-merk';
  merk.href = '/';
  merk.innerHTML = `${hsEsc(HS_MERK)}<span class="sub">${hsEsc(HS_MERK_SUB)}</span>`;

  const nav = document.createElement('nav');
  nav.className = 'topbal-nav';
  nav.setAttribute('aria-label', 'Hoofdnavigatie');
  const link = (pad, naam, key) => {
    const a = document.createElement('a');
    a.href = pad; a.textContent = naam;
    if (key === actief) { a.classList.add('actief'); a.setAttribute('aria-current', 'page'); }
    return a;
  };
  nav.append(link('/', 'Netwerk', 'netwerk'), link('/overleg', 'Overleg', 'overleg'),
             link('/methode', 'Methode', 'methode'));

  bal.prepend(merk, nav);

  const chip = document.createElement('a');
  chip.className = 'topbal-chip';
  chip.href = '/login';
  chip.textContent = '…';
  bal.append(chip);

  const me = await hsMe();
  if (me && !me.error) {
    if (me.role === 'maintainer') nav.append(link('/beheer', 'Beheer', 'beheer'));
    chip.href = '/account';
    chip.innerHTML = `${hsEsc(me.username)} <span style="color:var(--text-muted)">(${hsEsc(me.role)})</span>`;
    chip.title = 'Naar je accountpagina (token, uitloggen)';
  } else {
    chip.classList.add('invite');
    chip.textContent = '✎ Inloggen om bij te dragen';
    chip.title = 'Lezen kan vrij, zonder account. Log in om bij te dragen.';
  }
}

// ── Voettekst (J1) — gedeeld op élke pagina, net als de topbal ──────────
// Draagt de juridische posture (art. 43-UAVG-schild): op iedere publieke pagina
// een link naar de methodologie/verantwoording, de rectificatieflow (J2) en
// privacy. Auto-toegevoegd aan <body>; een pagina kan opt-outen met
// <body data-geen-voet>. De viz (web/template.html) stylet 'm compact (zie
// huisstijl.css .hs-voet + de viz-override).
const HS_VOET_LINKS = [
  ['Overzicht', '/overzicht'],
  ['Methode', '/methode'],
  ['Over', '/methode#verantwoording'],
  ['Rectificatie', '/rectificatie'],   // placeholder tot J2 (Fase 5)
  ['Privacy', '/methode#privacy'],
];
function hsBouwVoet() {
  if (document.body.dataset.geenVoet !== undefined) return;
  if (document.querySelector('footer.hs-voet')) return;
  const voet = document.createElement('footer');
  voet.className = 'hs-voet';
  const merk = document.createElement('span');
  merk.className = 'hs-voet-merk';
  merk.textContent = HS_MERK;
  const nav = document.createElement('nav');
  nav.setAttribute('aria-label', 'Voettekst');
  HS_VOET_LINKS.forEach(([naam, pad]) => {
    const a = document.createElement('a');
    a.href = pad; a.textContent = naam;
    nav.appendChild(a);
  });
  voet.append(merk, nav);
  document.body.appendChild(voet);
}

// ── Toast: melding(tekst, soort, duurMs) — vervangt alert() ────────────
// soort: 'info' | 'ok' | 'fout' | 'warn'
function melding(tekst, soort = 'info', duurMs = 4200) {
  let bak = document.getElementById('hsToosts');
  if (!bak) {
    bak = document.createElement('div');
    bak.id = 'hsToosts';
    bak.setAttribute('role', 'status');
    bak.setAttribute('aria-live', 'polite');
    document.body.appendChild(bak);
  }
  const t = document.createElement('div');
  t.className = 'toost ' + soort;
  t.textContent = tekst;
  bak.appendChild(t);
  const weg = () => { t.classList.add('weg'); setTimeout(() => t.remove(), 300); };
  t.addEventListener('click', weg);
  setTimeout(weg, duurMs);
  return t;
}

// ── Dialogen — vervangen confirm() en prompt() ─────────────────────────
function _hsDialoog(bouwInhoud) {
  return new Promise(resolve => {
    const vorigeFocus = document.activeElement;
    const overlay = document.createElement('div');
    overlay.className = 'hs-dlg-overlay';
    const dlg = document.createElement('div');
    dlg.className = 'hs-dlg';
    dlg.setAttribute('role', 'dialog');
    dlg.setAttribute('aria-modal', 'true');
    overlay.appendChild(dlg);

    let klaarGemeld = false;
    const klaar = (waarde) => {
      if (klaarGemeld) return;
      klaarGemeld = true;
      document.removeEventListener('keydown', opEscape, true);
      overlay.remove();
      if (vorigeFocus && vorigeFocus.focus) vorigeFocus.focus();
      resolve(waarde);
    };
    const opEscape = (e) => {
      if (e.key === 'Escape') { e.stopPropagation(); klaar(bouwInhoud.annuleerWaarde); }
    };
    document.addEventListener('keydown', opEscape, true);
    overlay.addEventListener('mousedown', e => {
      if (e.target === overlay) klaar(bouwInhoud.annuleerWaarde);
    });

    bouwInhoud(dlg, klaar);
    document.body.appendChild(overlay);
  });
}

// bevestig('Weet je het zeker?', {titel, okTekst, annuleerTekst, gevaar}) → Promise<boolean>
function bevestig(vraag, opties = {}) {
  const { titel = 'Bevestigen', okTekst = 'OK', annuleerTekst = 'Annuleren', gevaar = false } = opties;
  const bouw = (dlg, klaar) => {
    dlg.innerHTML = `
      <h3>${hsEsc(titel)}</h3>
      <div class="dlg-tekst">${hsEsc(vraag)}</div>
      <div class="dlg-acties">
        <button type="button" class="dlg-annuleer">${hsEsc(annuleerTekst)}</button>
        <button type="button" class="${gevaar ? 'gevaar' : 'prim'} dlg-ok">${hsEsc(okTekst)}</button>
      </div>`;
    dlg.querySelector('.dlg-ok').addEventListener('click', () => klaar(true));
    dlg.querySelector('.dlg-annuleer').addEventListener('click', () => klaar(false));
    // Bij een destructieve vraag start de focus op de veilige keuze.
    dlg.querySelector(gevaar ? '.dlg-annuleer' : '.dlg-ok').focus();
  };
  bouw.annuleerWaarde = false;
  return _hsDialoog(bouw);
}

// vraagTekst('Motivatie?', {titel, label, placeholder, beginwaarde, verplicht,
//   okTekst, gevaar, meerregels, hint}) → Promise<string|null>  (null = geannuleerd)
function vraagTekst(vraag, opties = {}) {
  const {
    titel = '', label = '', placeholder = '', beginwaarde = '',
    verplicht = true, okTekst = 'Opslaan', annuleerTekst = 'Annuleren',
    gevaar = false, meerregels = true, hint = '',
  } = opties;
  const bouw = (dlg, klaar) => {
    dlg.innerHTML = `
      ${titel ? `<h3>${hsEsc(titel)}</h3>` : ''}
      <div class="dlg-tekst">${hsEsc(vraag)}</div>
      ${label ? `<label class="veldlabel">${hsEsc(label)}</label>` : ''}
      ${meerregels
        ? `<textarea class="dlg-invoer" placeholder="${hsEsc(placeholder)}"></textarea>`
        : `<input type="text" class="dlg-invoer" placeholder="${hsEsc(placeholder)}">`}
      <div class="dlg-hint">${hsEsc(hint) || (meerregels ? 'Ctrl+Enter = opslaan · Esc = annuleren' : 'Enter = opslaan · Esc = annuleren')}</div>
      <div class="dlg-acties">
        <button type="button" class="dlg-annuleer">${hsEsc(annuleerTekst)}</button>
        <button type="button" class="${gevaar ? 'gevaar' : 'prim'} dlg-ok">${hsEsc(okTekst)}</button>
      </div>`;
    const invoer = dlg.querySelector('.dlg-invoer');
    const ok = dlg.querySelector('.dlg-ok');
    invoer.value = beginwaarde;
    const bijwerken = () => { ok.disabled = verplicht && !invoer.value.trim(); };
    invoer.addEventListener('input', bijwerken);
    bijwerken();
    const opslaan = () => { if (!ok.disabled) klaar(invoer.value.trim()); };
    ok.addEventListener('click', opslaan);
    dlg.querySelector('.dlg-annuleer').addEventListener('click', () => klaar(null));
    invoer.addEventListener('keydown', e => {
      if (e.key === 'Enter' && (!meerregels || e.ctrlKey || e.metaKey)) { e.preventDefault(); opslaan(); }
    });
    invoer.focus();
  };
  bouw.annuleerWaarde = null;
  return _hsDialoog(bouw);
}

// ── Uitleg-popover: klikbare ⓘ (vervangt title-only tooltips) ───────────
// Eén popover tegelijk; sluit met Esc, klik-buiten, nogmaals klikken of scrollen.
// Klik-afhandeling in de capture-fase mét stopPropagation: een ⓘ in een <label>
// mag de checkbox niet omzetten en een ⓘ in een inklapbare kop niet inklappen.
let _hsPopover = null, _hsPopoverKnop = null;
function hsSluitUitleg() {
  if (!_hsPopover) return;
  _hsPopover.remove();
  _hsPopover = null;
  if (_hsPopoverKnop) { _hsPopoverKnop.setAttribute('aria-expanded', 'false'); _hsPopoverKnop = null; }
}
function hsToonUitleg(knop) {
  hsSluitUitleg();
  const tekst = knop.dataset.uitleg || '';
  if (!tekst) return;
  _hsPopover = document.createElement('div');
  _hsPopover.className = 'hs-popover';
  _hsPopover.setAttribute('role', 'note');
  _hsPopover.textContent = tekst;   // altijd platte tekst — geen HTML-injectie
  document.body.appendChild(_hsPopover);
  const r = knop.getBoundingClientRect();
  const p = _hsPopover.getBoundingClientRect();
  const x = Math.min(Math.max(8, r.left + r.width / 2 - p.width / 2), window.innerWidth - p.width - 8);
  let y = r.bottom + 6;
  if (y + p.height > window.innerHeight - 8) y = Math.max(8, r.top - p.height - 6);
  _hsPopover.style.left = x + 'px';
  _hsPopover.style.top = y + 'px';
  knop.setAttribute('aria-expanded', 'true');
  _hsPopoverKnop = knop;
}
document.addEventListener('click', e => {
  const knop = e.target instanceof Element ? e.target.closest('button.uitleg') : null;
  if (knop) {
    e.preventDefault();
    e.stopPropagation();
    if (_hsPopoverKnop === knop) hsSluitUitleg(); else hsToonUitleg(knop);
    return;
  }
  if (_hsPopover && !(e.target instanceof Element && e.target.closest('.hs-popover'))) hsSluitUitleg();
  // Actie-menu: klik buiten menu én ankerknop sluit. Een klik op de ankerknop zelf
  // laten we door naar zijn eigen onclick — hsMenu toggelt daar (nogmaals = sluiten).
  if (_hsMenu) {
    const t = e.target instanceof Element ? e.target : null;
    if (!t || (!t.closest('.hs-menu') && !(_hsMenuAnker && _hsMenuAnker.contains(t)))) hsSluitMenu();
  }
}, true);
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { hsSluitUitleg(); hsSluitMenu(true); }
});
window.addEventListener('scroll', () => { hsSluitUitleg(); hsSluitMenu(); }, true);

// ── Actie-menu: hsMenu(anker, items) — één ⋯-menu i.p.v. een rij knoppen ──
// items: {label, onClick, gevaar?, titel?} of '---' (scheidingslijn). Eén menu
// tegelijk; nogmaals klikken op dezelfde knop sluit; Esc sluit met focus terug
// op de knop; pijltjes ↑/↓ lopen door de items (rondlopend).
let _hsMenu = null, _hsMenuAnker = null;
function hsSluitMenu(focusTerug) {
  if (!_hsMenu) return;
  _hsMenu.remove();
  _hsMenu = null;
  const anker = _hsMenuAnker;
  _hsMenuAnker = null;
  if (anker) {
    anker.setAttribute('aria-expanded', 'false');
    if (focusTerug && anker.focus) anker.focus();
  }
}
function hsMenu(anker, items) {
  if (_hsMenuAnker === anker) { hsSluitMenu(); return; }
  hsSluitMenu();
  hsSluitUitleg();
  items = (items || []).filter(Boolean);
  if (!items.length) return;
  const m = document.createElement('div');
  m.className = 'hs-menu';
  m.setAttribute('role', 'menu');
  items.forEach(it => {
    if (it === '---') {
      const s = document.createElement('div');
      s.className = 'hs-menu-scheiding';
      m.appendChild(s);
      return;
    }
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'hs-menu-item' + (it.gevaar ? ' gevaar' : '');
    b.setAttribute('role', 'menuitem');
    b.textContent = it.label;   // altijd platte tekst — geen HTML-injectie
    if (it.titel) b.title = it.titel;
    b.addEventListener('click', e => {
      e.stopPropagation();
      hsSluitMenu();
      if (it.onClick) it.onClick();
    });
    m.appendChild(b);
  });
  m.addEventListener('keydown', e => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    e.preventDefault();
    const its = [...m.querySelectorAll('.hs-menu-item')];
    if (!its.length) return;
    const i = its.indexOf(document.activeElement);
    its[(e.key === 'ArrowDown' ? i + 1 : i - 1 + its.length) % its.length].focus();
  });
  document.body.appendChild(m);
  // Positioneer onder de knop, rechterranden uitgelijnd; flip naar boven als het
  // niet past en klem binnen het scherm.
  const r = anker.getBoundingClientRect();
  const p = m.getBoundingClientRect();
  const x = Math.min(Math.max(8, r.right - p.width), window.innerWidth - p.width - 8);
  let y = r.bottom + 4;
  if (y + p.height > window.innerHeight - 8) y = Math.max(8, r.top - p.height - 4);
  m.style.left = x + 'px';
  m.style.top = y + 'px';
  anker.setAttribute('aria-expanded', 'true');
  _hsMenu = m;
  _hsMenuAnker = anker;
  const eerste = m.querySelector('.hs-menu-item');
  if (eerste) eerste.focus();
}

// ── Toetsenbord-bedienbaarheid voor [onclick]-elementen ─────────────────
// Veel bediening is historisch een <span onclick> of <div onclick>; die zijn
// zonder muis onbereikbaar. Geef ze automatisch tabindex + role zodat ze
// focusbaar zijn, en laat Enter/spatie het click-gedrag uitvoeren.
const _HS_NATIEF = 'a,button,input,select,textarea,summary,label';
function hsMaakFocusbaar(wortel) {
  (wortel || document.body).querySelectorAll('[onclick]').forEach(el => {
    if (el.matches(_HS_NATIEF) || el.closest(_HS_NATIEF)) return;
    if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
    if (!el.hasAttribute('role')) el.setAttribute('role', 'button');
  });
}
let _hsFocusTimer = null;
function _hsFocusGepland() {
  clearTimeout(_hsFocusTimer);
  _hsFocusTimer = setTimeout(() => hsMaakFocusbaar(), 80);
}
document.addEventListener('keydown', e => {
  if ((e.key === 'Enter' || e.key === ' ')
      && e.target instanceof Element
      && e.target.getAttribute('role') === 'button'
      && e.target.hasAttribute('onclick')) {
    e.preventDefault();
    e.target.click();
  }
});

// ── Advertenties + cookie-consent (B6) — SCAFFOLD, standaard UIT ────────
// LET OP: dit is de éérste plek waar de app ooit een *extern* script/cookie
// zou introduceren. Standaard gebeurt dat NIET: AD_CLIENT is leeg, dus er
// laadt geen ad-script, er wordt geen consent-banner getoond en er komen geen
// cookies bij — alleen de gereserveerde placeholder in de .ad-slot blijft staan.
// De eigenaar activeert door AD_CLIENT + AD_SCRIPT_URL in te vullen (OWNER-
// ACTION; zet dan óók de bijpassende AD_CSP_*-domeinen in server.py). Ads laden
// pas ná expliciete toestemming; bij weigeren komen er geen ad-cookies.
// De banner verschijnt alléén op ad-dragende pagina's (<body data-ads>) — dus
// op de element-pagina's, nooit op de viz (/) of de redactie-routes.
const AD_CLIENT = '';        // bv. 'ca-pub-XXXXXXXXXXXXXXXX' (AdSense) — leeg = uit
const AD_SCRIPT_URL = '';    // bv. 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-…'
const AD_CONSENT_KEY = 'hs-ad-consent';   // localStorage: 'ja' = geaccepteerd, 'nee' = geweigerd

function _hsAdConfig() {
  // Ads zijn pas "actief te maken" als de pagina ad-dragend is én de eigenaar
  // een publisher-ID + script-URL heeft ingevuld. Zonder dat: pure scaffold.
  return document.body && document.body.hasAttribute('data-ads') && AD_CLIENT && AD_SCRIPT_URL;
}
function _hsAdConsent() {
  try { return localStorage.getItem(AD_CONSENT_KEY); } catch (e) { return null; }
}
function _hsZetAdConsent(waarde) {
  try { localStorage.setItem(AD_CONSENT_KEY, waarde); } catch (e) { /* private mode: sla stil over */ }
}

// Injecteert de ad-tag ná toestemming. Generiek AdSense-vormig sjabloon: de
// eigenaar past het aan het gekozen netwerk aan. Draait nooit zonder consent.
let _hsAdsGeladen = false;
function hsLaadAdvertenties() {
  if (_hsAdsGeladen || !_hsAdConfig()) return;
  _hsAdsGeladen = true;
  const s = document.createElement('script');
  s.src = AD_SCRIPT_URL;
  s.async = true;
  s.crossOrigin = 'anonymous';
  s.setAttribute('data-ad-client', AD_CLIENT);
  document.head.appendChild(s);
  document.querySelectorAll('.ad-slot').forEach(slot => {
    slot.innerHTML = '';
    slot.classList.add('ad-actief');
    const ins = document.createElement('ins');
    ins.className = 'adsbygoogle';
    ins.style.display = 'block';
    ins.setAttribute('data-ad-client', AD_CLIENT);
    ins.setAttribute('data-ad-format', 'auto');
    ins.setAttribute('data-full-width-responsive', 'true');
    slot.appendChild(ins);
    try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch (e) { /* netwerk laadt nog */ }
  });
}

function _hsBouwConsentBanner() {
  if (document.querySelector('.hs-consent')) return;
  const bak = document.createElement('div');
  bak.className = 'hs-consent';
  bak.setAttribute('role', 'dialog');
  bak.setAttribute('aria-live', 'polite');
  bak.setAttribute('aria-label', 'Cookie-toestemming');
  bak.innerHTML = `
    <div class="hs-consent-tekst">
      Deze pagina toont advertenties die cookies plaatsen. We laden ze pas met
      jouw toestemming. Weiger je, dan komen er geen advertentie-cookies.
      <a href="/methode#privacy">Meer over privacy</a>.
    </div>
    <div class="hs-consent-acties">
      <button type="button" class="hs-consent-weiger">Weigeren</button>
      <button type="button" class="prim hs-consent-akkoord">Advertenties toestaan</button>
    </div>`;
  const sluit = () => bak.remove();
  bak.querySelector('.hs-consent-akkoord').addEventListener('click', () => {
    _hsZetAdConsent('ja'); sluit(); hsLaadAdvertenties();
  });
  bak.querySelector('.hs-consent-weiger').addEventListener('click', () => {
    _hsZetAdConsent('nee'); sluit();   // geen ad-tag, geen ad-cookies
  });
  document.body.appendChild(bak);
}

function hsConsentEnAds() {
  if (!_hsAdConfig()) return;   // scaffold-staat: geen banner, geen externe scripts
  const keuze = _hsAdConsent();
  if (keuze === 'ja') hsLaadAdvertenties();
  else if (keuze === 'nee') { /* respecteer weigering, toon niets opnieuw */ }
  else _hsBouwConsentBanner();
}

function _hsInit() {
  hsBouwTopbal();
  hsBouwVoet();
  hsConsentEnAds();
  hsMaakFocusbaar();
  new MutationObserver(_hsFocusGepland).observe(document.body, { childList: true, subtree: true });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', _hsInit);
else _hsInit();
