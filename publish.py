#!/usr/bin/env python3
"""KeyBrox_TR — Instagram otomatik yayinlayici.
Sirdaki seti alir: 1 gonderi (tek kareyse foto, coklu kareyse carousel) + hikaye
karesi/kareleri. Basarili olursa siradaki sete gecer.

GUNLUK SINIR (31 Agu 2026'da eklendi): cron guvenlik-agi tekrar denemeleri
gunde 15-20 kez calisabiliyor; sinirsiz sira ilerlemesi 30 gunluk kuyrugu
2 gunde tuketti ve ardindan Meta tarafinda art arda hata (muhtemelen hiz
siniri) basladi. Artik gunde en fazla GUNLUK_LIMIT set yayinlanir; asilan
denemeler sessizce cikar — cift yayin yapmaz, siradaki gune tasmaz.
"""
import json, os, sys, time, urllib.parse, urllib.request, datetime

API = "https://graph.instagram.com/v23.0"
IG_ID = os.environ["IG_USER_ID"].strip()
TOKEN = os.environ["IG_ACCESS_TOKEN"].strip()
REPO  = os.environ.get("GITHUB_REPOSITORY", "")
REF   = os.environ.get("MEDIA_REF", "main")
RAW   = f"https://raw.githubusercontent.com/{REPO}/{REF}/"
ROOT  = os.path.dirname(os.path.abspath(__file__))
DRY   = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
GUNLUK_LIMIT = 2  # 11:00 + 19:00 = gunde en fazla 2 set

# Turkiye 2016'dan beri yaz saati uygulamiyor — sabit UTC+3.
TR = datetime.timezone(datetime.timedelta(hours=3))


def bugun():
    return datetime.datetime.now(TR).date().isoformat()


def call(method, path, params):
    params = dict(params, access_token=TOKEN)
    url = f"{API}/{path}"
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {body}") from None


def wait_ready(cid, tries=20):
    for _ in range(tries):
        st = call("GET", cid, {"fields": "status_code"}).get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"kapsayici {cid} durumu: {st}")
        time.sleep(5)
    raise RuntimeError(f"kapsayici {cid} zaman asimi")


def publish(cid):
    return call("POST", f"{IG_ID}/media_publish", {"creation_id": cid})["id"]


def main():
    content = json.load(open(f"{ROOT}/icerik.json", encoding="utf-8"))
    state_path = f"{ROOT}/state/durum.json"
    state = json.load(open(state_path, encoding="utf-8"))
    nxt = state["sonraki"]

    gunluk = state.setdefault("gunluk_sayac", {})
    bugun_str = bugun()
    if gunluk.get(bugun_str, 0) >= GUNLUK_LIMIT:
        print(f"{bugun_str} icin gunluk sinir ({GUNLUK_LIMIT}) doldu. Cikiliyor.")
        return 0

    item = next((s for s in content["sets"] if s["sira"] == nxt), None)
    if item is None:
        print(f"Kuyrukta {nxt} numarali set yok — seri tamamlandi. Cikiliyor.")
        return 0

    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    print(f"Set {nxt} — {item['ad']} | {len(item['post'])} gonderi karesi, {len(item['story'])} hikaye")

    if DRY:
        for p in item["post"] + item["story"]:
            print("  ", RAW + p)
        print("DRY_RUN — hicbir sey yayinlanmadi.")
        return 0

    # 1) Gonderi — tek kare ise duz foto, coklu ise carousel.
    # Instagram Graph API tek elemanli CAROUSEL kabul etmiyor (min 2 cocuk ister),
    # bu yuzden 1 karelik gunler normal IMAGE olarak gonderilir.
    if len(item["post"]) == 1:
        img = call("POST", f"{IG_ID}/media", {"image_url": RAW + item["post"][0], "caption": item["caption"]})
        img_id = img["id"]
        wait_ready(img_id)
        post_id = publish(img_id)
    else:
        children = []
        for p in item["post"]:
            r = call("POST", f"{IG_ID}/media", {"image_url": RAW + p, "is_carousel_item": "true"})
            children.append(r["id"])
            print("  cocuk kapsayici:", r["id"])
        for c in children:
            wait_ready(c)
        car = call("POST", f"{IG_ID}/media", {
            "media_type": "CAROUSEL",
            "children": ",".join(children),
            "caption": item["caption"],
        })["id"]
        wait_ready(car)
        post_id = publish(car)
    print("  GONDERI YAYINLANDI:", post_id)

    # 2) Hikayeler
    story_ids = []
    for s in item["story"]:
        time.sleep(5)
        sc = call("POST", f"{IG_ID}/media", {"image_url": RAW + s, "media_type": "STORIES"})["id"]
        wait_ready(sc)
        sid = publish(sc)
        story_ids.append(sid)
        print("  HIKAYE YAYINLANDI:", sid)

    state["sonraki"] = nxt + 1
    gunluk[bugun_str] = gunluk.get(bugun_str, 0) + 1
    state["log"].append({
        "zaman": now, "sira": nxt, "ad": item["ad"],
        "gonderi_id": post_id, "hikaye_idleri": story_ids, "sonuc": "BASARILI",
    })
    json.dump(state, open(state_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("Durum guncellendi. Siradaki set:", state["sonraki"])
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("HATA:", e, file=sys.stderr)
        sys.exit(1)
