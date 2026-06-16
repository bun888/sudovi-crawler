import requests
from bs4 import BeautifulSoup
import json
import os
import time

BASE = "https://odluke.sudovi.hr"

TARGET = "Zakon o zaštiti od nasilja u obitelji"

STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE, "r", encoding="utf-8"))
    return {"seen": []}

def save_state(state):
    json.dump(state, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

state = load_state()
seen = set(state["seen"])

new_ids = []
new_links = []

# 1–1000 stranica
for page in range(1, 11):

    url = f"{BASE}/Document/DisplayList?page={page}&sort=dat&zk={TARGET}"
    r = requests.get(url, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select("a.search-result")

    if not items:
        break

    for a in items:
        href = a["href"]
        full = BASE + href

        # extract ID iz URL-a
        doc_id = href.split("id=")[-1]

        if doc_id in seen:
            continue

        seen.add(doc_id)
        new_ids.append(doc_id)
        new_links.append(full)

    time.sleep(0.2)

# 2) ako ima novih → provjeri datum objave
results = []

for link in new_links:

    r = requests.get(link, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    pub = soup.select_one('[data-metadata-type="publication-date"] .metadata-content')

    date = pub.text.strip() if pub else "?"

    results.append({
        "link": link,
        "date": date
    })

    time.sleep(0.2)

# save state
state["seen"] = list(seen)
save_state(state)

# output
print("\nNEW RESULTS:\n")
for r in results:
    print(r["date"], r["link"])
