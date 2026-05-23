from __future__ import annotations

import unicodedata

# ── Country name → ISO-2 for city autocomplete ───────────────────────────────
COUNTRY_TO_ISO2: dict[str, str] = {
    "germany": "de", "deutschland": "de",
    "austria": "at", "oesterreich": "at", "österreich": "at",
    "switzerland": "ch", "schweiz": "ch",
    "netherlands": "nl", "niederlande": "nl",
    "belgium": "be", "belgien": "be",
    "france": "fr", "frankreich": "fr",
    "spain": "es", "spanien": "es",
    "italy": "it", "italien": "it",
    "poland": "pl", "polen": "pl",
    "united states": "us", "usa": "us",
    "united kingdom": "gb", "uk": "gb", "great britain": "gb",
    "canada": "ca", "kanada": "ca",
    "czechia": "cz", "czech republic": "cz",
    "denmark": "dk", "dänemark": "dk",
    "sweden": "se", "schweden": "se",
    "norway": "no", "norwegen": "no",
    "finland": "fi", "finnland": "fi",
    "portugal": "pt",
    "hungary": "hu", "ungarn": "hu",
    "romania": "ro", "rumänien": "ro",
    "croatia": "hr", "kroatien": "hr",
    "greece": "gr", "griechenland": "gr",
    "turkey": "tr", "türkei": "tr", "türkiye": "tr",
    "russia": "ru", "russland": "ru",
    "ukraine": "ua",
    "japan": "jp",
    "china": "cn",
    "south korea": "kr",
    "india": "in",
    "australia": "au",
    "new zealand": "nz",
    "brazil": "br", "brasilien": "br",
    "mexico": "mx",
    "argentina": "ar",
}

# ── Full country list (from Agora Chat countries.py) ─────────────────────────
COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina",
    "Armenia", "Australia", "Austria", "Azerbaijan", "Bahrain", "Bangladesh",
    "Belarus", "Belgium", "Belize", "Benin", "Bolivia", "Bosnia and Herzegovina",
    "Botswana", "Brazil", "Brunei", "Bulgaria", "Burundi", "Cambodia",
    "Cameroon", "Canada", "Chile", "China", "Colombia", "Costa Rica",
    "Croatia", "Cuba", "Cyprus", "Czechia", "Denmark", "Dominican Republic",
    "Ecuador", "Egypt", "El Salvador", "Estonia", "Ethiopia", "Finland",
    "France", "Georgia", "Germany", "Ghana", "Greece", "Guatemala",
    "Honduras", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia",
    "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan",
    "Jordan", "Kazakhstan", "Kenya", "Kosovo", "Kuwait", "Kyrgyzstan",
    "Latvia", "Lebanon", "Libya", "Liechtenstein", "Lithuania", "Luxembourg",
    "Malaysia", "Malta", "Mexico", "Moldova", "Monaco", "Mongolia",
    "Montenegro", "Morocco", "Myanmar", "Nepal", "Netherlands", "New Zealand",
    "Nicaragua", "Nigeria", "North Macedonia", "Norway", "Oman", "Pakistan",
    "Palestine", "Panama", "Paraguay", "Peru", "Philippines", "Poland",
    "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saudi Arabia",
    "Senegal", "Serbia", "Singapore", "Slovakia", "Slovenia", "Somalia",
    "South Africa", "South Korea", "Spain", "Sri Lanka", "Sudan", "Sweden",
    "Switzerland", "Syria", "Taiwan", "Tanzania", "Thailand", "Togo",
    "Trinidad and Tobago", "Tunisia", "Türkiye", "Uganda", "Ukraine",
    "United Arab Emirates", "United Kingdom", "United States", "Uruguay",
    "Uzbekistan", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe",
]

_COUNTRY_ALIASES: dict[str, list[str]] = {
    "Germany": ["Deutschland", "DE", "GER"],
    "Austria": ["Österreich", "Oesterreich", "AUT"],
    "Switzerland": ["Schweiz", "CH", "SUI"],
    "United States": ["USA", "US", "United States of America"],
    "United Kingdom": ["UK", "GB", "Great Britain", "England", "Britain"],
    "Czechia": ["Czech Republic"],
    "Türkiye": ["Turkey"],
    "South Korea": ["Korea"],
    "Netherlands": ["Holland", "Niederlande"],
    "Belgium": ["Belgien"],
    "France": ["Frankreich"],
    "Italy": ["Italien"],
    "Spain": ["Spanien"],
    "Poland": ["Polen"],
    "Canada": ["Kanada"],
    "Russia": ["Russland"],
    "Denmark": ["Dänemark"],
    "Sweden": ["Schweden"],
    "Norway": ["Norwegen"],
    "Finland": ["Finnland"],
    "Hungary": ["Ungarn"],
    "Romania": ["Rumänien"],
    "Croatia": ["Kroatien"],
    "Greece": ["Griechenland"],
}

