#!/usr/bin/env python3

import csv
import io
import ipaddress
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


# Offizielles GERMA-Projekt auf OSF:
# https://osf.io/3bthj/
OSF_NODE_ID = "3bthj"

# Laut GERMA-Publikation enthält diese Datei die Liste der Websites.
SOURCE_FILENAME = "GERMA_websites.csv"

# Repository-Root bestimmen.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

# Von GitHub/AdGuard Home verwendete Ausgabedatei.
OUTPUT_FILE = REPOSITORY_ROOT / "germa-adguard.txt"

USER_AGENT = (
    "GERMA-for-AdGuard-Home/1.0 "
    "(https://github.com/Xilath1993/GERMA-for-AdGuard-Home)"
)

# Prüfung auf syntaktisch plausible DNS-Domainnamen.
DOMAIN_RE = re.compile(
    r"^(?=.{1,253}\.?$)"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.?$",
    re.IGNORECASE,
)


def request(url: str, accept: str | None = None) -> bytes:
    """
    Führt einen HTTP-GET-Request aus.
    """

    headers = {
        "User-Agent": USER_AGENT,
    }

    if accept:
        headers["Accept"] = accept

    req = Request(url, headers=headers)

    with urlopen(req, timeout=60) as response:
        return response.read()


def get_json(url: str) -> dict:
    """
    Ruft JSON von der OSF-API ab.
    """

    data = request(
        url,
        accept="application/json",
    )

    return json.loads(
        data.decode("utf-8")
    )


def related_href(item: dict) -> str | None:
    """
    Liefert bei einem OSF-Ordner den API-Link auf dessen Inhalt.
    """

    related = (
        item.get("relationships", {})
        .get("files", {})
        .get("links", {})
        .get("related")
    )

    if isinstance(related, str):
        return related

    if isinstance(related, dict):
        return related.get("href")

    return None


def iter_collection(url: str):
    """
    Iteriert über eine paginierte OSF-API-Collection.
    """

    while url:
        payload = get_json(url)

        for item in payload.get("data", []):
            yield item

        next_link = (
            payload.get("links", {})
            .get("next")
        )

        if isinstance(next_link, dict):
            url = next_link.get("href")
        else:
            url = next_link


def find_osf_file_download() -> str:
    """
    Durchsucht den OSF-Dateispeicher des GERMA-Projekts
    nach GERMA_websites.csv und gibt den Download-Link zurück.
    """

    start_url = (
        f"https://api.osf.io/v2/nodes/"
        f"{OSF_NODE_ID}/files/osfstorage/"
    )

    queue = [start_url]
    visited = set()

    while queue:
        collection_url = queue.pop(0)

        if collection_url in visited:
            continue

        visited.add(collection_url)

        for item in iter_collection(collection_url):
            attributes = item.get(
                "attributes",
                {},
            )

            name = attributes.get(
                "name",
                "",
            )

            kind = attributes.get(
                "kind",
                "",
            )

            # Gesuchte CSV-Datei gefunden.
            if (
                kind == "file"
                and name == SOURCE_FILENAME
            ):
                download_url = (
                    item.get("links", {})
                    .get("download")
                )

                if not download_url:
                    raise RuntimeError(
                        f"{SOURCE_FILENAME} wurde gefunden, "
                        "aber OSF liefert keinen Download-Link."
                    )

                return download_url

            # Unterordner rekursiv durchsuchen.
            if kind == "folder":
                child_url = related_href(item)

                if child_url:
                    queue.append(child_url)

    raise FileNotFoundError(
        f"{SOURCE_FILENAME} wurde im "
        f"OSF-Projekt {OSF_NODE_ID} nicht gefunden."
    )


