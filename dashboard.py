"""Area 139 · Command Center (Streamlit admin dashboard).

Run:   python -m streamlit run dashboard.py
"""
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Area 139 · Command Center", page_icon="✚", layout="wide")

# Bridge Streamlit secrets -> env vars so common.py can read them everywhere.
for _k in ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_KEY", "GA4_PROPERTY_ID",
           "DASHBOARD_PASSWORD", "GA_CREDENTIALS_JSON", "SITE_URL"):
    try:
        if _k in st.secrets:
            os.environ.setdefault(_k, str(st.secrets[_k]))
    except Exception:
        pass

import charts  # noqa: E402
import ui  # noqa: E402
from common import fetch_table  # noqa: E402

REPORT = Path(__file__).resolve().parent / "reports" / "link_report.json"
BD = timezone(timedelta(hours=6))  # Bangladesh time

st.markdown(ui.css(), unsafe_allow_html=True)

# ------------------------------------------------------------------ password gate
pw = os.getenv("DASHBOARD_PASSWORD")
if pw and not st.session_state.get("authed"):
    st.markdown(ui.login_card(), unsafe_allow_html=True)
    _l, _m, _r = st.columns([1, 1, 1])
    with _m:
        entered = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Password")
    if entered:
        if hmac.compare_digest(entered, pw):
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


# ------------------------------------------------------------------ helpers
def show(fig, key, select=False):
    """Render a Plotly figure; optionally return the clicked points (Streamlit >= 1.35)."""
    cfg = {"displayModeBar": False, "scrollZoom": False}
    if select:
        try:
            return st.plotly_chart(fig, key=key, theme=None, config=cfg, on_select="rerun", selection_mode="points")
        except TypeError:
            pass
    st.plotly_chart(fig, key=key, theme=None, config=cfg)
    return None


def picked_categories(event):
    try:
        pts = event["selection"]["points"]
    except Exception:
        return []
    out = []
    for p in pts:
        v = p.get("y") or p.get("label")
        if v and v not in out:
            out.append(v)
    return out


def greeting(now):
    h = now.hour
    if 5 <= h < 12:
        return "Good morning,"
    if 12 <= h < 15:
        return "Good afternoon,"
    if 15 <= h < 18:
        return "Good afternoon,"
    if 18 <= h < 20:
        return "Good evening,"
    return "Good evening,"


@st.cache_data(ttl=300, show_spinner="Loading data from Supabase...")
def load_supabase():
    return pd.DataFrame(fetch_table("posts")), pd.DataFrame(fetch_table("post_categories"))


def prep(posts: pd.DataFrame, cats: pd.DataFrame) -> pd.DataFrame:
    posts = posts.copy()
    for col, default in (("title", ""), ("category_slug", None), ("download_count", 0),
                         ("created_at", None), ("is_draft", False), ("download_link", "")):
        if col not in posts.columns:
            posts[col] = default
    posts["download_count"] = pd.to_numeric(posts["download_count"], errors="coerce").fillna(0).astype(int)
    names = {}
    if not cats.empty and {"slug", "name"} <= set(cats.columns):
        names = dict(zip(cats["slug"], cats["name"]))
    posts["category"] = posts["category_slug"].map(names).fillna(posts["category_slug"]).fillna("Uncategorised")
    posts["created_at"] = pd.to_datetime(posts["created_at"], errors="coerce", utc=True)
    posts["is_draft"] = posts["is_draft"].fillna(False).astype(bool)
    return posts


