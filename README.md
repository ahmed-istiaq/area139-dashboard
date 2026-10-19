# Area 139 tools - Command Center dashboard, link checker and backups

| File | Purpose |
|---|---|
| `dashboard.py` + `ui.py` + `charts.py` | Interactive admin dashboard ("Command Center") |
| `link_checker.py` | Checks every Telegram / Drive / other link and tells you exactly where on the site each one lives |
| `backup.py` | Zip backup of your Supabase tables |
| `ga_test.py` | Google Analytics connection test |
| `.github/workflows/` | Runs the link check (Mon + Thu) and the backup (weekly) automatically |
| `.streamlit/config.toml` | Dark + amber theme |

## 1. Run locally

```bash
python -m pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
python -m streamlit run dashboard.py
python link_checker.py
python backup.py
```

**Where to find the keys**
- `SUPABASE_KEY`: the `SUPABASE_PUBLISHABLE_KEY` in your `index.html` (read-only access is enough).
- `SUPABASE_SERVICE_KEY`: Supabase Dashboard > Project Settings > API > *service_role / secret*. **Keep it secret.** Never put it in `index.html` or a public repo.
- `TELEGRAM_BOT_TOKEN`: from @BotFather. `TELEGRAM_CHAT_ID`: message @userinfobot and it replies with your numeric ID.

## 2. What the dashboard shows

- **Hero + KPI cards:** animated count-up numbers, sparklines, hover glow.
- **Downloads:** podium (top 3), animated leaderboard, category bars (**click a bar to focus**), donut, **treemap** (click a tile to zoom), library growth chart and a searchable table.
- **Visitors:** daily traffic (drag the slider to zoom), **world map with a country chart beside it**, cities, devices, traffic sources and top pages.
- **Link health:** health ring plus a list of broken links. Each one shows **where it lives on your site** as `Section > Card > Button`, with an "Open section" link that jumps straight there.
- **Sidebar filters:** category, upload date and drafts.

## 3. Link checker: finding a broken link on your site

For every link the checker records where it is used, for example:

```
MBBS Textbooks & Clinical Atlases > Gray's Anatomy (14th Ed) > Open in Telegram   [Page]
Anatomy > Brachial Plexus Notes > Download Here                                  [Database]
Footer > Facebook                                                                [Page]
```

`[Page]` means the link is hard-coded in `index.html`. `[Database]` means it comes from a Supabase post, so fix it in your admin panel. The same details are included in the Telegram alert and in `reports/link_report.md`.

## 4. GitHub Actions (automatic link check + weekly backup)

1. Push this folder to a **private** GitHub repo (backup artifacts of public repos can be downloaded by anyone).
2. Repo > Settings > Secrets and variables > Actions > New secret:
   `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (the Telegram ones are optional).
3. Open the Actions tab and run "Link check" and "Weekly Supabase backup" once with *Run workflow* to test them.
4. If a link is broken the job fails and GitHub emails you. Backup zips are under *Artifacts* on the run page (kept for 90 days).

> GitHub disables scheduled workflows after 60 days without repo activity. If that happens, re-enable them from the Actions tab.

## 5. Deploy the dashboard (Streamlit Community Cloud, free)

1. Private repo > share.streamlit.io > New app > `dashboard.py`.
2. Advanced settings > Secrets:

```toml
SUPABASE_KEY = "..."
DASHBOARD_PASSWORD = "your-password"
GA4_PROPERTY_ID = "123456789"

[gcp_service_account]
# paste every field of the service account JSON here (type, project_id, private_key, client_email, ...)
```

## 6. Connect Google Analytics (Visitors tab)

1. GA > Admin > Property details: copy the **Property ID** (digits only, not `G-XXXX`).
2. Google Cloud Console: enable the **Google Analytics Data API**, create a service account and download its JSON key.
3. GA > Admin > Property access management: add the service account email as a **Viewer**.
4. Local use: save the key as `ga-key.json` and set `GOOGLE_APPLICATION_CREDENTIALS=ga-key.json`. Hosting: use the `[gcp_service_account]` secret.
5. Run `python ga_test.py`. When it prints `OK!`, restart the dashboard.

## Limitations
- `download_count` only covers posts stored in Supabase (the `increment_download` RPC). Downloads of the hard-coded static cards are not counted.
- Telegram: public post links (`t.me/channel/123`) are checked for deletion. Private and invite links (`t.me/c/...`, `t.me/+...`) can't be verified and are marked SKIP.
- Drive: a deleted file is BROKEN. "Quota exceeded" or "needs access" is a WARN (temporary or a permission issue).
- Facebook, X and YouTube sometimes block bots, so a WARN there can be a false alarm.
