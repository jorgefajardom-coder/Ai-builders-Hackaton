"""Genera site/index.html con toda la documentación del proyecto.

Fuentes: README.md (EN|ES), el vault de Obsidian en docs/, material/README.md,
experimentos.jsonl (estadísticas en vivo) y el historial de git.

Uso:
    python tools/build_docs.py            # genera una vez
    python tools/build_docs.py --watch    # regenera al detectar cambios (cada 2 s)

El HTML es autocontenido (los datos van embebidos); solo carga marked y mermaid
desde CDN para renderizar. Al servirse por HTTP (GitHub Pages o un servidor local),
la página consulta site/version.json y se recarga sola cuando hay una versión nueva.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "site"
DOCS = ROOT / "docs"
EXCLUDE_DIRS = {".obsidian", ".trash", "Plantillas"}
# Defensa en profundidad: nada con forma de token llega al sitio publicado.
SECRET_PATTERNS = [re.compile(r"cn-p-[A-Za-z0-9_\-]{10,}"), re.compile(r"ftr_[A-Za-z0-9]{16,}")]


def redact(text):
    for p in SECRET_PATTERNS:
        text = p.sub("[token-redactado]", text)
    return text


def read(path):
    return redact(path.read_text(encoding="utf-8"))


def split_frontmatter(md):
    meta = {}
    if md.startswith("---\n") or md.startswith("---\r\n"):
        end = md.find("\n---", 4)
        if end != -1:
            for line in md[4:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
            md = md[end + 4:].lstrip("\r\n")
    tags = meta.get("tags", "")
    meta["tags"] = [t.strip() for t in tags.strip("[]").split(",") if t.strip()] if tags else []
    return meta, md


def slug(text):
    s = re.sub(r"[^\w\s-]", "", text.lower().replace("/", " ").replace("\\", " "), flags=re.UNICODE)
    return re.sub(r"[\s_]+", "-", s).strip("-")


ASSETS = OUT_DIR / "assets"
IMG_RE = re.compile(r"!\[([^\]]*)\]\((?!https?:|data:)([^)\s]+)\)")


def localize_images(md, base_dir):
    """Copia a site/assets/ las imágenes referenciadas con ruta relativa y reescribe el enlace."""
    def repl(m):
        src = (base_dir / m.group(2).replace("%20", " ")).resolve()
        if not src.is_file() or ROOT not in src.parents:
            return m.group(0)
        ASSETS.mkdir(parents=True, exist_ok=True)
        name = f"{hashlib.sha1(str(src.relative_to(ROOT)).encode()).hexdigest()[:8]}-{src.name.replace(' ', '-')}"
        dst = ASSETS / name
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            dst.write_bytes(src.read_bytes())
        return f"![{m.group(1)}](assets/{name})"
    return IMG_RE.sub(repl, md)


def collect_docs():
    docs = []
    for p in sorted(DOCS.rglob("*.md")):
        rel = p.relative_to(DOCS)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        meta, body = split_frontmatter(read(p))
        body = localize_images(body, p.parent)
        group = rel.parts[0] if len(rel.parts) > 1 else "General"
        if len(rel.parts) > 2:
            group = f"{rel.parts[0]} / {rel.parts[1]}"
        docs.append({
            "id": slug(str(rel.with_suffix(""))),
            "title": p.stem,
            "path": f"docs/{rel.as_posix()}",
            "group": group,
            "tags": meta["tags"],
            "meta": {k: v for k, v in meta.items() if k != "tags"},
            "md": body,
            "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return docs


def split_readme():
    p = ROOT / "README.md"
    if not p.exists():
        return {"en": "", "es": ""}
    text = localize_images(read(p), ROOT)
    m = re.search(r"\n(?:---\n)+\s*\n# Caja Negra\s+-\s+Servicio", text)
    if not m:
        return {"en": text, "es": text}
    return {"en": text[:m.start()], "es": text[m.start():].lstrip("-\n ")}


def experiment_stats():
    p = ROOT / "experimentos.jsonl"
    if not p.exists():
        return None
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(redact(line)))
            except ValueError:
                pass
    by_seq = defaultdict(lambda: {"n": 0, "first": None, "last": None, "hipotesis": None})
    status = Counter()
    errors = {}
    for r in rows:
        s = by_seq[r.get("seq", "?")]
        s["n"] += 1
        s["first"] = s["first"] or r.get("id")
        s["last"] = r.get("id")
        if s["hipotesis"] is None and r.get("ruta") != "/__reset":
            s["hipotesis"] = r.get("hipotesis")
        status[str(r.get("status"))] += 1
        resp = r.get("response")
        if isinstance(resp, dict) and "error" in resp:
            code = resp["error"]
            e = errors.setdefault(code, {"code": code, "status": r.get("status"), "mensaje": resp.get("mensaje"),
                                         "count": 0, "first": r.get("id")})
            e["count"] += 1
    interesting = [r for r in rows if not (isinstance(r.get("response"), dict)
                                            and r["response"].get("error") == "E202"
                                            and "barrido" in (r.get("hipotesis") or ""))]
    return {
        "total": len(rows),
        "budget": 8000,
        "seqs": [{"seq": k, **v} for k, v in by_seq.items()],
        "status": dict(sorted(status.items())),
        "errors": sorted(errors.values(), key=lambda e: e["code"]),
        "notable": interesting[-300:],
    }


def git_log():
    try:
        out = subprocess.run(["git", "log", "--date=format:%Y-%m-%d %H:%M", "--pretty=%h\t%ad\t%s", "-n", "100"],
                             cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    return [dict(zip(("hash", "date", "msg"), l.split("\t", 2))) for l in out.splitlines() if l.count("\t") >= 2]


def build():
    data = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "readme": split_readme(),
        "material": read(ROOT / "material" / "README.md") if (ROOT / "material" / "README.md").exists() else "",
        "docs": collect_docs(),
        "exp": experiment_stats(),
        "commits": git_log(),
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    version = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    data_tag = f'<script id="data" type="application/json">{payload}</script>'
    html = TEMPLATE.replace("__VERSION__", version).replace("<!--DATA-->", data_tag)
    OUT_DIR.mkdir(exist_ok=True)
    write_atomic(OUT_DIR / "index.html", html)
    write_atomic(OUT_DIR / "version.json", json.dumps({"version": version, "generated": data["generated"]}))
    write_atomic(OUT_DIR / ".nojekyll", "")
    return version, data


def write_atomic(path, text):
    """Escribe a un temporal y lo renombra: nunca deja el archivo a medias si dos builds coinciden."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    for attempt in range(10):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.2 * (attempt + 1))
    os.replace(tmp, path)


