"""HTTP client that transparently solves the 2waf JS proof-of-work challenge
used by omr.gov.ua, so the rest of the parser can just call get(url)."""
import re, time, hashlib, base64, itertools, http.cookiejar, urllib.request, urllib.error

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

_cj = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))
_opener.addheaders = [("User-Agent", UA),
                      ("Accept-Language", "uk,en;q=0.9"),
                      ("Accept", "text/html,application/xhtml+xml")]

CHARS = "01"

def _decode(data):
    # site serves cyrillic; try utf-8 then cp1251
    for enc in ("utf-8", "windows-1251"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")

def _raw(url):
    req = urllib.request.Request(url)
    try:
        with _opener.open(req, timeout=60) as r:
            return _decode(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 503:
            return _decode(e.read())
        raise

def _is_challenge(html):
    return "pow-result" in html and "hash4find" in html

def _solve(html):
    prefix = re.search(r'const prefix\s*=\s*"([^"]+)"', html).group(1)
    suffix_len = int(re.search(r'const suffixLen\s*=\s*(\d+)', html).group(1))
    target = re.search(r'const hash4find\s*=\s*"([^"]+)"', html).group(1)
    notbot = re.search(r"setCookie\('notbot','([^']+)'\)", html).group(1)
    for combo in itertools.product(CHARS, repeat=suffix_len):
        s = prefix + "".join(combo)
        if hashlib.sha256(s.encode()).hexdigest() == target:
            pow_result = base64.b64encode(s.encode()).decode()
            return notbot, pow_result
    raise RuntimeError("PoW solution not found")

def _set_cookie(name, value):
    c = http.cookiejar.Cookie(0, name, value, None, False,
                              "omr.gov.ua", True, False, "/", True,
                              True, None, False, None, None, {})
    _cj.set_cookie(c)

def get(url, retries=4):
    for attempt in range(retries):
        html = _raw(url)
        if not _is_challenge(html):
            return html
        notbot, pow_result = _solve(html)
        _set_cookie("notbot", notbot)
        _set_cookie("pow-result", pow_result)
        # server rejects solutions returned faster than the JS minimum (~5.5s)
        time.sleep(6)
    # last try
    html = _raw(url)
    if _is_challenge(html):
        raise RuntimeError(f"Still blocked after {retries} attempts: {url}")
    return html

if __name__ == "__main__":
    import sys
    h = get(sys.argv[1] if len(sys.argv) > 1 else "https://omr.gov.ua/ua/acts/projects/committee/")
    print("OK length:", len(h))
    print(h[:1500])
