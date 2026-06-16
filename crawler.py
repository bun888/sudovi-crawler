import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import time
import json
import os

BASE = "https://odluke.sudovi.hr"
KEYWORD = "Zakon o zaštiti od nasilja u obitelji"

# 🔥 tražimo JUČER
yesterday = date.today() - timedelta(days=1)
TARGET = f"{yesterday.day}.{yesterday.month}.{yesterday.year}."

STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE, "r", encoding="utf-8"))
    return {"seen": []}

def save_state(state):
    json.dump(state, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

state = load_state()
seen = set(state["seen"])

results = []

# 🔥 TEST: prvih 10 stranica (kasnije može 1000)
for page in range(1, 11):

    url = f"{BASE}/Document/DisplayList?page={page}&sort=dat&zk={KEYWORD}"
    r = requests.get(url, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select("a.search-result")

    for a in items:

        href = a["href"]
        doc_id = href.split("id=")[-1]

        if doc_id in seen:
            continue

        seen.add(doc_id)

        full_url = BASE + href

        try:
            r2 = requests.get(full_url, timeout=30)
            s2 = BeautifulSoup(r2.text, "html.parser")

            pub = s2.select_one('[data-metadata-type="publication-date"] .metadata-content')

            if pub:
                pub_date = pub.text.strip()

                # 🔥 FILTER: samo JUČER
                if pub_date == TARGET:
                    results.append({
                        "date": pub_date,
                        "link": full_url
                    })

        except Exception as e:
            print("error:", e)

        time.sleep(0.2)

    time.sleep(0.5)

# 💾 spremi state
state["seen"] = list(seen)
save_state(state)

# 💾 napiši results.txt
with open("results.txt", "w", encoding="utf-8") as f:
    for r in results:
        f.write(f"{r['date']} {r['link']}\n")

print("DONE")
print("Found:", len(results))
