import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://odluke.sudovi.hr/Document/DisplayList"
ZAGREB = ZoneInfo("Europe/Zagreb")

session = requests.Session()

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def load_state():
    try:
        with open("state.json", "r", encoding="utf-8") as f:
            return set(json.load(f).get("seen", []))
    except FileNotFoundError:
        return set()


def save_state(seen):
    with open("state.json", "w", encoding="utf-8") as f:
        json.dump(
            {"seen": sorted(seen)},
            f,
            ensure_ascii=False,
            indent=2,
        )


def make_results_file(found):
    today = datetime.now(ZAGREB).strftime("%Y-%m-%d")
    filename = f"results_{today}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Nove presude pronađene {today}\n\n")

        if not found:
            f.write("Nema novih presuda.\n")
        else:
            for url in found:
                f.write(f"- [{url}]({url})\n")

    return filename


def main():
    seen = load_state()
    found = []

    run_date = datetime.now(ZAGREB).strftime("%d.%m.%Y %H:%M:%S")

    print(f"RUN DATE: {run_date}")

    for page in range(1, 1001):
        print(f"PAGE {page}")

        params = {
            "page": page,
            "sort": "dat",
            "zk": "Zakon o zaštiti od nasilja u obitelji",
        }

        try:
            r = session.get(
                BASE_URL,
                params=params,
                headers=HEADERS,
                timeout=30,
            )

            r.raise_for_status()

        except Exception as e:
            print(f"ERROR PAGE {page}: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "/Document/View?id=" not in href:
                continue

            m = re.search(r"id=([0-9a-fA-F-]+)", href)

            if not m:
                continue

            doc_id = m.group(1)

            if doc_id in seen:
                continue

            url = f"https://odluke.sudovi.hr{href}"

            print(f"NEW: {url}")

            found.append(url)
            seen.add(doc_id)

    save_state(seen)

    result_file = make_results_file(found)

    print()
    print("DONE")
    print(f"FOUND: {len(found)}")
    print(f"RESULT FILE: {result_file}")


if __name__ == "__main__":
    main()
