"""Download brand + vintage fonts from Google Fonts with css rewritten to local paths.
Run from the project working dir; creates fonts/all.css + fonts/*.woff2.
IMPORTANT: url() paths in css resolve relative to the CSS FILE, so all.css must
reference bare filenames (they sit in the same folder)."""
import urllib.request, re, ssl, os
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (Macintosh) Chrome/137"})
    return urllib.request.urlopen(req, context=ctx, timeout=30).read()
css_urls = {
 "fraunces":"https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,700;9..144,900&display=swap",
 "inter":"https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap",
 "plexmono":"https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap",
 "oldstandard":"https://fonts.googleapis.com/css2?family=Old+Standard+TT:wght@400;700&display=swap",
 "caveat":"https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&display=swap",
}
os.makedirs("fonts", exist_ok=True)
combined = []
for name,u in css_urls.items():
    css = get(u).decode()
    idx = 0
    def repl(m):
        global idx
        fn = f"fonts/{name}-x{idx}.woff2"
        open(fn,"wb").write(get(m.group(1)))
        idx += 1
        return f"url('{os.path.basename(fn)}')"
    css = re.sub(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", repl, css)
    combined.append(css)
open("fonts/all.css","w").write("\n".join(combined))
print("fonts ready:", sum(c.count('@font-face') for c in combined), "faces")
