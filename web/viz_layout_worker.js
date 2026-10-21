// Layout-worker voor de netwerkvisualisatie (web/template.html).
//
// De force-layout (d3-force) draait hier, buiten de hoofdthread: zo blijft pannen,
// zoomen en klikken vloeiend terwijl het netwerk zich ordent. De pagina stuurt een
// 'run' met knopen (posities, straal, vast/los) en verbindingen (indexparen); de
// worker stuurt tussenstanden ('tick') en de eindstand ('end') terug als Float32Array.
// Een nieuwe 'run' breekt de lopende af (de pagina telt alleen het laatste runId).
// Zelfde bundel als de pagina zelf laadt: komt uit de HTTP-cache, geen extra download.
importScripts('https://d3js.org/d3.v7.min.js');

let huidig = 0;   // runId van de lopende berekening

function run(msg) {
  const id = msg.runId;
  huidig = id;
  const n = msg.x.length;
  const p = msg.params;
  const nodes = new Array(n);
  for (let i = 0; i < n; i++) {
    const nd = { index: i, x: msg.x[i], y: msg.y[i], r: msg.r[i] };
    if (msg.fixed[i]) { nd.fx = msg.x[i]; nd.fy = msg.y[i]; }
    nodes[i] = nd;
  }
  const links = [];
  for (let k = 0; k < msg.links.length; k += 2) {
    links.push({ source: msg.links[k], target: msg.links[k + 1] });
  }
  const sim = d3.forceSimulation(nodes)
    .stop()
    .alpha(p.alpha)
    .alphaMin(p.alphaMin || 0.002)
    .alphaDecay(p.alphaDecay)
    .velocityDecay(p.velocityDecay)
    .force('link', d3.forceLink(links)
      .distance(l => p.linkDist + (l.source.r + l.target.r) * 0.6))
    .force('charge', d3.forceManyBody().strength(p.charge).distanceMax(p.distanceMax).theta(0.9))
    .force('collide', d3.forceCollide().radius(d => d.r + p.collidePad).strength(0.85).iterations(1))
    .force('x', d3.forceX(p.cx).strength(p.gravity))
    .force('y', d3.forceY(p.cy).strength(p.gravity));
  if (!(p.linkStrength == null)) sim.force('link').strength(p.linkStrength);

  const maxTicks = p.maxTicks || 400;
  let ticks = 0;
  const xy = () => {
    const out = new Float32Array(n * 2);
    for (let i = 0; i < n; i++) { out[2 * i] = nodes[i].x; out[2 * i + 1] = nodes[i].y; }
    return out;
  };
  // In porties rekenen zodat een nieuwe 'run' (onmessage) tussendoor kan binnenkomen.
  const portie = () => {
    if (huidig !== id) return;                       // afgebroken door een nieuwere run
    const t0 = performance.now();
    while (performance.now() - t0 < 40 && sim.alpha() > sim.alphaMin() && ticks < maxTicks) {
      sim.tick();
      ticks++;
    }
    const klaar = sim.alpha() <= sim.alphaMin() || ticks >= maxTicks;
    const buf = xy();
    postMessage({ type: klaar ? 'end' : 'tick', runId: id, xy: buf, ticks }, [buf.buffer]);
    if (!klaar) setTimeout(portie, 0);
  };
  portie();
}

onmessage = (e) => {
  const msg = e.data;
  if (msg.type === 'run') run(msg);
  else if (msg.type === 'stop') huidig = -1;
};
