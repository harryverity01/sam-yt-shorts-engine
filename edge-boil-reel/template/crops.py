# Crop the headline (h1) out of real article pages at 2x for crisp cards on the stage.
# Run from your work dir; outputs land in assets/. Launches Chromium with
# --ignore-certificate-errors because the cloud egress proxy self-signs TLS.
#
# REPLACE the JOBS list below with THIS reel's real article URLs. The entries here are
# only an example (they were the headlines for the sample reel). Each job is
# (url, css_selector, output_path, _scale).
import asyncio
from playwright.async_api import async_playwright

JOBS = [
    ("https://techcrunch.com/2026/06/09/anthropics-claude-fable-5-is-a-version-of-mythos-the-public-can-access-today/", "h1", "assets/crop-techcrunch.png", 2),
    ("https://www.cnbc.com/2026/06/09/anthropic-mythos-claude-fable-5.html", "h1", "assets/crop-cnbc.png", 2),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--ignore-certificate-errors"])
        ctx = await browser.new_context(viewport={"width":1280,"height":1600}, device_scale_factor=2,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
        for url, sel, out, scale in JOBS:
            page = await ctx.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(3500)
                el = page.locator(sel).first
                box = await el.bounding_box()
                pad = 40
                clip = {"x": max(0,box["x"]-pad), "y": max(0,box["y"]-70),
                        "width": min(1280, box["width"]+2*pad), "height": box["height"]+70+50}
                await page.screenshot(path=out, clip=clip)
                print("OK", out, clip)
            except Exception as e:
                print("FAIL", out, str(e)[:150])
            await page.close()
        await browser.close()

asyncio.run(main())