_COUNTRY_PRIORITY: dict[str, int] = {
    "Germany": 0, "Austria": 1, "Switzerland": 2,
    "United States": 3, "United Kingdom": 4, "France": 5,
    "Spain": 6, "Italy": 7, "Netherlands": 8, "Canada": 9,
}


def _norm(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").casefold().split()
    )


# Build search index: normalized alias → canonical name
_COUNTRY_INDEX: dict[str, str] = {}
for _c in COUNTRIES:
    _COUNTRY_INDEX[_norm(_c)] = _c
for _c, _aliases in _COUNTRY_ALIASES.items():
    for _a in _aliases:
        _COUNTRY_INDEX[_norm(_a)] = _c


def country_suggestions(query: str, limit: int = 8) -> list[dict[str, str]]:
    needle = _norm(query)
    if not needle:
        top = sorted(COUNTRIES, key=lambda c: _COUNTRY_PRIORITY.get(c, 99))
        return [{"label": c, "value": c} for c in top[:limit]]

    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for country in COUNTRIES:
        aliases = [country] + _COUNTRY_ALIASES.get(country, [])
        for alias in aliases:
            if not _norm(alias).startswith(needle):
                continue
            if country in seen:
                continue
            seen.add(country)
            results.append({"label": alias if alias != country else country, "value": country})

    results.sort(key=lambda item: (
        0 if _norm(item["label"]) == needle else 1,
        _COUNTRY_PRIORITY.get(item["value"], 99),
        0 if item["label"] == item["value"] else 1,
        len(item["label"]),
    ))
    return results[:limit]


