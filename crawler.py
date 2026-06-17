import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time
import json
import os

BASE = "https://odluke.sudovi.hr"
KEYWORD = "Zakon o zaštiti od nasilja u obitelji"

STATE_FILE = "state.json"

session = requests.Session()

# Vrijeme pokretanja crawlera (samo jednom!)
RUN_DATE = datetime.now(ZoneInfo("Europe/Zagreb"))

# Jučerašnji datum u odnosu na vrijeme pokretanja
TARGET = (
    RUN_DATE - timedelta(days=1)
).strftime("%-d.%-m.%Y")

# Datoteka rezultata vezana uz datum pokretanja
RESULT_FILE = RUN_DATE.strftime("results_%Y-%m-%d.md")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {"seen": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2
        )


state = load_state()
seen = set(state["seen"])

results = []

print("RUN DATE:", RUN_DATE.strftime("%d.%m.%Y %H:%M:%S"))
print("TARGET DATE:", TARGET)

for page in range(1, 1001):

    print(f"PAGE {page}")

    url = (
        f"{BASE}/Document/DisplayList"
        f"?page={page}"
        f"&sort=dat"
        f"&zk={KEYWORD}"
    )

    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()

    except Exception as e:
        print("PAGE ERROR:", e)
        continue

    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select("a.search-result")

    if not items:
        print("NO MORE RESULTS")
        break

    for a in items:

        try:
            href = a["href"]

            if "id=" not in href:
                continue

            doc_id = href.split("id=")[-1]

            # već viđeno -> ne otvaraj presudu
            if doc_id in seen:
                continue

            full_url = BASE + href

            try:
                r2 = session.get(full_url, timeout=30)
                r2.raise_for_status()

                s2 = BeautifulSoup(r2.text, "html.parser")

                pub = s2.select_one(
                    '[data-metadata-type="publication-date"] .metadata-content'
                )

                pub_date = pub.text.strip() if pub else ""

                print("NEW:", pub_date, full_url)

                if TARGET.replace(".", "") in pub_date.replace(".", ""):

                    results.append({
                        "date": pub_date,
                        "link": full_url
                    })

                    print("FOUND:", full_url)

                # spremi kao viđeno tek nakon uspješnog čitanja
                seen.add(doc_id)

            except Exception as e:
                print("DOC ERROR:", e)

            time.sleep(0.05)

        except Exception as e:
            print("ITEM ERROR:", e)

    time.sleep(0.05)

state["seen"] = sorted(seen)
save_state(state)

with open(RESULT_FILE, "w", encoding="utf-8") as f:

    f.write(f"# Presude objavljene {TARGET}\n\n")

    if results:
        for item in results:
            f.write(f"- {item['link']}\n")
    else:
        f.write("Nema novih presuda.\n")

print()
print("DONE")
print("FOUND:", len(results))
print("RESULT FILE:", RESULT_FILE)