def normalize_domain(value: str) -> str | None:
    """
    Normalisiert einen GERMA-Eintrag auf einen reinen Domainnamen.
    """

    value = value.strip().lower()

    if not value:
        return None

    # Sowohl vollständige URLs als auch nackte Hostnamen verarbeiten.
    parsed = urlsplit(
        value
        if "://" in value
        else f"//{value}"
    )

    host = parsed.hostname

    if not host:
        return None

    # Abschließenden Punkt entfernen.
    host = host.rstrip(".")

    # www.example.org -> example.org
    # Dadurch wird mit ||example.org^ auch die Hauptdomain erfasst.
    if host.startswith("www."):
        host = host[4:]

    # Internationale Domains in ASCII/Punycode überführen.
    try:
        host = (
            host.encode("idna")
            .decode("ascii")
        )
    except UnicodeError:
        return None

    # IP-Adressen sollen nicht als Domains in der Liste landen.
    try:
        ipaddress.ip_address(host)
        return None
    except ValueError:
        pass

    if not DOMAIN_RE.fullmatch(host):
        return None

    return host


def read_domains(csv_bytes: bytes) -> list[str]:
    """
    Liest ausschließlich die Spalte 'website'
    aus GERMA_websites.csv.
    """

    text = csv_bytes.decode(
        "utf-8-sig"
    )

    reader = csv.DictReader(
        io.StringIO(text)
    )

    if not reader.fieldnames:
        raise RuntimeError(
            "GERMA_websites.csv hat keine Kopfzeile."
        )

    # Spaltennamen robust gegen Groß-/Kleinschreibung
    # und überflüssige Leerzeichen behandeln.
    field_map = {
        name.strip().lower(): name
        for name in reader.fieldnames
        if name is not None
    }

    website_field = field_map.get(
        "website"
    )

    if website_field is None:
        raise RuntimeError(
            "Die erwartete Spalte 'website' fehlt "
            "in GERMA_websites.csv. "
            "Gefundene Spalten: "
            + ", ".join(reader.fieldnames)
        )

    domains = set()

    for row in reader:
        domain = normalize_domain(
            row.get(
                website_field,
                "",
            )
        )

        if domain:
            domains.add(domain)

    if not domains:
        raise RuntimeError(
            "Aus GERMA_websites.csv konnten "
            "keine gültigen Domains gelesen werden."
        )

    # Deterministische Reihenfolge:
    # dieselben Domains erzeugen immer dieselbe Datei.
    return sorted(domains)


def build_adguard_list(
    domains: list[str],
) -> str:
    """
    Wandelt die Domains in AdGuard-DNS-Regeln um.
    """

    header = [
        "! Title: GERMA for AdGuard Home",
        (
            "! Description: AdGuard Home DNS blocklist "
            "generated from the GERMA corpus."
        ),
        "! Source project: https://osf.io/3bthj/",
        "! Source file: GERMA_websites.csv",
        (
            "! Paper: "
            "https://doi.org/10.1515/lingvan-2024-0064"
        ),
        "! Format: AdGuard DNS filtering rules",
        (
            "! Generated automatically. "
            "Do not edit this file manually."
        ),
        "!",
    ]

    rules = [
        f"||{domain}^"
        for domain in domains
    ]

    return (
        "\n".join(
            header + rules
        )
        + "\n"
    )


def main() -> int:
    """
    Hauptprogramm.
    """

    print(
        f"Suche {SOURCE_FILENAME} "
        "im offiziellen GERMA-OSF-Projekt ..."
    )

    download_url = (
        find_osf_file_download()
    )

    print(
        "Lade GERMA-Domainliste herunter ..."
    )

    csv_bytes = request(
        download_url
    )

    domains = read_domains(
        csv_bytes
    )

    output = build_adguard_list(
        domains
    )

    OUTPUT_FILE.write_text(
        output,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"{len(domains)} Domains nach "
        f"{OUTPUT_FILE.name} geschrieben."
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )

    except Exception as exc:
        print(
            f"FEHLER: {exc}",
            file=sys.stderr,
        )

        raise SystemExit(1)
