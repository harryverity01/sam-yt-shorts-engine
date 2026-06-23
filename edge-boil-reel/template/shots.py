# Full-page screenshots of real article pages (best-effort cookie-banner dismissal).
# Run from your work dir; outputs land in assets/. Chromium launches with
# --ignore-certificate-errors for the cloud egress proxy's self-signed TLS.
#
# REPLACE the PAGES list below with THIS reel's real article URLs. The entries here are
# only an example. Each entry is (url, output_path).
import asyncio
from playwright.async_api import async_playwright

PAGES = [
    ("https://techcrunch.com/2026/06/09/anthropics-claude-fable-5-is-a-version-of-mythos-the-public-can-access-today/", "assets/headline-techcrunch.png"),
    ("https://www.cnbc.com/2026/06/09/anthropic-mythos-claude-fable-5.html", "assets/headline-cnbc.png"),
    ("https://www.nytimes.com/1958/07/08/archives/new-navy-device-learns-by-doing-psychologist-shows-embryo-of.html", "assets/nyt-archive-1958.png"),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--ignore-certificate-errors"])
        ctx = await browser.new_context(viewport={"width":1280,"height":1600},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
        for url, out in PAGES:
            page = await ctx.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(4000)
                # best-effort dismiss overlays
                for sel in ["button:has-text('Accept')","button:has-text('I Accept')","button:has-text('Agree')","[aria-label='Close']","button:has-text('Continue')"]:
                    try: await page.locator(sel).first.click(timeout=1500)
                    except Exception: pass
                await page.wait_for_timeout(1500)
                await page.screenshot(path=out)
                print("OK", out)
            except Exception as e:
                print("FAIL", out, str(e)[:120])
            await page.close()
        await browser.close()

asyncio.run(main())
