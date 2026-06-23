import asyncio, sys, os, glob
from playwright.async_api import async_playwright

# usage: render.py preview t1 t2 ...   OR   render.py full [fps] [t_end]
async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "preview"
    hf_count = len(glob.glob("clipframes/f_*.jpg"))
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--force-color-profile=srgb","--disable-lcd-text"])
        page = await browser.new_page(viewport={"width":1080,"height":1920})
        await page.goto("file://" + os.path.abspath("stage.html"))
        await page.evaluate(f"window.HF_COUNT={hf_count}; HFCLIP.count={hf_count};")
        await page.evaluate("document.fonts.ready.then(()=>{})")
        await page.wait_for_timeout(1200)
        # show b2/b3 once so spans lay out, then measure underline geometry
        await page.evaluate("seek(6); ")
        await page.wait_for_timeout(100)
        await page.evaluate("document.getElementById('b3').style.opacity=1; setUnderlines();")
        await page.wait_for_timeout(100)

        if mode == "preview":
            times = [float(x) for x in sys.argv[2:]] or [2.0,4.2,6.9,8.3,11.8,15.2,16.6,18.8,21.0,23.2,25.2,28.2,30.8]
            os.makedirs("preview", exist_ok=True)
            for t in times:
                await page.evaluate(f"seek({t})")
                await page.wait_for_timeout(60)
                await page.screenshot(path=f"preview/t{str(t).replace('.','_')}.jpg", quality=85, type="jpeg")
                print("shot", t)
        else:
            fps = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            t_end = float(sys.argv[3]) if len(sys.argv) > 3 else 32.0
            os.makedirs("frames_out", exist_ok=True)
            n = int(t_end * fps)
            for i in range(n):
                t = i / fps
                await page.evaluate(f"seek({t})")
                await page.screenshot(path=f"frames_out/{i:05d}.jpg", quality=88, type="jpeg")
                if i % 60 == 0: print(f"{i}/{n}", flush=True)
        await browser.close()

asyncio.run(main())
