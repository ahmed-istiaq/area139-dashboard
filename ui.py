"""UI building blocks for the Area 139 dashboard: CSS + HTML snippets.
No Streamlit import here, so everything is easy to test on its own.
"""
import html
import re
from math import hypot

# (hex, "r,g,b") - amber is the brand colour of the Area 139 site
PALETTE = [
    ("#fbbf24", "251,191,36"),   # amber
    ("#38bdf8", "56,189,248"),   # sky
    ("#a78bfa", "167,139,250"),  # violet
    ("#34d399", "52,211,153"),   # emerald
    ("#fb7185", "251,113,133"),  # rose
    ("#fb923c", "251,146,60"),   # orange
    ("#2dd4bf", "45,212,191"),   # teal
    ("#f472b6", "244,114,182"),  # pink
]
AMBER, SKY, VIOLET, EMERALD, ROSE = (PALETTE[i][1] for i in (0, 1, 2, 3, 4))
MEDAL_RGB = ["251,191,36", "203,213,225", "251,146,60"]


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def _c(s: str) -> str:
    """Collapse to one line: Streamlit's markdown turns indented/blank-line HTML into code."""
    return re.sub(r"\s*\n\s*", " ", s.strip())


def cat_palette(categories) -> dict:
    """Stable category -> (hex, rgb) mapping (same colours in HTML and in charts)."""
    return {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(sorted(set(categories)))}