def watched_mtimes():
    paths = [ROOT / "README.md", ROOT / "experimentos.jsonl", ROOT / "material" / "README.md",
             ROOT / ".git" / "HEAD", ROOT / ".git" / "refs" / "heads", Path(__file__)]
    paths += [p for p in DOCS.rglob("*.md")]
    out = {}
    for p in paths:
        try:
            if p.is_dir():
                for q in p.rglob("*"):
                    out[str(q)] = q.stat().st_mtime
            else:
                out[str(p)] = p.stat().st_mtime
        except OSError:
            pass
    return out


def main():
    # La consola de Windows usa cp1252 por defecto; sin esto, imprimir "·" o tildes tumba el observador.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    version, data = build()
    print(f"site/index.html generado · versión {version} · {len(data['docs'])} notas · "
          f"{data['exp']['total'] if data['exp'] else 0} experimentos")
    if "--watch" in sys.argv:
        print("Observando cambios (Ctrl+C para salir)...")
        last = watched_mtimes()
        while True:
            time.sleep(2)
            now = watched_mtimes()
            if now != last:
                last = now
                # Proceso nuevo en cada build: si cambia este mismo generador, se usa el código actual.
                r = subprocess.run([sys.executable, __file__], cwd=ROOT, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
                msg = (r.stdout.strip() or r.stderr.strip().splitlines()[-1:] or ["?"])
                msg = msg if isinstance(msg, str) else msg[0]
                print(f"[{datetime.now():%H:%M:%S}] {'regenerado' if r.returncode == 0 else 'ERROR'} · {msg}", flush=True)


TEMPLATE = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="doc-version" content="__VERSION__">
<title>Caja Negra · Documentación</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#ffffff; --panel:#f7f7f9; --panel-2:#efeff3; --border:#e2e2e8; --text:#16161a; --muted:#62626e;
  --accent:#5b4fd6; --accent-soft:#ecebfd; --ok:#1d9e75; --warn:#b7791f; --err:#c0392b; --code:#f2f2f6;
  --mono:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace; --sans:'Inter',system-ui,sans-serif;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0b0b0d; --panel:#111114; --panel-2:#17171c; --border:#26262e; --text:#ececf1; --muted:#9a9aa6;
    --accent:#a99cff; --accent-soft:#1d1a33; --ok:#3ccf9b; --warn:#e3b341; --err:#ff6b5e; --code:#15151a;
  }
}
:root[data-theme="dark"]{
  --bg:#0b0b0d; --panel:#111114; --panel-2:#17171c; --border:#26262e; --text:#ececf1; --muted:#9a9aa6;
  --accent:#a99cff; --accent-soft:#1d1a33; --ok:#3ccf9b; --warn:#e3b341; --err:#ff6b5e; --code:#15151a;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);font-size:15px;line-height:1.6}
a{color:var(--accent);text-decoration:none} a:hover{text-decoration:underline}
.layout{display:grid;grid-template-columns:290px 1fr;min-height:100vh}
aside{border-right:1px solid var(--border);background:var(--panel);position:sticky;top:0;height:100vh;overflow:auto;padding:20px 16px}
.brand{font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.brand b{display:block;font-family:var(--sans);font-size:18px;letter-spacing:0;text-transform:none;color:var(--text);margin-top:4px}
.search{width:100%;margin:16px 0 8px;padding:8px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font:inherit}
.navgroup{margin-top:14px}
.navgroup h4{margin:0 0 4px;font-family:var(--mono);font-size:11px;font-weight:500;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.navgroup a{display:block;padding:4px 8px;border-radius:6px;color:var(--text);font-size:14px}
.navgroup a:hover{background:var(--panel-2);text-decoration:none}
.navgroup a.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
main{min-width:0;padding:28px 48px 80px;max-width:1100px}
.topbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:20px;font-family:var(--mono);font-size:12px;color:var(--muted)}
.pill{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--border);border-radius:999px;padding:3px 10px;background:var(--panel)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--ok)}
.btn{cursor:pointer;border:1px solid var(--border);background:var(--panel);color:var(--text);border-radius:8px;padding:4px 10px;font:inherit;font-size:12px}
.btn.on{border-color:var(--accent);color:var(--accent)}
.doc h1{font-size:28px;line-height:1.25;margin:.2em 0 .6em}
.doc h2{font-size:21px;margin:1.8em 0 .6em;padding-bottom:6px;border-bottom:1px solid var(--border)}
.doc h3{font-size:17px;margin:1.4em 0 .5em}
.doc table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px;display:block;overflow-x:auto}
.doc th,.doc td{border:1px solid var(--border);padding:7px 10px;text-align:left;vertical-align:top}
.doc th{background:var(--panel);font-weight:600}
.doc code{font-family:var(--mono);font-size:.88em;background:var(--code);padding:1px 5px;border-radius:4px}
.doc pre{background:var(--code);border:1px solid var(--border);border-radius:8px;padding:14px;overflow:auto}
.doc pre code{background:none;padding:0}
.doc blockquote{margin:12px 0;padding:8px 14px;border-left:3px solid var(--accent);background:var(--panel);border-radius:0 8px 8px 0;color:var(--muted)}
.doc img{max-width:100%}
.callout{margin:14px 0;padding:10px 14px;border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:8px;background:var(--panel)}
.callout .ct{font-weight:600;font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--accent);margin-bottom:4px}
.callout.warning,.callout.important{border-left-color:var(--warn)} .callout.warning .ct,.callout.important .ct{color:var(--warn)}
.callout.tip,.callout.note,.callout.abstract{border-left-color:var(--ok)} .callout.tip .ct,.callout.note .ct,.callout.abstract .ct{color:var(--ok)}
.mermaid{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px;overflow:auto;text-align:center}
/* Flujo animado: el trazo avanza del origen al destino y un "paquete" recorre cada conexión. */
.mermaid .flow{stroke-dasharray:7 5;animation:flow 1.1s linear infinite}
.mermaid .flow.dotted{stroke-dasharray:2 5}
@keyframes flow{to{stroke-dashoffset:-24}}
.mermaid .packet{fill:var(--accent);stroke:var(--bg);stroke-width:1.5;filter:drop-shadow(0 0 3px var(--accent))}
.flowctl{display:flex;justify-content:flex-end;gap:6px;margin:-4px 0 6px}
@media (prefers-reduced-motion: reduce){.mermaid .flow{animation:none}.mermaid .packet{display:none}}
body.noanim .mermaid .flow{animation:none} body.noanim .mermaid .packet{display:none}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin:-6px 0 18px;font-family:var(--mono);font-size:12px;color:var(--muted)}
.tag{background:var(--accent-soft);color:var(--accent);border-radius:4px;padding:1px 7px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:16px 0}
.card{border:1px solid var(--border);border-radius:10px;padding:14px;background:var(--panel)}
.card .k{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.card .v{font-size:26px;font-weight:700;margin-top:4px}
.bar{height:8px;background:var(--panel-2);border-radius:99px;overflow:hidden;margin-top:8px}
.bar i{display:block;height:100%;background:var(--accent)}
.wl-missing{color:var(--muted);border-bottom:1px dashed var(--muted)}
.mono{font-family:var(--mono);font-size:12.5px}
.s2{color:var(--ok)} .s4{color:var(--warn)} .s5{color:var(--err)}
.menu{display:none}
@media (max-width:860px){
  .layout{grid-template-columns:1fr}
  aside{position:fixed;inset:0 25% 0 0;z-index:10;transform:translateX(-100%);transition:transform .2s}
  aside.open{transform:none;box-shadow:0 0 40px rgba(0,0,0,.4)}
  main{padding:18px 16px 60px}
  .menu{display:inline-block}
}
</style>
</head>
<body>
<div class="layout">
  <aside id="nav">
    <div class="brand">AI Builders · Reto 2<b>Caja Negra · Docs</b></div>
    <input class="search" id="q" placeholder="Buscar en la documentación…" autocomplete="off">
    <div id="navlist"></div>
  </aside>
  <main>
    <div class="topbar">
      <span><button class="btn menu" id="menu">☰ Menú</button> <span class="pill"><span class="dot" id="livedot"></span><span id="genat"></span></span></span>
      <span><button class="btn on" id="anim" title="Animar el flujo de datos en los diagramas">⇢ Flujo</button> <button class="btn" id="lang-es">ES</button> <button class="btn" id="lang-en">EN</button> <button class="btn" id="theme">◐ Tema</button></span>
    </div>
    <article class="doc" id="content"></article>
  </main>
</div>
<!--DATA-->
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script type="module">
// Mermaid 11 + layout ELK: enrutado ortogonal que evita que las aristas crucen nodos o se superpongan.
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs';
import elkLayouts from 'https://cdn.jsdelivr.net/npm/@mermaid-js/layout-elk@0.1.7/dist/mermaid-layout-elk.esm.min.mjs';
mermaid.registerLayoutLoaders(elkLayouts);
window.mermaid = mermaid;
const D = JSON.parse(document.getElementById('data').textContent);
const VERSION = document.querySelector('meta[name=doc-version]').content;
let lang = 'es';
try { lang = localStorage.getItem('docs-lang') || 'es'; } catch (e) {}
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

// Índice de notas por título (para resolver [[wikilinks]] de Obsidian).
const byTitle = {};
D.docs.forEach(d => { byTitle[d.title.toLowerCase()] = d; byTitle[d.path.replace(/^docs\//,'').replace(/\.md$/,'').toLowerCase()] = d; });
const headingId = t => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^\w\s-]/g,'').trim().replace(/\s+/g,'-');

// Solo fuera de bloques de código: dentro de ```mermaid, `[[...]]` es sintaxis (nodo subrutina), no un enlace.
function wikilinks(md){
  return md.split(/(```[\s\S]*?```)/g).map((part, i) => i % 2 ? part : wikilinksText(part)).join('');
}
function wikilinksText(md){
  return md.replace(/!?\[\[([^\]|#]+)(#[^\]|]+)?(\|([^\]]+))?\]\]/g, (m, target, sec, _a, alias) => {
    const d = byTitle[target.trim().toLowerCase()];
    const label = alias || (target.split('/').pop() + (sec ? ' › ' + sec.slice(1) : ''));
    if (!d) return `<span class="wl-missing" title="Nota aún no creada">${esc(label)}</span>`;
    return `[${label}](#/doc/${d.id}${sec ? '~' + headingId(sec.slice(1)) : ''})`;
  });
}

const renderer = new marked.Renderer();
renderer.code = (code, info) => {
  if ((info || '').trim() === 'mermaid') return `<div class="mermaid">${esc(code)}</div>`;
  return `<pre><code>${esc(code)}</code></pre>`;
};
renderer.heading = (text, level, raw) => `<h${level} id="${headingId(raw)}">${text}</h${level}>`;
marked.setOptions({ renderer, gfm: true });

function callouts(root){
  root.querySelectorAll('blockquote').forEach(bq => {
    const p = bq.querySelector('p'); if (!p) return;
    const m = p.innerHTML.match(/^\[!(\w+)\][+-]?\s*([^<\n]*)/); if (!m) return;
    p.innerHTML = p.innerHTML.slice(m[0].length).replace(/^\s*<br>/, '');
    const div = document.createElement('div');
    div.className = 'callout ' + m[1].toLowerCase();
    div.innerHTML = `<div class="ct">${esc(m[2] || m[1])}</div>` + bq.innerHTML;
    bq.replaceWith(div);
  });
}

// Los enlaces relativos a archivos del repo apuntan a GitHub.
const REPO = 'https://github.com/jorgefajardom-coder/Ai-builders-Hackaton/blob/main/';
function fixLinks(root){
  root.querySelectorAll('a[href]').forEach(a => {
    const h = a.getAttribute('href');
    if (h.startsWith('#') && !h.startsWith('#/')) {
      a.addEventListener('click', e => { e.preventDefault(); document.getElementById(h.slice(1))?.scrollIntoView({behavior:'smooth'}); });
    } else if (!/^(https?:|#|mailto:)/.test(h)) {
      a.href = REPO + h.replace(/^\.\//, ''); a.target = '_blank';
    }
  });
}

const SVGNS = 'http://www.w3.org/2000/svg';
let packetSeq = 0;

// Convierte cada conexión en un flujo animado y le agrega un paquete que viaja origen → destino.
// El retraso de cada paquete sigue el orden de las aristas en el diagrama, así se lee la secuencia.
function animateFlows(root){
  root.querySelectorAll('.mermaid svg').forEach(svg => {
    const edges = [];
    svg.querySelectorAll('path.flowchart-link, .edgePaths path, .edgePath path.path').forEach(p => { if (!edges.includes(p)) edges.push(p); });
    // Diagramas de secuencia: los mensajes son <line> o <path>; se convierten a path para poder recorrerlos.
    svg.querySelectorAll('line[class*="messageLine"]').forEach(l => {
      const p = document.createElementNS(SVGNS, 'path');
      p.setAttribute('d', `M${l.getAttribute('x1')},${l.getAttribute('y1')} L${l.getAttribute('x2')},${l.getAttribute('y2')}`);
      p.setAttribute('fill', 'none'); p.setAttribute('stroke', 'none');
      l.parentNode.insertBefore(p, l.nextSibling);
      l.classList.add('flow'); if (l.classList.contains('messageLine1')) l.classList.add('dotted');
      edges.push(Object.assign(p, { _seq: true }));
    });
    svg.querySelectorAll('path[class*="messageLine"]').forEach(p => edges.push(p));
    edges.forEach((p, i) => {
      if (!p._seq) {
        p.classList.add('flow');
        const da = getComputedStyle(p).strokeDasharray;
        if (p.classList.contains('edge-pattern-dotted') || p.classList.contains('messageLine1') || (da && da !== 'none' && parseFloat(da) <= 3)) p.classList.add('dotted');
      }
      let len = 0; try { len = p.getTotalLength(); } catch (e) {}
      if (!len) return;
      if (!p.id) p.id = 'flowpath-' + (++packetSeq);
      const c = document.createElementNS(SVGNS, 'circle');
      c.setAttribute('r', '4'); c.setAttribute('class', 'packet');
      const m = document.createElementNS(SVGNS, 'animateMotion');
      const dur = Math.max(1.2, Math.min(4, len / 90));
      m.setAttribute('dur', dur.toFixed(2) + 's');
      m.setAttribute('begin', ((i * 0.35) % 4).toFixed(2) + 's');
      m.setAttribute('repeatCount', 'indefinite');
      m.setAttribute('rotate', 'auto');
      const mp = document.createElementNS(SVGNS, 'mpath');
      mp.setAttribute('href', '#' + p.id);
      m.appendChild(mp); c.appendChild(m);
      p.parentNode.appendChild(c);
    });
  });
}

// Verificador de diagramas: devuelve las aristas que atraviesan nodos ajenos, pisan títulos de grupo
// o etiquetas de otras aristas, o se cruzan entre sí. [] = diagramas limpios. Uso: checkOverlaps() en consola.
window.checkOverlaps = function(){
  const out = [];
  document.querySelectorAll('#content .mermaid svg').forEach((svg, d) => {
    const inv = svg.getCTM().inverse();
    const box = el => { const b = el.getBBox(), t = inv.multiply(el.getCTM());
      const p = new DOMPoint(b.x, b.y).matrixTransform(t), q = new DOMPoint(b.x + b.width, b.y + b.height).matrixTransform(t);
      return { x1: Math.min(p.x, q.x), y1: Math.min(p.y, q.y), x2: Math.max(p.x, q.x), y2: Math.max(p.y, q.y), el }; };
    const visible = sel => [...svg.querySelectorAll(sel)].filter(e => e.getBBox().width > 0).map(box);
    const nodes = visible('g.node'), titles = visible('g.cluster-label'), labels = visible('g.edgeLabel');
    const S = [...svg.querySelectorAll('path.flowchart-link')].map(p => {
      const L = p.getTotalLength(), m = inv.multiply(p.getCTM()), pts = [];
      for (let s = 0; s <= L; s += 3) { const q = p.getPointAtLength(s); pts.push(new DOMPoint(q.x, q.y).matrixTransform(m)); }
      return { id: p.id, pts };
    });
    const inside = (pt, r, pad) => pt.x > r.x1 + pad && pt.x < r.x2 - pad && pt.y > r.y1 + pad && pt.y < r.y2 - pad;
    const owner = labels.map(l => { const cx = (l.x1 + l.x2) / 2, cy = (l.y1 + l.y2) / 2; let best = null, bd = 1e9;
      S.forEach(s => s.pts.forEach(p => { const dd = Math.hypot(p.x - cx, p.y - cy); if (dd < bd) { bd = dd; best = s.id; } })); return best; });
    S.forEach(s => {
      const a = s.pts[0], b = s.pts[s.pts.length - 1];
      nodes.forEach(n => { if (!inside(a, n, -12) && !inside(b, n, -12) && s.pts.some(p => inside(p, n, 2))) out.push({ d, type: 'arista-atraviesa-nodo', edge: s.id, node: n.el.id }); });
      titles.forEach(t => { if (s.pts.some(p => inside(p, t, 0))) out.push({ d, type: 'arista-sobre-titulo', edge: s.id, title: t.el.textContent.slice(0, 40) }); });
      labels.forEach((l, k) => { if (owner[k] !== s.id && s.pts.some(p => inside(p, l, 1))) out.push({ d, type: 'arista-sobre-etiqueta-ajena', edge: s.id, label: l.el.textContent.slice(0, 40) }); });
    });
    for (let i = 0; i < S.length; i++) for (let j = i + 1; j < S.length; j++) {
      const A = S[i].pts, B = S[j].pts, ends = [A[0], A[A.length - 1], B[0], B[B.length - 1]];
      let hit = null;
      for (const p of A) { if (ends.some(e => Math.hypot(e.x - p.x, e.y - p.y) < 16)) continue;
        if (B.some(q => Math.hypot(p.x - q.x, p.y - q.y) < 2)) { hit = p; break; } }
      if (hit) out.push({ d, type: 'aristas-se-cruzan', a: S[i].id, b: S[j].id, at: [Math.round(hit.x), Math.round(hit.y)] });
    }
  });
  return out;
};

let renderToken = 0;
async function show(md, meta){
  const token = ++renderToken;
  const el = document.getElementById('content');
  el.innerHTML = (meta || '') + marked.parse(wikilinks(md));
  callouts(el); fixLinks(el);
  // Un diagrama a la vez; si el usuario navegó mientras se dibujaba, se abandona el render viejo.
  for (const node of el.querySelectorAll('.mermaid')) {
    if (token !== renderToken) return;
    try { await mermaid.run({ nodes: [node] }); } catch (e) { console.warn('mermaid', e); }
  }
  if (token === renderToken) animateFlows(el);
}

function viewHome(){
  show(D.readme[lang] || D.readme.es);
}

function viewDoc(id, anchor){
  const d = D.docs.find(x => x.id === id);
  if (!d) return show('# Nota no encontrada');
  const meta = `<div class="meta"><span>${esc(d.path)}</span><span>· editado ${esc(d.mtime)}</span>${d.tags.map(t => `<span class="tag">#${esc(t)}</span>`).join('')}</div>`;
  show(d.md, meta);
  if (anchor) setTimeout(() => document.getElementById(anchor)?.scrollIntoView(), 50);
}

function viewExp(){
  const E = D.exp;
  if (!E) return show('# Experimentos\n\nAún no hay `experimentos.jsonl`.');
  const pct = Math.min(100, E.total / E.budget * 100).toFixed(1);
  const statusCls = s => 's' + String(s)[0];
  let h = `<h1>Experimentos</h1>
  <p>Generado desde <code>experimentos.jsonl</code>: una línea por cada request al servicio original.</p>
  <div class="cards">
    <div class="card"><div class="k">Requests al original</div><div class="v">${E.total}</div><div class="bar"><i style="width:${pct}%"></i></div><div class="mono">${pct}% del cupo diario (${E.budget})</div></div>
    <div class="card"><div class="k">Secuencias</div><div class="v">${E.seqs.length}</div></div>
    <div class="card"><div class="k">Códigos de error vistos</div><div class="v">${E.errors.length}</div></div>
    <div class="card"><div class="k">Status HTTP</div><div class="v mono" style="font-size:15px">${Object.entries(E.status).map(([s,n]) => `<span class="${statusCls(s)}">${s}</span>×${n}`).join(' · ')}</div></div>
  </div>
  <h2>Catálogo de errores observado</h2>
  <table><thead><tr><th>Código</th><th>Status</th><th>Mensaje exacto</th><th>Veces</th><th>Primera evidencia</th></tr></thead><tbody>
  ${E.errors.map(e => `<tr><td class="mono">${esc(e.code)}</td><td class="mono ${statusCls(e.status)}">${e.status}</td><td class="mono">"${esc(e.mensaje)}"</td><td>${e.count}</td><td class="mono">#${e.first}</td></tr>`).join('')}
  </tbody></table>
  <h2>Secuencias</h2>
  <table><thead><tr><th>Seq</th><th>Requests</th><th>Ids</th><th>Hipótesis inicial</th></tr></thead><tbody>
  ${E.seqs.map(s => `<tr><td class="mono">${esc(s.seq)}</td><td>${s.n}</td><td class="mono">#${s.first}–#${s.last}</td><td>${esc(s.hipotesis)}</td></tr>`).join('')}
  </tbody></table>
  <h2>Log (sin el ruido de los barridos)</h2>
  <input class="search" id="expq" placeholder="Filtrar por id, seq, mensaje, error…">
  <table id="exptable"><thead><tr><th>#</th><th>Seq</th><th>Request</th><th>Status</th><th>Respuesta</th><th>Hipótesis</th></tr></thead><tbody>
  ${E.notable.slice().reverse().map(r => `<tr><td class="mono">${r.id}</td><td class="mono">${esc(r.seq)}</td><td class="mono">${esc((r.metodo||'') + ' ' + (r.ruta||''))}<br>${esc(typeof r.request === 'object' && r.request ? JSON.stringify(r.request) : (r.request ?? ''))}</td><td class="mono ${statusCls(r.status)}">${r.status}</td><td class="mono">${esc(typeof r.response === 'object' ? JSON.stringify(r.response) : r.response)}</td><td>${esc(r.hipotesis)}${r.conclusion ? '<br><b>→ ' + esc(r.conclusion) + '</b>' : ''}</td></tr>`).join('')}
  </tbody></table>`;
  const el = document.getElementById('content'); el.innerHTML = h;
  document.getElementById('expq').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('#exptable tbody tr').forEach(tr => tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none');
  });
}

function viewHistory(){
  show('# Historial\n\nCommits del repositorio (más recientes primero). Cada commit regenera esta documentación.\n\n| Commit | Fecha | Mensaje |\n|---|---|---|\n' +
    D.commits.map(c => `| [\`${c.hash}\`](https://github.com/jorgefajardom-coder/Ai-builders-Hackaton/commit/${c.hash}) | ${c.date} | ${c.msg.replace(/\|/g,'\\|')} |`).join('\n'));
}

function viewMaterial(){ show(D.material || '# Material\n\nNo disponible.'); }

function buildNav(filter){
  const q = (filter || '').toLowerCase();
  const match = d => !q || d.title.toLowerCase().includes(q) || d.md.toLowerCase().includes(q);
  const groups = {};
  D.docs.filter(match).forEach(d => (groups[d.group] = groups[d.group] || []).push(d));
  let h = `<div class="navgroup"><h4>Proyecto</h4>
    <a href="#/" data-r="#/">Documento de diseño (README)</a>
    <a href="#/exp" data-r="#/exp">Experimentos · ${D.exp ? D.exp.total : 0}</a>
    <a href="#/material" data-r="#/material">Material del reto</a>
    <a href="#/historial" data-r="#/historial">Historial · ${D.commits.length} commits</a></div>`;
  Object.keys(groups).sort((a,b) => a === 'General' ? -1 : b === 'General' ? 1 : a.localeCompare(b)).forEach(g => {
    h += `<div class="navgroup"><h4>${esc(g)}</h4>` + groups[g].map(d => `<a href="#/doc/${d.id}" data-r="#/doc/${d.id}">${esc(d.title)}</a>`).join('') + '</div>';
  });
  document.getElementById('navlist').innerHTML = h;
  markActive();
}

function markActive(){
  let r = location.hash.split('~')[0] || '#/';
  try { r = decodeURIComponent(r); } catch (e) {}
  document.querySelectorAll('#navlist a').forEach(a => a.classList.toggle('active', a.dataset.r === r));
}

function route(){
  let h = location.hash || '#/';
  try { h = decodeURIComponent(h); } catch (e) {}
  const [path, anchor] = h.slice(1).split('~');
  if (path.startsWith('/doc/')) viewDoc(path.slice(5), anchor);
  else if (path === '/exp') viewExp();
  else if (path === '/historial') viewHistory();
  else if (path === '/material') viewMaterial();
  else viewHome();
  markActive();
  document.getElementById('nav').classList.remove('open');
  if (!anchor) window.scrollTo(0, 0);
}

function setLang(l, render = true){
  lang = l; try { localStorage.setItem('docs-lang', l); } catch (e) {}
  document.getElementById('lang-es').classList.toggle('on', l === 'es');
  document.getElementById('lang-en').classList.toggle('on', l === 'en');
  if (render && (location.hash || '#/') === '#/') viewHome();
}

function initTheme(){
  const dark = () => document.documentElement.dataset.theme ? document.documentElement.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
  try { const t = localStorage.getItem('docs-theme'); if (t) document.documentElement.dataset.theme = t; } catch (e) {}
  const apply = () => mermaid.initialize({
    startOnLoad: false, theme: dark() ? 'dark' : 'default', securityLevel: 'strict',
    layout: 'elk', look: 'classic',
    elk: { mergeEdges: false, nodePlacementStrategy: 'NETWORK_SIMPLEX', cycleBreakingStrategy: 'GREEDY' },
    flowchart: { curve: 'linear', padding: 14, nodeSpacing: 40, rankSpacing: 60, htmlLabels: true },
    sequence: { mirrorActors: false, messageMargin: 34 },
  });
  apply();
  document.getElementById('theme').onclick = () => {
    const t = dark() ? 'light' : 'dark';
    document.documentElement.dataset.theme = t;
    try { localStorage.setItem('docs-theme', t); } catch (e) {}
    apply(); route();
  };
}

// Recarga automática: si el sitio se sirve por HTTP y hay una versión nueva, recarga la página.
function liveReload(){
  const dot = document.getElementById('livedot');
  if (!/^https?:/.test(location.protocol)) { dot.style.background = 'var(--muted)'; dot.title = 'Abierto como archivo: sin recarga automática'; return; }
  if (new URLSearchParams(location.search).has('nolive')) { dot.style.background = 'var(--warn)'; dot.title = 'Recarga automática pausada (?nolive)'; return; }
  dot.title = 'Recarga automática activa';
  setInterval(async () => {
    try {
      const r = await fetch('version.json?t=' + Date.now(), { cache: 'no-store' });
      if (!r.ok) return;
      const v = await r.json();
      if (v.version && v.version !== VERSION) location.reload();
    } catch (e) {}
  }, 10000);
}

document.getElementById('genat').textContent = 'Actualizado ' + D.generated + ' · v' + VERSION;
document.getElementById('q').addEventListener('input', e => buildNav(e.target.value));
document.getElementById('lang-es').onclick = () => setLang('es');
document.getElementById('lang-en').onclick = () => setLang('en');
document.getElementById('menu').onclick = () => document.getElementById('nav').classList.toggle('open');
document.getElementById('anim').onclick = e => { const off = document.body.classList.toggle('noanim'); e.currentTarget.classList.toggle('on', !off); };
window.addEventListener('hashchange', route);
initTheme(); setLang(lang, false); buildNav(); route(); liveReload();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