def load_link_report():
    if REPORT.exists():
        try:
            return json.loads(REPORT.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


# ------------------------------------------------------------------ Google Analytics 4
@st.cache_resource
def ga_client():
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.oauth2 import service_account

    scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
    info = None
    try:
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
    except Exception:
        pass
    if info is None and os.getenv("GA_CREDENTIALS_JSON"):
        info = json.loads(os.environ["GA_CREDENTIALS_JSON"])
    if info:
        creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
        return BetaAnalyticsDataClient(credentials=creds)
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return BetaAnalyticsDataClient()
    return None


@st.cache_data(ttl=600, show_spinner="Loading data from Google Analytics...")
def ga_report(prop: str, days: int, dims: tuple, mets: tuple, limit: int = 10) -> pd.DataFrame:
    from google.analytics.data_v1beta.types import (DateRange, Dimension, Metric, OrderBy,
                                                    RunReportRequest)

    req = RunReportRequest(
        property=f"properties/{prop}",
        dimensions=[Dimension(name=d) for d in dims],
        metrics=[Metric(name=m) for m in mets],
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        limit=limit,
    )
    if dims and dims != ("date",):
        req.order_bys = [OrderBy(metric=OrderBy.MetricOrderBy(metric_name=mets[0]), desc=True)]
    resp = ga_client().run_report(req)
    rows = [[v.value for v in r.dimension_values] + [v.value for v in r.metric_values] for r in resp.rows]
    df = pd.DataFrame(rows, columns=list(dims) + list(mets))
    for m in mets:
        df[m] = pd.to_numeric(df[m])
    return df


# ------------------------------------------------------------------ load data
try:
    posts_raw, cats_raw = load_supabase()
except Exception as e:
    st.markdown(ui.empty_state("🔌", "Can't connect to Supabase", str(e)[:300],
                [("Check the key", "Is SUPABASE_KEY set correctly in .env?"),
                 ("Permissions", "With a service key, run the GRANT SELECT SQL"),
                 ("Retry", "Press Refresh in the sidebar")]), unsafe_allow_html=True)
    st.stop()

posts = prep(posts_raw, cats_raw)
COLORS = ui.cat_palette(posts["category"].unique())
HEX = {c: v[0] for c, v in COLORS.items()}
RGB = {c: v[1] for c, v in COLORS.items()}
now = datetime.now(BD)

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown(ui.sidebar_brand(), unsafe_allow_html=True)
    st.markdown(ui.side_heading("Filters"), unsafe_allow_html=True)
    sel_cats = st.multiselect("Category", sorted(posts["category"].unique()), placeholder="All categories")
    dated_all = posts["created_at"].dropna()
    rng = None
    if not dated_all.empty and dated_all.min().date() < dated_all.max().date():
        dmin, dmax = dated_all.min().date(), dated_all.max().date()
        picked = st.date_input("Upload date", value=(dmin, dmax), min_value=dmin, max_value=dmax)
        if isinstance(picked, (tuple, list)) and len(picked) == 2 and tuple(picked) != (dmin, dmax):
            rng = picked
    show_drafts = st.toggle("Include drafts", value=False)
    st.markdown(ui.side_heading("Actions"), unsafe_allow_html=True)
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
    if pw and st.button("🚪 Log out"):
        st.session_state.clear()
        st.rerun()

# ------------------------------------------------------------------ apply filters
df = posts.copy()
if not show_drafts:
    df = df[~df["is_draft"]]
if sel_cats:
    df = df[df["category"].isin(sel_cats)]
if rng:
    day = df["created_at"].dt.tz_convert(None).dt.date
    df = df[day.between(rng[0], rng[1])]

prop = os.getenv("GA4_PROPERTY_ID")
ga_ready = False
if prop:
    try:
        ga_ready = ga_client() is not None
    except Exception:
        ga_ready = False
rep = load_link_report()

# ------------------------------------------------------------------ hero
total_dl = int(df["download_count"].sum()) if not df.empty else 0
chips = [("Live data", "ok", True), (f"{now:%d %b, %I:%M %p} BDT", "", False),
         (f"Supabase · {len(posts)} notes", "ok", False),
         ("GA4 connected" if ga_ready else "GA4 not connected", "ok" if ga_ready else "warn", False)]
if rep:
    s_ = rep["summary"]
    chips.append((f"{s_['BROKEN']} broken links" if s_["BROKEN"] else "All links healthy", "bad" if s_["BROKEN"] else "ok", False))
st.markdown(ui.hero(greeting(now), f"Today's snapshot: {len(df)} notes · {total_dl:,} downloads.", chips), unsafe_allow_html=True)

if df.empty:
    st.markdown(ui.empty_state("🕳️", "No notes match these filters", "Try loosening the filters in the sidebar.",
                [("Category", "Clear the category filter"), ("Date", "Widen the date range"), ("Drafts", "Turn on 'Include drafts'")]),
                unsafe_allow_html=True)
    st.stop()

if not st.session_state.get("greeted"):
    st.session_state["greeted"] = True
    try:
        st.toast(f"{total_dl:,} total downloads", icon="🏆")
    except Exception:
        pass

# ------------------------------------------------------------------ KPI strip
by_cat = (df.groupby("category").agg(posts=("title", "count"), downloads=("download_count", "sum")).reset_index())
by_cat["avg"] = (by_cat["downloads"] / by_cat["posts"]).round(1)
by_cat = by_cat.sort_values("downloads", ascending=False)
top_cat = by_cat.iloc[0]
zero_n = int((df["download_count"] == 0).sum())
avg_dl = df["download_count"].mean()
med_dl = df["download_count"].median()
popularity = df["download_count"].sort_values(ascending=False).head(14).tolist()
dated = df.dropna(subset=["created_at"])
growth_spark = None
if not dated.empty:
    mcount = dated.groupby(dated["created_at"].dt.tz_convert(None).dt.to_period("M")).size().sort_index()
    if len(mcount) >= 2:
        growth_spark = mcount.cumsum().tolist()
    last_note = dated["created_at"].max().tz_convert(BD)
    freshness = f"latest {last_note:%d %b}"
else:
    freshness = "no dates"
share = (top_cat["downloads"] / total_dl * 100) if total_dl else 0

st.markdown(ui.kpi_grid([
    ui.kpi_card("Total downloads", ui.count_html(total_dl), ui.delta(f"{len(df)} notes", ui.AMBER) + "all time", "📥", ui.AMBER, 0, popularity),
    ui.kpi_card("Library size", ui.count_html(len(df)), ui.delta(f"😴 {zero_n}", ui.SKY) + "never downloaded", "📚", ui.SKY, 1, growth_spark),
    ui.kpi_card("Avg per note", f"{avg_dl:,.1f}", ui.delta(f"median {med_dl:,.0f}", ui.VIOLET) + freshness, "⚡", ui.VIOLET, 2),
    ui.kpi_card("Top category", ui.esc(top_cat["category"]), ui.delta(f"{share:.0f}%", ui.EMERALD) + f"{int(top_cat['posts'])} notes", "🏆", ui.EMERALD, 3, small=True),
]), unsafe_allow_html=True)

tab_dl, tab_vis, tab_links, tab_data = st.tabs(["📥 Downloads", "🌍 Visitors", "🔗 Link health", "🗂 Data"])

# ================================================================== DOWNLOADS
with tab_dl:
    st.markdown(ui.section("Hall of fame", "Top notes", "The most downloaded notes on your site"), unsafe_allow_html=True)
    with st.container(key="pill_top"):
        top_n = st.radio("Top N", [5, 10, 15, 25], index=1, horizontal=True, label_visibility="collapsed",
                         format_func=lambda n: f"Top {n}")
    ranked = df.sort_values("download_count", ascending=False).head(top_n)
    items = [{"title": r.title, "value": int(r.download_count), "badge": r.category, "rgb": RGB[r.category]}
             for r in ranked.itertuples()]
    st.markdown(ui.podium(items, total_dl), unsafe_allow_html=True)
    if len(items) > 3:
        st.markdown(ui.rank_panel(items[3:], start=4), unsafe_allow_html=True)

    st.markdown(ui.section("Categories", "Which categories perform best?", "Click a bar to focus on that category"), unsafe_allow_html=True)
    left, right = st.columns([3, 2])
    with left:
        event = show(charts.category_bar(by_cat, HEX), "cat_bar", select=True)
    with right:
        show(charts.category_donut(by_cat, HEX), "cat_donut")
    focus = picked_categories(event)
    if focus:
        fdf = df[df["category"].isin(focus)].sort_values("download_count", ascending=False).head(12)
        st.markdown(ui.section("Focus", " + ".join(focus), f"{len(fdf)} top notes"), unsafe_allow_html=True)
        st.markdown(ui.rank_panel([{"title": r.title, "value": int(r.download_count), "badge": r.category, "rgb": RGB[r.category]}
                                   for r in fdf.itertuples()]), unsafe_allow_html=True)

    st.markdown(ui.section("Explore", "Your library at a glance", "Click a tile to zoom in, click the path above to go back"), unsafe_allow_html=True)
    if (df["download_count"] > 0).any():
        show(charts.treemap(df, HEX), "treemap")
    else:
        st.markdown('<div class="a-note">No downloads yet. The treemap will appear here once notes are downloaded.</div>', unsafe_allow_html=True)

    growth = charts.growth_combo(df)
    if growth is not None:
        st.markdown(ui.section("Growth", "How your library is growing", "Bars = new notes per month, line = total library size"), unsafe_allow_html=True)
        show(growth, "growth")

    zero_titles = df[df["download_count"] == 0]["title"].tolist()
    st.markdown(ui.section("Needs attention", "Never downloaded", f"{len(zero_titles)} notes worth promoting"), unsafe_allow_html=True)
    if zero_titles:
        st.markdown(ui.pills(zero_titles), unsafe_allow_html=True)
    else:
        st.markdown('<div class="a-note">🎉 Every note has been downloaded at least once!</div>', unsafe_allow_html=True)

    st.markdown(ui.section("Search", "Find any note"), unsafe_allow_html=True)
    q = st.text_input("Search", placeholder="🔎  Search by note title...", label_visibility="collapsed")
    table = df.sort_values("download_count", ascending=False)
    if q:
        table = table[table["title"].str.contains(q, case=False, na=False, regex=False)]
    st.dataframe(
        table[["title", "category", "download_count", "created_at", "download_link"]], hide_index=True,
        column_config={
            "title": "Title", "category": "Category",
            "download_count": st.column_config.ProgressColumn("Downloads", min_value=0, max_value=max(int(df["download_count"].max()), 1), format="%d"),
            "created_at": st.column_config.DatetimeColumn("Added", format="DD MMM YYYY"),
            "download_link": st.column_config.LinkColumn("Link", display_text="Open ↗"),
        })
    st.caption("Note: download_count only covers posts stored in Supabase (the increment_download RPC). Downloads of the hard-coded static cards are not counted here.")

# ================================================================== VISITORS
with tab_vis:
    if not ga_ready:
        st.markdown(ui.empty_state(
            "🔒", "Visitor insights are locked",
            "Connect Google Analytics to see the country map, daily traffic, devices and sources here.",
            [("Property ID", "GA > Admin > Property details. Put the number in .env as GA4_PROPERTY_ID"),
             ("Service account", "Create one in Google Cloud and download its JSON key"),
             ("Viewer access", "Add the service account email to GA as a Viewer"),
             ("Test", "Run python ga_test.py, then restart the dashboard")]), unsafe_allow_html=True)
    else:
        st.markdown(ui.section("Audience", "Visitors", "Google Analytics 4 · live"), unsafe_allow_html=True)
        with st.container(key="pill_days"):
            days = st.radio("Period", [7, 28, 90], index=1, horizontal=True, label_visibility="collapsed",
                            format_func=lambda d: f"Last {d} days")
        try:
            tot = ga_report(prop, days, (), ("activeUsers", "newUsers", "sessions", "screenPageViews"))
            row = tot.iloc[0] if not tot.empty else pd.Series({"activeUsers": 0, "newUsers": 0, "sessions": 0, "screenPageViews": 0})
            daily = ga_report(prop, days, ("date",), ("activeUsers", "sessions"), limit=1000)
            spark_u = spark_s = None
            if not daily.empty:
                daily["date"] = pd.to_datetime(daily["date"], format="%Y%m%d")
                daily = daily.sort_values("date")
                spark_u, spark_s = daily["activeUsers"].tolist(), daily["sessions"].tolist()
            nu, au = int(row["newUsers"]), int(row["activeUsers"])
            st.markdown(ui.kpi_grid([
                ui.kpi_card("Visitors", ui.count_html(au), f"last {days} days", "👥", ui.AMBER, 0, spark_u),
                ui.kpi_card("New visitors", ui.count_html(nu), ui.delta(f"{(nu / au * 100) if au else 0:.0f}%", ui.EMERALD) + "of visitors", "✨", ui.EMERALD, 1),
                ui.kpi_card("Sessions", ui.count_html(row["sessions"]), "total visits", "🔁", ui.VIOLET, 2, spark_s),
                ui.kpi_card("Page views", ui.count_html(row["screenPageViews"]), "all pages", "👁", ui.SKY, 3),
            ]), unsafe_allow_html=True)

            if not daily.empty:
                st.markdown(ui.section("Trend", "Daily traffic", "Drag the slider below the chart to zoom"), unsafe_allow_html=True)
                show(charts.traffic_area(daily), "ga_daily")

            countries = ga_report(prop, days, ("country",), ("activeUsers",), 60)
            st.markdown(ui.section("Geography", "Where your visitors come from", "Hover the map or the bars for details"), unsafe_allow_html=True)
            g1, g2 = st.columns([3, 2])
            with g1:
                if not countries.empty:
                    show(charts.world_map(countries), "ga_map")
            with g2:
                if not countries.empty:
                    show(charts.country_bar(countries), "ga_countries")

            cities = ga_report(prop, days, ("city",), ("activeUsers",), 10)
            devices = ga_report(prop, days, ("deviceCategory",), ("activeUsers",), 5)
            sources = ga_report(prop, days, ("sessionSource",), ("sessions",), 8)
            pages = ga_report(prop, days, ("pagePath",), ("screenPageViews",), 10)
            st.markdown(ui.section("Breakdown", "Cities, devices and traffic sources"), unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            with b1:
                st.markdown(ui.mini_title("Top cities"), unsafe_allow_html=True)
                st.markdown(ui.rank_panel([{"title": r.city, "value": int(r.activeUsers), "rgb": ui.SKY}
                                           for r in cities.itertuples() if r.city != "(not set)"]), unsafe_allow_html=True)
            with b2:
                st.markdown(ui.mini_title("Devices"), unsafe_allow_html=True)
                if not devices.empty:
                    show(charts.donut(devices["deviceCategory"].str.title().tolist(), devices["activeUsers"].tolist()), "ga_dev")
            with b3:
                st.markdown(ui.mini_title("Traffic sources"), unsafe_allow_html=True)
                st.markdown(ui.rank_panel([{"title": r.sessionSource, "value": int(r.sessions), "rgb": ui.VIOLET}
                                           for r in sources.itertuples()]), unsafe_allow_html=True)

            st.markdown(ui.section("Content", "Most viewed pages"), unsafe_allow_html=True)
            st.markdown(ui.rank_panel([{"title": r.pagePath, "value": int(r.screenPageViews), "rgb": ui.AMBER}
                                       for r in pages.itertuples()]), unsafe_allow_html=True)
        except Exception as e:
            st.markdown(ui.empty_state("⚠️", "Couldn't load Google Analytics data", str(e)[:260],
                        [("Property ID", "Is GA4_PROPERTY_ID correct?"), ("Viewer access", "Is the service account a Viewer in GA?"),
                         ("Test", "Run python ga_test.py")]), unsafe_allow_html=True)

# ================================================================== LINK HEALTH
with tab_links:
    st.markdown(ui.section("Health", "Are your download links working?",
                           "Every problem shows exactly where it lives on your site"), unsafe_allow_html=True)
    if st.button("▶  Run link check now"):
        from link_checker import run_check

        with st.spinner("Checking links... this can take a minute or two"):
            run_check()
        st.rerun()
    rep = load_link_report()
    if not rep:
        st.markdown(ui.empty_state("🛰️", "No link check yet", "Press the button above, or run `python link_checker.py` in a terminal."),
                    unsafe_allow_html=True)
    else:
        st.markdown(ui.health_panel(rep["summary"], rep["generated_at"].replace("T", " ")), unsafe_allow_html=True)
        for note in rep.get("notes", []):
            st.warning(note)
        bad = [r for r in rep["results"] if r["status"] in ("BROKEN", "WARN")]
        if bad:
            st.markdown(ui.section("Attention", f"{len(bad)} link{'s' if len(bad) != 1 else ''} need a look",
                                   "Use 'Open section' to jump straight to the place on your site"), unsafe_allow_html=True)
            st.markdown(ui.issue_rows(bad), unsafe_allow_html=True)
        else:
            st.markdown('<div class="a-note" style="margin-top:16px">🎉 All links are working!</div>', unsafe_allow_html=True)
        with st.expander("Show all links"):
            st.dataframe(pd.DataFrame([{
                "status": r["status"], "url": r["url"], "detail": r["detail"],
                "where on site": " | ".join(l["path"] for l in r.get("locations", [])[:3]) or " | ".join(r.get("sources", [])[:3]),
            } for r in rep["results"]]), hide_index=True)

# ================================================================== DATA
with tab_data:
    st.markdown(ui.section("Raw data", "Posts table", f"{len(posts)} rows · export as CSV or JSON"), unsafe_allow_html=True)
    c1, c2, _sp = st.columns([1, 1, 4])
    with c1:
        st.download_button("⬇ CSV", posts.to_csv(index=False).encode("utf-8-sig"), "area139_posts.csv", "text/csv")
    with c2:
        st.download_button("⬇ JSON", posts.to_json(orient="records", force_ascii=False, date_format="iso").encode("utf-8"),
                           "area139_posts.json", "application/json")
    st.dataframe(posts, hide_index=True)

st.markdown(ui.footer(f"{now:%d %b %Y, %I:%M %p}"), unsafe_allow_html=True)