# ------------------------------------------------------------------ CSS
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root{--amber:#fbbf24;--text:#e5e7eb;--muted:#94a3b8;--line:rgba(255,255,255,.08)}

/* ---------- page ---------- */
.stApp{font-family:'Plus Jakarta Sans',system-ui,sans-serif;color:var(--text);
 background:
  radial-gradient(900px 520px at 6% -8%,rgba(251,191,36,.14),transparent 60%),
  radial-gradient(820px 520px at 100% 0%,rgba(167,139,250,.13),transparent 60%),
  radial-gradient(900px 600px at 50% 125%,rgba(56,189,248,.10),transparent 60%),
  #030712 !important;background-attachment:fixed !important}
.stApp::before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.5;z-index:0;
 background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
 background-size:46px 46px;mask-image:radial-gradient(ellipse at 50% 0%,#000 25%,transparent 75%);-webkit-mask-image:radial-gradient(ellipse at 50% 0%,#000 25%,transparent 75%)}
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{visibility:hidden;height:0}
[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:1.2rem;padding-bottom:3rem;max-width:1380px;position:relative;z-index:1}
.stApp h1,.stApp h2,.stApp h3,.stApp h4{font-family:'Space Grotesk','Plus Jakarta Sans',sans-serif;letter-spacing:-.01em}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:10px}
::-webkit-scrollbar-thumb:hover{background:rgba(251,191,36,.4)}

/* ---------- animations ---------- */
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes grow{from{width:0}}
@keyframes draw{to{stroke-dashoffset:0}}
@keyframes fade{from{opacity:0}}
@keyframes ring{from{stroke-dashoffset:var(--C)}}
@keyframes shimmer{to{background-position:200% center}}
@keyframes sheen{0%,55%{transform:translateX(-110%)}100%{transform:translateX(110%)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(52,211,153,.6)}70%{box-shadow:0 0 0 9px rgba(52,211,153,0)}100%{box-shadow:0 0 0 0 rgba(52,211,153,0)}}
@keyframes ecg{from{stroke-dashoffset:110}to{stroke-dashoffset:-760}}

/* ---------- hero ---------- */
.a-hero{position:relative;overflow:hidden;border-radius:28px;padding:30px 34px 28px;margin-bottom:22px;
 border:1px solid rgba(251,191,36,.22);
 background:linear-gradient(135deg,rgba(251,191,36,.11),rgba(167,139,250,.07) 45%,rgba(56,189,248,.07)),rgba(8,12,24,.72);
 box-shadow:0 30px 80px -40px rgba(251,191,36,.4),inset 0 1px 0 rgba(255,255,255,.06);animation:rise .7s both}
.a-hero::after{content:"";position:absolute;inset:0;pointer-events:none;
 background:linear-gradient(110deg,transparent 35%,rgba(255,255,255,.07) 50%,transparent 65%);animation:sheen 7s ease-in-out infinite}
.a-orb{position:absolute;border-radius:50%;filter:blur(55px);animation:float 9s ease-in-out infinite;pointer-events:none}
.a-orb.o1{width:230px;height:230px;background:#fbbf24;right:-60px;top:-100px;opacity:.26}
.a-orb.o2{width:210px;height:210px;background:#7c3aed;right:200px;bottom:-130px;opacity:.24;animation-delay:-4s}
.a-hero-in{position:relative;z-index:2}
.a-brand{display:flex;align-items:center;gap:16px}
.a-logo{width:56px;height:56px;border-radius:18px;display:grid;place-items:center;font-size:28px;font-weight:800;color:#1c1303;
 background:linear-gradient(135deg,#fde68a,#fbbf24 50%,#fb923c);box-shadow:0 10px 30px -8px rgba(251,191,36,.7);animation:float 5s ease-in-out infinite}
.a-eyebrow{font:600 11.5px 'JetBrains Mono',monospace;letter-spacing:.22em;color:#fcd34d;opacity:.85}
.a-title{margin:2px 0 0;font:700 clamp(30px,4.2vw,48px)/1.05 'Space Grotesk',sans-serif;letter-spacing:-.02em;
 background:linear-gradient(90deg,#fde68a,#fbbf24 30%,#fb923c 55%,#fde68a 85%);background-size:200% auto;
 -webkit-background-clip:text;background-clip:text;color:transparent;animation:shimmer 7s linear infinite}
.a-greet{margin:16px 0 14px;font-size:16px;color:#cbd5e1}
.a-greet b{color:#fff}
.a-chips{display:flex;flex-wrap:wrap;gap:8px}
.a-chip{display:inline-flex;align-items:center;gap:8px;padding:6px 13px;border-radius:999px;background:rgba(255,255,255,.06);
 border:1px solid var(--line);font:500 12px 'JetBrains Mono',monospace;color:#cbd5e1;backdrop-filter:blur(8px);transition:.2s}
.a-chip:hover{transform:translateY(-2px);border-color:rgba(251,191,36,.45)}
.a-chip.ok{border-color:rgba(52,211,153,.35);color:#6ee7b7;background:rgba(52,211,153,.08)}
.a-chip.warn{border-color:rgba(251,191,36,.4);color:#fcd34d;background:rgba(251,191,36,.08)}
.a-chip.bad{border-color:rgba(251,113,133,.4);color:#fda4af;background:rgba(251,113,133,.08)}
.a-dot{width:8px;height:8px;border-radius:50%;background:#34d399;animation:pulse 2s infinite}
.a-ecg{position:absolute;right:26px;bottom:14px;width:46%;max-width:540px;height:74px;pointer-events:none;z-index:1;
 -webkit-mask-image:linear-gradient(90deg,transparent,#000 35%);mask-image:linear-gradient(90deg,transparent,#000 35%)}
.a-ecg path{fill:none;stroke:#fbbf24;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.a-ecg .e0{opacity:.16}
.a-ecg .e1{stroke-dasharray:110 900;animation:ecg 3.4s linear infinite;filter:drop-shadow(0 0 5px #fbbf24)}

/* ---------- KPI cards ---------- */
.a-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(235px,1fr));gap:16px;margin-bottom:10px}
.a-kpi{--rgb:251,191,36;position:relative;overflow:hidden;padding:18px 20px 16px;min-height:150px;border-radius:22px;
 border:1px solid var(--line);background:linear-gradient(160deg,rgba(255,255,255,.075),rgba(255,255,255,.02));
 backdrop-filter:blur(12px);animation:rise .65s cubic-bezier(.2,.8,.2,1) both;animation-delay:calc(var(--i,0)*90ms);
 transition:transform .25s,border-color .25s,box-shadow .25s}
.a-kpi::before{content:"";position:absolute;width:160px;height:160px;border-radius:50%;background:rgb(var(--rgb));
 filter:blur(62px);opacity:.15;right:-40px;top:-70px;transition:opacity .3s}
.a-kpi:hover{transform:translateY(-6px);border-color:rgba(var(--rgb),.55);box-shadow:0 24px 46px -24px rgba(var(--rgb),.9)}
.a-kpi:hover::before{opacity:.34}
.a-kpi-top{display:flex;justify-content:space-between;align-items:center;position:relative;z-index:1}
.a-kpi-l{font:600 11px 'JetBrains Mono',monospace;letter-spacing:.15em;text-transform:uppercase;color:#94a3b8}
.a-ico{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;font-size:18px;
 background:rgba(var(--rgb),.14);border:1px solid rgba(var(--rgb),.3)}
.a-kpi-v{position:relative;z-index:1;margin:12px 0 4px;font:700 38px/1.1 'Space Grotesk',sans-serif;letter-spacing:-.02em;
 background:linear-gradient(180deg,#fff 10%,rgb(var(--rgb)));-webkit-background-clip:text;background-clip:text;color:transparent;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.a-kpi-v.sm{font-size:27px;padding-top:6px;padding-bottom:6px}
.a-kpi-s{position:relative;z-index:1;font-size:12.5px;color:#94a3b8;max-width:60%}
.a-delta{display:inline-block;padding:2px 9px;border-radius:999px;font:600 11.5px 'JetBrains Mono',monospace;margin-right:6px;
 background:rgba(var(--rgb),.14);color:rgb(var(--rgb))}
.a-spark{position:absolute;right:14px;bottom:12px;width:150px;height:44px;opacity:.95}
.a-spark .sa{fill:rgba(var(--rgb),.15);stroke:none;animation:fade 1.2s .6s both}
.a-spark .sl{fill:none;stroke:rgb(var(--rgb));stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round;
 stroke-dasharray:var(--L);stroke-dashoffset:var(--L);animation:draw 1.6s .3s ease forwards}
@media(max-width:600px){.a-spark{display:none}.a-kpi-s{max-width:100%}}

/* ---------- sections / panels ---------- */
.a-sec{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin:34px 0 14px;animation:rise .6s both}
.a-kicker{font:600 11px 'JetBrains Mono',monospace;letter-spacing:.2em;color:#fbbf24;text-transform:uppercase;margin-bottom:4px}
.a-sec h3{margin:0;font:700 24px 'Space Grotesk',sans-serif;color:#f8fafc}
.a-sec p{margin:0;color:#94a3b8;font-size:13.5px;max-width:420px;text-align:right}
.a-panel{border-radius:22px;border:1px solid var(--line);background:linear-gradient(160deg,rgba(255,255,255,.05),rgba(255,255,255,.015));padding:10px;backdrop-filter:blur(10px)}
@media(max-width:700px){.a-sec{flex-direction:column;align-items:flex-start}.a-sec p{text-align:left}}

/* ---------- podium ---------- */
.a-podium{display:grid;grid-template-columns:1fr 1.14fr 1fr;gap:16px;align-items:end;margin-bottom:14px}
.a-pod{position:relative;overflow:hidden;padding:20px 18px 18px;border-radius:24px;border:1px solid rgba(var(--rgb),.3);text-align:center;
 background:linear-gradient(170deg,rgba(var(--rgb),.17),rgba(255,255,255,.02) 62%);animation:rise .7s both;animation-delay:calc(var(--i)*130ms);
 transition:transform .25s,box-shadow .25s}
.a-pod:hover{transform:translateY(-7px);box-shadow:0 28px 52px -26px rgba(var(--rgb),.95)}
.a-pod.p1{padding-top:32px;padding-bottom:26px;border-color:rgba(251,191,36,.55);box-shadow:0 20px 60px -30px rgba(251,191,36,.7)}
.a-medal{display:block;font-size:38px;animation:float 4s ease-in-out infinite}
.a-pod.p1 .a-medal{font-size:50px}
.a-pod h4{margin:8px 0 8px;font:700 15px/1.35 'Plus Jakarta Sans',sans-serif;color:#f8fafc;min-height:2.7em;
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.a-pod .num{margin-top:10px;font:700 36px 'Space Grotesk',sans-serif;color:rgb(var(--rgb))}
.a-pod.p1 .num{font-size:42px}
.a-pod .share{font:500 11.5px 'JetBrains Mono',monospace;color:#94a3b8}
@media(max-width:760px){.a-podium{grid-template-columns:1fr}}

/* ---------- ranked rows ---------- */
.a-rank{display:grid;grid-template-columns:34px minmax(0,1.6fr) minmax(80px,1.2fr) 74px;align-items:center;gap:14px;padding:11px 14px;
 border-radius:14px;border:1px solid transparent;transition:.2s;animation:rise .5s both;animation-delay:calc(var(--i)*45ms)}
.a-rank:hover{background:rgba(255,255,255,.055);border-color:var(--line);transform:translateX(5px)}
.a-rank .n{font:600 12px 'JetBrains Mono',monospace;color:#64748b}
.a-rank .t{min-width:0}
.a-rank .t b{display:block;font-weight:600;font-size:14px;color:#f1f5f9;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.a-badge{display:inline-block;margin-top:3px;padding:1px 9px;border-radius:999px;font:600 10.5px 'JetBrains Mono',monospace;
 background:rgba(var(--rgb),.14);color:rgb(var(--rgb));border:1px solid rgba(var(--rgb),.3)}
.a-track{height:8px;border-radius:99px;background:rgba(255,255,255,.07);overflow:hidden}
.a-track i{display:block;height:100%;width:var(--w);border-radius:99px;background:linear-gradient(90deg,rgba(var(--rgb),.5),rgb(var(--rgb)));
 box-shadow:0 0 12px rgba(var(--rgb),.6);animation:grow 1.2s cubic-bezier(.2,.8,.2,1) both;animation-delay:calc(var(--i)*45ms + .2s)}
.a-rank .v{text-align:right;font:700 15px 'Space Grotesk',sans-serif;color:#f8fafc}
@media(max-width:760px){.a-rank{grid-template-columns:26px 1fr 60px}.a-rank .a-track{display:none}}

/* ---------- pills / misc ---------- */
.a-pill{display:inline-block;margin:4px 3px;padding:6px 13px;border-radius:999px;background:rgba(255,255,255,.05);border:1px solid var(--line);
 font-size:12.5px;color:#cbd5e1;transition:.2s;animation:rise .5s both;animation-delay:calc(var(--i)*25ms)}
.a-pill:hover{border-color:rgba(251,191,36,.5);color:#fde68a;transform:translateY(-2px);background:rgba(251,191,36,.08)}
.a-note{padding:12px 16px;border-radius:14px;background:rgba(56,189,248,.07);border:1px solid rgba(56,189,248,.22);color:#bae6fd;font-size:13px}
.a-empty{padding:34px 28px;border-radius:26px;border:1px dashed rgba(251,191,36,.38);text-align:center;
 background:radial-gradient(500px 220px at 50% 0%,rgba(251,191,36,.10),transparent 70%),rgba(255,255,255,.02);animation:rise .6s both}
.a-empty .big{font-size:46px;display:block;animation:float 4s ease-in-out infinite}
.a-empty h3{margin:8px 0 6px;font:700 26px 'Space Grotesk',sans-serif;color:#fde68a}
.a-empty p{margin:0 auto 22px;max-width:520px;color:#94a3b8}
.a-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;text-align:left}
.a-step{padding:14px 16px;border-radius:16px;background:rgba(255,255,255,.04);border:1px solid var(--line);transition:.2s}
.a-step:hover{border-color:rgba(251,191,36,.45);transform:translateY(-3px)}
.a-step i{display:inline-grid;place-items:center;width:26px;height:26px;border-radius:50%;margin-bottom:8px;font:700 12px 'JetBrains Mono',monospace;
 font-style:normal;color:#1c1303;background:linear-gradient(135deg,#fde68a,#fbbf24)}
.a-step b{display:block;color:#f8fafc;font-size:14px;margin-bottom:2px}
.a-step span{font-size:12.5px;color:#94a3b8}

/* ---------- link health ---------- */
.a-health{display:flex;gap:30px;align-items:center;flex-wrap:wrap;padding:24px 28px;border-radius:26px;border:1px solid var(--line);
 background:linear-gradient(160deg,rgba(255,255,255,.06),rgba(255,255,255,.015));animation:rise .6s both}
.a-ring{position:relative;width:172px;height:172px;flex:none}
.a-ring svg{width:100%;height:100%}
.a-ring .rb{fill:none;stroke:rgba(255,255,255,.08);stroke-width:12}
.a-ring .rf{fill:none;stroke:rgb(var(--rgb));stroke-width:12;stroke-linecap:round;stroke-dasharray:var(--C);stroke-dashoffset:var(--off);
 animation:ring 1.7s cubic-bezier(.2,.8,.2,1) both;filter:drop-shadow(0 0 8px rgba(var(--rgb),.75))}
.a-ring-c{position:absolute;inset:0;display:grid;place-content:center;text-align:center}
.a-ring-c b{font:700 38px 'Space Grotesk',sans-serif;color:#fff}
.a-ring-c span{font:500 11px 'JetBrains Mono',monospace;color:#94a3b8;letter-spacing:.1em;text-transform:uppercase}
.a-minis{flex:1;min-width:280px;display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px}
.a-mini{padding:14px 16px;border-radius:18px;background:rgba(var(--rgb),.08);border:1px solid rgba(var(--rgb),.24);transition:.2s}
.a-mini:hover{transform:translateY(-4px);background:rgba(var(--rgb),.14)}
.a-mini b{display:block;font:700 30px 'Space Grotesk',sans-serif;color:rgb(var(--rgb))}
.a-mini>span{font:600 10.5px 'JetBrains Mono',monospace;letter-spacing:.14em;color:#94a3b8;text-transform:uppercase}
.a-issue{--rgb:251,113,133;display:grid;grid-template-columns:86px minmax(0,1fr);gap:14px;align-items:start;padding:14px 16px;margin-bottom:10px;
 border-radius:16px;background:rgba(255,255,255,.035);border:1px solid var(--line);border-left:3px solid rgb(var(--rgb));
 animation:rise .5s both;animation-delay:calc(var(--i)*50ms);transition:.2s}
.a-issue:hover{background:rgba(255,255,255,.06);transform:translateX(4px)}
.a-issue .st{padding:3px 0;text-align:center;border-radius:999px;font:700 10.5px 'JetBrains Mono',monospace;letter-spacing:.1em;
 color:rgb(var(--rgb));background:rgba(var(--rgb),.14);border:1px solid rgba(var(--rgb),.3)}
.a-issue a{color:#fcd34d;text-decoration:none;word-break:break-all;font-size:13.5px}
.a-issue a:hover{text-decoration:underline}
.a-issue p{margin:4px 0 0;color:#94a3b8;font-size:12.5px}

.a-where{margin-top:12px;padding:11px 13px;border-radius:14px;background:rgba(251,191,36,.05);border:1px dashed rgba(251,191,36,.28)}
.a-where-h{font:600 10.5px 'JetBrains Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#fbbf24}
.a-loc{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:8px}
.a-loc+.a-loc{padding-top:8px;border-top:1px solid rgba(255,255,255,.06)}
.a-crumb{padding:3px 10px;border-radius:8px;background:rgba(255,255,255,.07);border:1px solid var(--line);font-size:12px;color:#e2e8f0}
.a-crumb.btn{background:rgba(251,191,36,.14);border-color:rgba(251,191,36,.35);color:#fde68a}
.a-loc i{font-style:normal;color:#64748b}
.a-tag{padding:2px 9px;border-radius:999px;font:600 10px 'JetBrains Mono',monospace;letter-spacing:.08em;text-transform:uppercase;
 color:#7dd3fc;background:rgba(56,189,248,.1);border:1px solid rgba(56,189,248,.3)}
.a-where a.a-open{margin-left:auto;padding:3px 11px;border-radius:999px;font:600 11.5px 'Plus Jakarta Sans',sans-serif;color:#fde68a;
 background:rgba(251,191,36,.1);border:1px solid rgba(251,191,36,.35);text-decoration:none;transition:.2s;white-space:nowrap}
.a-where a.a-open:hover{background:rgba(251,191,36,.25);transform:translateY(-1px);text-decoration:none}
.a-mt{margin:6px 2px 10px;font:600 11px 'JetBrains Mono',monospace;letter-spacing:.16em;text-transform:uppercase;color:#94a3b8}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a0f1e,#050816) !important;border-right:1px solid rgba(255,255,255,.06)}
.a-sbrand{display:flex;align-items:center;gap:12px;padding:6px 2px 16px;margin-bottom:6px;border-bottom:1px solid var(--line)}
.a-sbrand .a-logo{width:42px;height:42px;font-size:21px;border-radius:14px}
.a-sbrand b{display:block;font:700 17px 'Space Grotesk',sans-serif;color:#f8fafc}
.a-sbrand span{font:500 10.5px 'JetBrains Mono',monospace;letter-spacing:.14em;color:#94a3b8}
.a-side-h{margin:18px 0 6px;font:600 11px 'JetBrains Mono',monospace;letter-spacing:.2em;color:#fbbf24;text-transform:uppercase}
.a-foot{margin-top:46px;padding-top:18px;border-top:1px solid var(--line);text-align:center;color:#64748b;font:500 12px 'JetBrains Mono',monospace}
.a-foot b{color:#fbbf24}

/* ---------- native widgets ---------- */
.stTabs [data-baseweb="tab-list"]{gap:6px;padding:6px;width:fit-content;max-width:100%;overflow-x:auto;border-radius:16px;background:rgba(255,255,255,.04);border:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{height:42px;padding:0 20px;border-radius:11px;color:#94a3b8;font-weight:600;transition:.2s;background:transparent}
.stTabs [data-baseweb="tab"]:hover{color:#fde68a;background:rgba(255,255,255,.05)}
.stTabs [aria-selected="true"]{color:#fde68a !important;background:linear-gradient(135deg,rgba(251,191,36,.2),rgba(251,146,60,.1)) !important;box-shadow:inset 0 0 0 1px rgba(251,191,36,.38),0 8px 24px -12px rgba(251,191,36,.6)}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none}
.stTabs [data-baseweb="tab-panel"]{padding-top:6px}
.stButton>button,.stDownloadButton>button{border-radius:12px;border:1px solid rgba(251,191,36,.38);font-weight:700;color:#fde68a;transition:.22s;
 background:linear-gradient(135deg,rgba(251,191,36,.16),rgba(251,146,60,.07))}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-2px);border-color:#fbbf24;color:#fff;box-shadow:0 12px 28px -14px rgba(251,191,36,.9)}
[data-testid="stDataFrame"]{border-radius:16px;overflow:hidden;border:1px solid var(--line)}
[data-testid="stPlotlyChart"]{border-radius:22px;border:1px solid var(--line);padding:8px 6px 2px;transition:.25s;
 background:linear-gradient(160deg,rgba(255,255,255,.05),rgba(255,255,255,.012))}
[data-testid="stPlotlyChart"]:hover{border-color:rgba(251,191,36,.28);box-shadow:0 22px 50px -32px rgba(251,191,36,.7)}
[data-testid="stExpander"]{border-radius:16px;border:1px solid var(--line);background:rgba(255,255,255,.025)}
[data-testid="stTextInput"] input,[data-baseweb="select"]>div{border-radius:12px}
/* pill-style horizontal radios (inside st.container(key="pill_*")) */
[class*="st-key-pill"] div[role="radiogroup"]{gap:8px;flex-wrap:wrap}
[class*="st-key-pill"] div[role="radiogroup"]>label{margin:0;padding:7px 16px;border-radius:999px;cursor:pointer;transition:.2s;
 background:rgba(255,255,255,.05);border:1px solid var(--line)}
[class*="st-key-pill"] div[role="radiogroup"]>label:hover{border-color:rgba(251,191,36,.5);transform:translateY(-2px)}
[class*="st-key-pill"] div[role="radiogroup"]>label>div:first-child{display:none}
[class*="st-key-pill"] div[role="radiogroup"]>label:has(input:checked){background:linear-gradient(135deg,rgba(251,191,36,.25),rgba(251,146,60,.12));
 border-color:rgba(251,191,36,.6);box-shadow:0 8px 22px -12px rgba(251,191,36,.9)}
[class*="st-key-pill"] div[role="radiogroup"]>label:has(input:checked) p{color:#fde68a;font-weight:700}
"""


def _counter_css() -> str:
    """Count-up animation for integers (pure CSS: @property + counters). 4 digit-groups max."""
    out = ["@counter-style three{system:numeric;symbols:'0' '1' '2' '3' '4' '5' '6' '7' '8' '9';pad:3 '0'}",
           ".cu{display:inline-flex;align-items:baseline}.cu .cs{padding:0 1px}"]
    for k in range(4):
        out.append(f"@property --k{k}{{syntax:'<integer>';initial-value:0;inherits:false}}")
        out.append(f"@keyframes cu{k}{{from{{--k{k}:0}}}}")
        out.append(f".cg.k{k}{{animation:cu{k} 1.8s cubic-bezier(.16,.84,.3,1) both;counter-reset:c{k} var(--k{k})}}")
        out.append(f".cg.k{k}::after{{content:counter(c{k},three)}}")
        out.append(f".cg.k{k}.lead::after{{content:counter(c{k})}}")
    return "".join(out)


def css() -> str:
    return "<style>" + _c(_CSS) + _counter_css() + "</style>"


# ------------------------------------------------------------------ small pieces
def count_html(n) -> str:
    """Integer with thousands separators that counts up from 0 on load."""
    n = max(int(n), 0)
    groups = f"{n:,}".split(",")
    parts = []
    for idx, g in enumerate(groups):
        k = len(groups) - 1 - idx
        if k > 3:  # absurdly large - just show it
            return f'<span class="cu">{n:,}</span>'
        lead = " lead" if idx == 0 else ""
        parts.append(f'<span class="cg k{k}{lead}" style="--k{k}:{int(g)}"></span>')
        if idx < len(groups) - 1:
            parts.append('<span class="cs">,</span>')
    return f'<span class="cu">{"".join(parts)}</span>'


def chip(text, kind="", dot=False) -> str:
    d = '<i class="a-dot"></i>' if dot else ""
    return f'<span class="a-chip {kind}">{d}{esc(text)}</span>'


def spark_svg(values, w=150, h=44, pad=3) -> str:
    vals = [float(v) for v in values]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    step = (w - 2 * pad) / (len(vals) - 1)
    pts = [(pad + i * step, h - pad - (v - lo) / rng * (h - 2 * pad)) for i, v in enumerate(vals)]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    length = sum(hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    area = f"{d} L{pts[-1][0]:.1f},{h} L{pts[0][0]:.1f},{h} Z"
    return (f'<svg class="a-spark" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
            f'<path class="sa" d="{area}"/><path class="sl" d="{d}" style="--L:{length + 2:.0f}"/></svg>')


_ECG = ("M0,40 L110,40 L122,32 L134,40 L190,40 L200,40 L210,8 L222,66 L234,22 L242,40 "
        "L300,40 L316,30 L332,40 L400,40 L410,36 L420,40 L520,40")


def hero(greeting: str, summary: str, chips: list) -> str:
    chips_html = "".join(chip(t, k, dot) for t, k, dot in chips)
    return _c(f"""
<div class="a-hero"><div class="a-orb o1"></div><div class="a-orb o2"></div>
<svg class="a-ecg" viewBox="0 0 520 74" xmlns="http://www.w3.org/2000/svg"><path class="e0" d="{_ECG}"/><path class="e1" d="{_ECG}"/></svg>
<div class="a-hero-in">
<div class="a-brand"><div class="a-logo">✚</div><div><div class="a-eyebrow">AREA 139 · MEDINOTE</div><h1 class="a-title">Command Center</h1></div></div>
<p class="a-greet">{esc(greeting)} <b>Istiaq</b> 👋 &nbsp;{esc(summary)}</p>
<div class="a-chips">{chips_html}</div></div></div>""")


def kpi_card(label, value_html, sub_html, icon, rgb, idx=0, spark=None, small=False) -> str:
    sp = spark_svg(spark) if spark else ""
    cls = "a-kpi-v sm" if small else "a-kpi-v"
    return (f'<div class="a-kpi" style="--rgb:{rgb};--i:{idx}"><div class="a-kpi-top"><span class="a-kpi-l">{esc(label)}</span>'
            f'<span class="a-ico">{icon}</span></div><div class="{cls}">{value_html}</div>'
            f'<div class="a-kpi-s">{sub_html}</div>{sp}</div>')


def kpi_grid(cards: list) -> str:
    return f'<div class="a-kpis">{"".join(cards)}</div>'


def delta(text, rgb=None) -> str:
    style = f' style="--rgb:{rgb}"' if rgb else ""
    return f'<span class="a-delta"{style}>{esc(text)}</span>'


def section(kicker, title, sub="") -> str:
    sub_html = f"<p>{esc(sub)}</p>" if sub else ""
    return _c(f'<div class="a-sec"><div><div class="a-kicker">{esc(kicker)}</div><h3>{esc(title)}</h3></div>{sub_html}</div>')


def _badge(text, rgb) -> str:
    return f'<span class="a-badge" style="--rgb:{rgb}">{esc(text)}</span>' if text else ""


def podium(items: list, total: int) -> str:
    """items: dicts with title/value/badge/rgb, sorted desc. Shows top 3 as 2nd-1st-3rd."""
    medals = ["🥇", "🥈", "🥉"]
    cards = []
    for pos in (1, 0, 2):
        if pos >= len(items):
            continue
        it = items[pos]
        share = (it["value"] / total * 100) if total else 0
        cards.append(
            f'<div class="a-pod p{pos + 1}" style="--rgb:{MEDAL_RGB[pos]};--i:{pos}"><span class="a-medal">{medals[pos]}</span>'
            f'<h4>{esc(it["title"])}</h4>{_badge(it.get("badge"), it.get("rgb", AMBER))}'
            f'<div class="num">{count_html(it["value"])}</div><div class="share">{share:.1f}% of all downloads</div></div>')
    return f'<div class="a-podium">{"".join(cards)}</div>'


def rank_panel(items: list, start=1, value_label="") -> str:
    """Animated leaderboard rows. items: dicts with title/value/badge/rgb."""
    if not items:
        return ""
    top = max(i["value"] for i in items) or 1
    rows = []
    for n, it in enumerate(items):
        rgb = it.get("rgb", AMBER)
        w = max(it["value"] / top * 100, 2)
        rows.append(
            f'<div class="a-rank" style="--i:{n};--rgb:{rgb}"><span class="n">{start + n:02d}</span>'
            f'<div class="t"><b title="{esc(it["title"])}">{esc(it["title"])}</b>{_badge(it.get("badge"), rgb)}</div>'
            f'<div class="a-track"><i style="--w:{w:.1f}%"></i></div><span class="v">{it["value"]:,}{value_label}</span></div>')
    return f'<div class="a-panel">{"".join(rows)}</div>'


def pills(titles: list, limit=60) -> str:
    shown = titles[:limit]
    more = len(titles) - len(shown)
    html_ = "".join(f'<span class="a-pill" style="--i:{i}">{esc(t)}</span>' for i, t in enumerate(shown))
    if more > 0:
        html_ += f'<span class="a-pill">+{more} more</span>'
    return f'<div>{html_}</div>'


def empty_state(icon, title, text, steps=()) -> str:
    st_html = "".join(f'<div class="a-step"><i>{n}</i><b>{esc(t)}</b><span>{esc(d)}</span></div>'
                      for n, (t, d) in enumerate(steps, 1))
    steps_block = f'<div class="a-steps">{st_html}</div>' if st_html else ""
    return _c(f'<div class="a-empty"><span class="big">{icon}</span><h3>{esc(title)}</h3><p>{esc(text)}</p>{steps_block}</div>')


def health_ring(pct: float, caption="healthy") -> str:
    pct = max(0.0, min(100.0, float(pct)))
    circ = 2 * 3.14159265 * 58
    off = circ * (1 - pct / 100)
    rgb = EMERALD if pct >= 90 else AMBER if pct >= 70 else ROSE
    return _c(f'<div class="a-ring" style="--rgb:{rgb};--C:{circ:.1f};--off:{off:.1f}"><svg viewBox="0 0 140 140">'
              f'<circle class="rb" cx="70" cy="70" r="58"/><circle class="rf" cx="70" cy="70" r="58" transform="rotate(-90 70 70)"/></svg>'
              f'<div class="a-ring-c"><b>{pct:.0f}%</b><span>{esc(caption)}</span></div></div>')


def health_panel(summary: dict, generated_at: str) -> str:
    total = summary.get("total", 0) or 0
    checked = total - summary.get("SKIP", 0)
    pct = (summary.get("OK", 0) / checked * 100) if checked else 100
    minis = [("OK", "OK", EMERALD), ("BROKEN", "Broken", ROSE), ("WARN", "Warnings", AMBER), ("SKIP", "Skipped", SKY)]
    tiles = "".join(f'<div class="a-mini" style="--rgb:{rgb}"><b>{count_html(summary.get(k, 0))}</b><span>{lbl}</span></div>'
                    for k, lbl, rgb in minis)
    return _c(f'<div class="a-health">{health_ring(pct)}<div class="a-minis">{tiles}'
              f'<div style="grid-column:1/-1;color:#64748b;font:500 12px \'JetBrains Mono\',monospace">'
              f'{total} links · last check {esc(generated_at)}</div></div></div>')


def _location_rows(r: dict, limit: int = 4) -> str:
    locs = r.get("locations")
    if not locs:  # reports made by older versions only have plain strings
        locs = [{"path": s, "area": "", "card": None, "label": "", "origin": "", "site_link": ""} for s in r.get("sources", [])]
    rows = []
    for l in locs[:limit]:
        if l.get("area") or l.get("card") or l.get("label"):
            crumbs = [(l.get("area"), ""), (l.get("card"), ""), (l.get("label"), " btn")]
            parts = [f'<span class="a-crumb{cls}">{esc(t)}</span>' for t, cls in crumbs if t]
            trail = '<i>›</i>'.join(parts)
        else:
            trail = f'<span class="a-crumb">{esc(l["path"])}</span>'
        tag = f'<span class="a-tag">{esc(l["origin"])}</span>' if l.get("origin") else ""
        link = (f'<a class="a-open" href="{esc(l["site_link"])}" target="_blank" rel="noopener noreferrer">Open section ↗</a>'
                if l.get("site_link") else "")
        rows.append(f'<div class="a-loc">{trail}{tag}{link}</div>')
    more = len(locs) - limit
    if more > 0:
        rows.append(f'<div class="a-loc"><span class="a-crumb">+{more} more location{"s" if more > 1 else ""}</span></div>')
    head = "Found on your site" if len(locs) == 1 else f"Found in {len(locs)} places on your site"
    return f'<div class="a-where"><div class="a-where-h">📍 {head}</div>{"".join(rows)}</div>'


def issue_rows(issues: list) -> str:
    rows = []
    for n, r in enumerate(issues):
        rgb = ROSE if r["status"] == "BROKEN" else AMBER
        rows.append(
            f'<div class="a-issue" style="--rgb:{rgb};--i:{n}"><span class="st">{esc(r["status"])}</span><div>'
            f'<a href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer">{esc(r["url"])}</a>'
            f'<p>{esc(r["detail"])}</p>{_location_rows(r)}</div></div>')
    return "".join(rows)


def mini_title(text) -> str:
    return f'<div class="a-mt">{esc(text)}</div>'


def sidebar_brand() -> str:
    return ('<div class="a-sbrand"><div class="a-logo">✚</div><div><b>Area 139</b><span>ADMIN · MEDINOTE</span></div></div>')


def side_heading(text) -> str:
    return f'<div class="a-side-h">{esc(text)}</div>'


def footer(stamp: str) -> str:
    return f'<div class="a-foot">Made with <b>♥</b> for Area 139 · refreshed {esc(stamp)}</div>'


def login_card() -> str:
    return _c('<div class="a-empty" style="max-width:520px;margin:8vh auto 18px"><span class="big">🔐</span>'
              '<h3>Area 139 Admin</h3><p style="margin-bottom:6px">Enter your password to continue.</p></div>')
