import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

URL = (
    "https://odluke.sudovi.hr/Document/DisplayList"
    "?sort=dat&zk=Zakon%20o%20za%C5%A1titi%20od%20nasilja%20u%20obitelji"
)

ZAGREB = ZoneInfo("Europe/Zagreb")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def main():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()

    html = r.text

    m = re.search(
        r'Ukupno objavljenih odluka:\s*<span[^>]*>([\d\.]+)</span>',
        html,
        re.IGNORECASE | re.DOTALL,
    )

    if not m:
        print("Broj odluka nije pronađen.")
        return

    total = m.group(1)

    timestamp = datetime.now(ZAGREB).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with open(
        "decision_count_log.txt",
        "a",
        encoding="utf-8",
    ) as f:
        f.write(f"{timestamp} | {total}\n")

    print(f"{timestamp} | {total}")


if __name__ == "__main__":
    main()
