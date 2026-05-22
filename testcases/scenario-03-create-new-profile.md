# Szenario 03 – Neues Profil anlegen

**Ziel:** Ein eingeloggter Recruiter sucht eine Person, findet keinen Treffer und legt ein neues Profil an.

**Vorbedingungen:**
- Recruiter `recruiter1@example.com` eingeloggt
- Kandidatin „Miriam" existiert noch NICHT in der Datenbank

---

## Schritte

### 1. Suche mit 0 Treffern auslösen
- Dashboard → Land: `Germany`, Provinz: `Sachsen`, Vorname: `Miriam`, Geschlecht: `Female`
- Klicke „Treffer prüfen".
- **Erwartung:** Antwort zeigt „0 Treffer". Text „Kein Treffer. Lege ein neues Profil an" erscheint.
- **Prüfe:** Button „Neues Profil anlegen" ist sichtbar.

### 2. Profil-Formular öffnen
- Klicke „Neues Profil anlegen".
- **Erwartung:** Formularfelder erscheinen: Nachname, Geburtsdatum, Haarfarbe, Stadt, E-Mail, Telefon.

### 3. Pflichtfelder ausfüllen
- Nachname: `Bergmann`
- Stadt: `Chemnitz`
- Optional: Geburtsdatum `1997-08-20`, Haarfarbe `Blond`

### 4. Profil erstellen
- Klicke „Profil erstellen".
- **Erwartung:** Meldung „Profil erstellt (ID X). 2 Credits gutgeschrieben."
- Credits-Anzeige im Dashboard steigt um 2.

### 5. Profil in Datenbank verifizieren
- Navigiere zu `/admin-overview/` (als admin@example.com).
- **Erwartung:** Kandidaten-Zähler ist um 1 gestiegen.

### 6. Erneute Suche nach Miriam Bergmann
- Dashboard → Land: `Germany`, Provinz: `Sachsen`, Vorname: `Miriam`, Geschlecht: `Female`
- **Erwartung:** Jetzt 1 Treffer. Suche kann fortgesetzt werden.

### 7. Wochenlimit testen
- Versuche ein weiteres neues Profil anzulegen (Schritt 1–4 mit anderem Namen).
- **Erwartung:** Fehlermeldung „Weekly candidate creation limit reached".

---

**Ergebnis:** PASS wenn Profil erstellt wird, Credits korrekt vergeben werden und Wochenlimit greift.
