# GERMA for AdGuard Home

Dieses Repository stellt die Domainliste des wissenschaftlichen **GERMA**-Datensatzes als DNS-Sperrliste für **AdGuard Home** bereit.

## Was ist GERMA?

**GERMA** steht für **GErman coRpus of MisinformAtion** und ist ein wissenschaftlicher Datensatz von Fabio Carrella und Alessandro Miani.

Der Datensatz umfasst deutschsprachige Nachrichtenquellen, die auf Quellenebene anhand externer Bewertungen als **unzuverlässig („untrustworthy“) eingestuft** wurden. Dabei spielen unter anderem Kriterien wie Faktizität, Glaubwürdigkeit, Transparenz und Bias eine Rolle.

Wichtig: GERMA bewertet **Websites bzw. Quellen**, nicht jeden einzelnen dort veröffentlichten Artikel. Die Aufnahme einer Domain bedeutet daher nicht, dass jeder einzelne Inhalt dieser Website falsch ist.

## Welche Websites werden blockiert?

Die Liste blockiert die Domains, die im GERMA-Datensatz als unzuverlässige deutschsprachige Nachrichtenquellen enthalten sind.

Dazu zählen insbesondere Websites, auf denen unter anderem

- Desinformation oder nachweislich falsche Behauptungen,
- Verschwörungserzählungen,
- stark verzerrte oder irreführende Nachrichteninhalte,
- pseudowissenschaftliche bzw. medizinisch fragwürdige Inhalte,
- propagandistische oder besonders einseitige Berichterstattung

veröffentlicht werden können.

Die Sperrung erfolgt auf **Domain-Ebene**. Dadurch werden auch Subdomains der jeweiligen Website erfasst.

## AdGuard-Home-Liste

Die fertige Sperrliste kann direkt in AdGuard Home eingebunden werden:

```text
https://raw.githubusercontent.com/Xilath1993/GERMA-for-AdGuard-Home/main/germa-adguard.txt
```

## Quellen

GERMA-Forschungsarbeit:

**Fabio Carrella & Alessandro Miani – GERMA: a comprehensive corpus of untrustworthy German news**

https://doi.org/10.1515/lingvan-2024-0064

Offizieller GERMA-Datensatz:

https://osf.io/3bthj/

---

Dieses Repository nimmt keine eigene Bewertung der aufgeführten Websites vor, sondern stellt ausschließlich die im GERMA-Datensatz enthaltenen Domains in einem für AdGuard Home geeigneten Format bereit.
