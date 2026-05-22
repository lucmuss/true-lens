# Szenario 01 – Captcha lösen und Profil suchen (anonymer Nutzer)

**Ziel:** Ein anonymer Besucher löst das Captcha und findet erfolgreich das Profil von Clara Schmidt.

**Vorbedingungen:**
- Datenbank enthält Kandidatin Clara Schmidt (via `seed_dev_data`)
- Browser hat keine aktive Session

---

## Schritte

### 1. Landing Page öffnen
- Navigiere zu `http://localhost:18087/`
- **Erwartung:** Seite zeigt Logo, Beschreibungstext, Statistik-Kacheln (Profile im System, Gesamtaufrufe) und ein Captcha-Bild.
- **Prüfe:** Kein Suchformular ist sichtbar. Das Suchfeld ist verborgen.

### 2. Captcha lösen
- Lies den angezeigten Code aus dem Captcha-Bild.
- Gib den Code in das Feld „Captcha Code" ein.
- Klicke „Prüfung starten".
- **Erwartung:** Meldung „Captcha erfolgreich." erscheint. Ein Link „Zum Dashboard" wird sichtbar.

### 3. Zum Dashboard wechseln
- Klicke „Zum Dashboard".
- **Erwartung:** Dashboard lädt. Login-Weiterleitung erscheint (da nicht eingeloggt). Gehe alternativ direkt zu `/dashboard/`.

### 4. Als Recruiter einloggen (falls nötig)
- Navigiere zu `/accounts/login/`
- E-Mail: `recruiter1@example.com`, Passwort: `Test1234!secure`
- **Erwartung:** Redirect zum Dashboard.

### 5. Suche starten – Schritt 1 Basisdaten
- Im Dashboard: Wähle Land `Germany` aus dem Dropdown.
- Wähle Provinz `Bayern`.
- Gib Vorname `Clara` ein.
- Wähle Geschlecht `Female`.
- Klicke „Treffer prüfen".
- **Erwartung:** Antwort zeigt „1 Treffer". Schaltflächen für Verifizierungsfall erscheinen.

### 6. Verifizierungsfall wählen – Geburtsdatum
- Klicke auf „Geburtsdatum + Stadt + Haarfarbe".
- **Erwartung:** Timer startet (sichtbarer Countdown). Eingabefeld für Geburtsdatum erscheint.

### 7. Geburtsdatum eingeben
- Gib `1990-03-04` ein.
- Klicke „Weiter".
- **Erwartung:** Nächstes Feld (Stadt) erscheint. Rückmeldung zeigt noch mögliche Treffer.

### 8. Stadt eingeben
- Tippe `Mun` – warte auf Autocomplete-Vorschlag.
- Wähle `Munich`.
- Klicke „Weiter".
- **Erwartung:** Haarfarbe-Dropdown erscheint.

### 9. Haarfarbe wählen
- Wähle `Braun` aus dem Dropdown.
- Klicke „Weiter".
- **Erwartung:** Profil erscheint: „Clara S*****t", Alter, Geschlecht, maskierte E-Mail/Telefon.

### 10. Profilinhalt prüfen
- **Prüfe:** Vorname ist vollständig sichtbar (`Clara`).
- **Prüfe:** Nachname zeigt nur ersten und letzten Buchstaben (`S*****t`).
- **Prüfe:** Alter ist korrekt (Jahrgang 1990 → ca. 35-36 Jahre).
- **Prüfe:** Attribut-Votes sind sichtbar (falls vorhanden).

---

**Ergebnis:** PASS wenn Profil korrekt maskiert angezeigt wird.