# ── Regions by country ────────────────────────────────────────────────────────
REGIONS_BY_COUNTRY: dict[str, list[str]] = {
    "Germany": [
        "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen",
        "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen",
        "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen",
        "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen",
    ],
    "Austria": [
        "Burgenland", "Kärnten", "Niederösterreich", "Oberösterreich",
        "Salzburg", "Steiermark", "Tirol", "Vorarlberg", "Wien",
    ],
    "Switzerland": [
        "Aargau", "Appenzell Ausserrhoden", "Appenzell Innerrhoden",
        "Basel-Landschaft", "Basel-Stadt", "Bern", "Fribourg", "Genf",
        "Glarus", "Graubünden", "Jura", "Luzern", "Neuenburg",
        "Nidwalden", "Obwalden", "Schaffhausen", "Schwyz", "Solothurn",
        "St. Gallen", "Tessin", "Thurgau", "Uri", "Waadt", "Wallis",
        "Zug", "Zürich",
    ],
    "Netherlands": [
        "Drenthe", "Flevoland", "Friesland", "Gelderland", "Groningen",
        "Limburg", "Noord-Brabant", "Noord-Holland", "Overijssel",
        "Utrecht", "Zeeland", "Zuid-Holland",
    ],
    "Belgium": [
        "Antwerpen", "Brüssel", "Flämisch-Brabant", "Hennegau", "Limburg",
        "Lüttich", "Luxemburg", "Namur", "Ostflandern", "Wallonisch-Brabant",
        "Westflandern",
    ],
    "France": [
        "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne",
        "Centre-Val de Loire", "Grand-Est", "Hauts-de-France",
        "Île-de-France", "Normandie", "Nouvelle-Aquitaine", "Occitanie",
        "Pays-de-la-Loire", "Provence-Alpes-Côte d'Azur",
        "Korsika", "Guadeloupe", "Martinique", "Réunion",
    ],
    "Spain": [
        "Andalusien", "Aragonien", "Asturien", "Balearen", "Baskenland",
        "Extremadura", "Galicien", "Kanarische Inseln", "Kantabrien",
        "Kastilien-La Mancha", "Kastilien-León", "Katalonien", "La Rioja",
        "Madrid", "Murcia", "Navarra", "Valencia",
    ],
    "Italy": [
        "Abruzzen", "Aostatals", "Apulien", "Basilikata", "Emilia-Romagna",
        "Friaul-Julisch Venetien", "Kalabrien", "Kampanien", "Ligurien",
        "Lombardei", "Marken", "Molise", "Piemont", "Sardinien", "Sizilien",
        "Südtirol", "Toskana", "Trentino", "Umbrien", "Venetien",
    ],
    "Poland": [
        "Großpolen", "Heiligkreuz", "Karpatenvorland", "Kujawien-Pommern",
        "Lebus", "Lodz", "Lublin", "Masowien", "Masuren-Ermland",
        "Niederschlesien", "Oppeln", "Pommern", "Schlesien", "Silesia",
        "Westpommern",
    ],
    "United Kingdom": [
        "England", "Nordirland", "Schottland", "Wales",
    ],
    "United States": [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
        "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
        "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
        "New Hampshire", "New Jersey", "New Mexico", "New York",
        "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
        "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming",
    ],
    "Canada": [
        "Alberta", "British Columbia", "Manitoba", "New Brunswick",
        "Newfoundland and Labrador", "Nova Scotia", "Ontario",
        "Prince Edward Island", "Quebec", "Saskatchewan",
    ],
    "Czechia": [
        "Böhmen", "Mähren", "Mährisch-Schlesien", "Mittelböhmen",
        "Nordböhmen", "Nordmähren", "Ostböhmen", "Prag",
        "Südböhmen", "Südmähren", "Westböhmen",
    ],
    "Denmark": [
        "Hauptstadtregion", "Mitteljütland", "Nordjütland",
        "Seeland", "Süddänemark",
    ],
    "Sweden": [
        "Blekinge", "Dalarna", "Gävleborg", "Gotland", "Halland",
        "Jämtland", "Jönköping", "Kalmar", "Kronoberg", "Norrbotten",
        "Örebro", "Östergötland", "Skåne", "Södermanland", "Stockholm",
        "Uppsala", "Värmland", "Västerbotten", "Västernorrland",
        "Västmanland", "Västra Götaland",
    ],
    "Norway": [
        "Agder", "Innlandet", "Møre og Romsdal", "Nordland",
        "Oslo", "Rogaland", "Troms og Finnmark", "Trøndelag",
        "Vestfold og Telemark", "Vestland", "Viken",
    ],
    "Finland": [
        "Åland", "Birkaland", "Egentliga Finland", "Kajanaland",
        "Kymmenedalen", "Lappland", "Mellersta Finland", "Norra Karelen",
        "Norra Savolax", "Österbotten", "Päijänne-Tavastland",
        "Satakunta", "Södra Karelen", "Södra Savolax", "Tavastland",
        "Uusimaa",
    ],
    "Portugal": [
        "Alentejo", "Algarve", "Azoren", "Centro", "Lisboa",
        "Madeira", "Norte",
    ],
    "Hungary": [
        "Bács-Kiskun", "Baranya", "Békés", "Borsod-Abaúj-Zemplén",
        "Budapest", "Csongrád-Csanád", "Fejér", "Győr-Moson-Sopron",
        "Hajdú-Bihar", "Heves", "Jász-Nagykun-Szolnok", "Komárom-Esztergom",
        "Nógrád", "Pest", "Somogy", "Szabolcs-Szatmár-Bereg",
        "Tolna", "Vas", "Veszprém", "Zala",
    ],
    "Romania": [
        "Alba", "Arad", "Argeș", "Bacău", "Bihor", "Bistrița-Năsăud",
        "Botoșani", "Brăila", "Brașov", "București", "Buzău", "Călărași",
        "Caraș-Severin", "Cluj", "Constanța", "Covasna", "Dâmbovița",
        "Dolj", "Galați", "Giurgiu", "Gorj", "Harghita", "Hunedoara",
        "Ialomița", "Iași", "Ilfov", "Maramureș", "Mehedinți", "Mureș",
        "Neamț", "Olt", "Prahova", "Satu Mare", "Sălaj", "Sibiu",
        "Suceava", "Teleorman", "Timiș", "Tulcea", "Vâlcea", "Vaslui", "Vrancea",
    ],
    "Greece": [
        "Attika", "Epirus", "Ionische Inseln", "Kreta", "Makedonien",
        "Peloponnes", "Thessalien", "Thrakien", "Ägäis",
    ],
    "Turkey": [
        "Adana", "Ankara", "Antalya", "Bursa", "Eskişehir",
        "Gaziantep", "İstanbul", "İzmir", "Kayseri", "Konya",
        "Mersin", "Samsun", "Trabzon",
    ],
    "Japan": [
        "Aichi", "Chiba", "Fukuoka", "Hokkaido", "Hyōgo", "Kanagawa",
        "Kyōto", "Ōsaka", "Saitama", "Tōkyō",
    ],
    "China": [
        "Beijing", "Chongqing", "Fujian", "Guangdong", "Hebei",
        "Heilongjiang", "Henan", "Hubei", "Hunan", "Jiangsu",
        "Liaoning", "Shanghai", "Shandong", "Shaanxi", "Sichuan",
        "Tianjin", "Yunnan", "Zhejiang",
    ],
    "Australia": [
        "Australian Capital Territory", "New South Wales", "Northern Territory",
        "Queensland", "South Australia", "Tasmania", "Victoria",
        "Western Australia",
    ],
}
