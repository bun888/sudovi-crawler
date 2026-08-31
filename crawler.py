```python
import json
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://odluke.sudovi.hr/Document/DisplayList"
ZAGREB = ZoneInfo("Europe/Zagreb")

STATE_FILE = "state.json"

MAX_PAGES = 1000

# Koliko puta pokušati dohvatiti jednu stranicu prije nego je proglasimo neuspješnom
MAX_RETRIES = 3

# Pauza između pokušaja
RETRY_DELAY = 5

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return set(data.get("seen", []))

    return set()


def save_state(seen):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "seen": sorted(seen)
            },
            f,
            ensure_ascii=False,
            indent=2
        )


def get_page(page):
    """
    Pokušava dohvatiti jednu stranicu više puta.
    Vraća BeautifulSoup objekt ako uspije.
    Ako svi pokušaji ne uspiju, vraća None i grešku.
    """

    params = {
        "page": page,
        "sort": "dat",
        "zk": "Zakon o zaštiti od nasilja u obitelji"
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            r = session.get(
                BASE_URL,
                params=params,
                headers=HEADERS,
                timeout=30
            )

            r.raise_for_status()

            return BeautifulSoup(r.text, "html.parser"), None

        except Exception as e:

            last_error = e

            print(
                f"PAGE {page}: pokušaj "
                f"{attempt}/{MAX_RETRIES} nije uspio: {e}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    return None, last_error


def make_results_file(found, errors, run_time):
    """
    Sprema rezultate u jedinstvenu datoteku.
    U imenu je i datum i vrijeme pokretanja kako se datoteke
    nikada ne bi međusobno prepisale.
    """

    filename = run_time.strftime(
        "results_%Y-%m-%d_%H-%M-%S.md"
    )

    with open(filename, "w", encoding="utf-8") as f:

        f.write(
            "# Crawl "
            + run_time.strftime("%d.%m.%Y %H:%M:%S")
            + "\n\n"
        )

        if errors:

            f.write("## ⚠️ NEPOTPUN CRAWL\n\n")

            f.write(
                f"Uspješno dohvaćenih stranica: "
                f"{MAX_PAGES - len(errors)}\n"
            )

            f.write(
                f"Stranica s greškom: {len(errors)}\n"
            )

            f.write(
                f"Pronađenih novih UUID-ova: "
                f"{len(found)}\n\n"
            )

            f.write("### Greške\n\n")

            for page, error in errors:
                f.write(
                    f"- PAGE {page}: {error}\n"
                )

            f.write("\n")

        else:

            f.write("## ✅ CRAWL USPJEŠAN\n\n")

            f.write(
                f"Provjereno stranica: {MAX_PAGES}\n"
            )

            f.write(
                f"Pronađenih novih UUID-ova: "
                f"{len(found)}\n\n"
            )

        if found:

            f.write("## Nove presude\n\n")

            for url in found:
                f.write(
                    f"- [{url}]({url})\n"
                )

        else:

            f.write("Nema novih presuda.\n")

    return filename


def main():

    run_time = datetime.now(ZAGREB)

    print(
        "RUN DATE:",
        run_time.strftime("%d.%m.%Y %H:%M:%S")
    )

    seen = load_state()

    found = []
    errors = []

    for page in range(1, MAX_PAGES + 1):

        print(f"PAGE {page}")

        soup, error = get_page(page)

        if soup is None:

            errors.append(
                (page, str(error))
            )

            continue

        items = soup.find_all(
            "a",
            href=True
        )

        for a in items:

            href = a["href"]

            # Prihvati samo linkove prema dokumentima
            if "/Document/View?id=" not in href:
                continue

            match = re.search(
                r"id=([0-9a-fA-F-]+)",
                href
            )

            if not match:
                continue

            doc_id = match.group(1)

            # Već poznat UUID -> preskoči
            if doc_id in seen:
                continue

            full_url = f"https://odluke.sudovi.hr{href}"

            print(
                f"NEW: {full_url}"
            )

            # Novi UUID odmah ide u rezultat
            found.append(full_url)

            # I odmah ga označavamo kao viđen
            seen.add(doc_id)

        # Mala pauza između stranica
        time.sleep(0.05)

    # State spremamo samo s UUID-ovima koje smo stvarno vidjeli
    save_state(seen)

    result_file = make_results_file(
        found,
        errors,
        run_time
    )

    print()
    print("DONE")
    print("FOUND:", len(found))
    print("PAGE ERRORS:", len(errors))
    print("RESULT FILE:", result_file)

    # Ako je bilo grešaka, workflow će završiti kao failed.
    # To omogućuje da jasno vidiš da crawl nije bio potpun.
    if errors:
        raise RuntimeError(
            f"Crawl nije bio potpun. "
            f"Neuspješno dohvaćenih stranica: {len(errors)}"
        )


if __name__ == "__main__":
    import os
    main()
```
