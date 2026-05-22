# Szenario 02 – Registrierung und Kategorien-Vote

**Ziel:** Ein neuer Recruiter registriert sich, verifiziert die E-Mail und gibt für eine gefundene Person einen Vote ab.

**Vorbedingungen:**
- E-Mail-Delivery-Mode auf `console` oder `file` (Ausgabe lesbar)
- Kandidat Max Mueller existiert (via `seed_dev_data`)

---

## Schritte

### 1. Registrierung starten
- Navigiere zu `/accounts/signup/`
- Gib E-Mail `newrecruiter@test.local` und ein sicheres Passwort (min. 12 Zeichen, Sonderzeichen) ein.
- Klicke „Registrieren".
- **Erwartung:** Hinweis, dass eine Bestätigungs-E-Mail gesendet wurde.

### 2. E-Mail-Link öffnen
- Lese die gesendete E-Mail (Konsole oder `/tmp/mail/`).
- Klicke den Bestätigungslink.
- **Erwartung:** Seite zur Sicherheitsverifikation öffnet sich. Captcha und Eingabefeld für 6-stelligen Code werden angezeigt.

### 3. Sicherheitsverifikation
- Löse das Captcha.
- Gib den 6-stelligen Code aus der E-Mail ein.
- Klicke „Bestätigen".
- **Erwartung:** Meldung „Verifikation erfolgreich". Redirect zur Login-Seite.

### 4. Einloggen
- E-Mail und Passwort eingeben.
- **Erwartung:** Dashboard erscheint. Credits-Anzeige zeigt `0 Credits`.

### 5. Profil suchen (Max Mueller, Berlin)
- Land: `Germany`, Provinz: `Berlin`, Vorname: `Max`, Geschlecht: `Male`
- Klicke „Treffer prüfen".
- Wähle Verifizierungsfall „Nachname + Stadt".
- Nachname: `Mueller` → Weiter.
- Stadt: `Berlin` → Weiter.
- **Erwartung:** Profil von Max Mueller erscheint.

### 6. Vote abgeben
- Scrolle zu „Kategorien voten (max. 3)".
- Setze 2 Haken (z.B. „Zuverlässig" und „Klug").
- Klicke „Vote absenden".
- **Erwartung:** Meldung „Vote gespeichert." Credits steigen um 1 (Reward für Voting).

### 7. Doppelter Vote verhindern
- Klicke erneut „Vote absenden" mit denselben oder anderen Kategorien.
- **Erwartung:** Fehlermeldung „Recruiter already voted this candidate".

### 8. Vote-Historie prüfen
- Klicke in der Sidebar auf „Votes" → navigiert zu `/votes/`
- **Erwartung:** Tabelle zeigt den abgegebenen Vote mit Datum, Kandidat, Kategorie.

---

**Ergebnis:** PASS wenn Vote korrekt gespeichert und Doppel-Vote abgelehnt wird.
