# Szenario 04 – Admin-Dashboard und Moderation

**Ziel:** Der Admin prüft System-Übersicht, ausstehende Enrichment-Einreichungen und IP-Bans.

**Vorbedingungen:**
- Als `admin@example.com` eingeloggt (`Test1234!secure`)
- `seed_dev_data` wurde ausgeführt (hat Kandidaten und Votes)

---

## Schritte

### 1. Admin-Dashboard aufrufen
- Navigiere zu `/admin-overview/`
- **Erwartung:** Seite lädt ohne Fehler. Vier Statistik-Kacheln zeigen:
  - Kandidaten (> 0)
  - Recruiter (> 0)
  - Votes gesamt
  - Profil-Aufrufe

### 2. Credits & Einnahmen prüfen
- Scrolle zum Abschnitt „Credits & Einnahmen".
- **Erwartung:** Werte werden angezeigt (auch wenn 0 EUR).

### 3. Replikations-Knoten-Tabelle
- Scrolle zum Abschnitt „Replikations-Knoten".
- **Erwartung:** Tabelle erscheint (leer wenn keine Knoten, oder mit vorhandenen Einträgen).

### 4. Moderation Queue
- Scrolle zum Abschnitt „Moderation Queue".
- **Prüfe:** Zähler zeigt korrekte Anzahl ausstehender Einreichungen.
- Wenn Einreichungen vorhanden: Kandidat-Link klicken → Profil öffnet sich.

### 5. IP-Bans prüfen
- Scrolle zu „Aktive IP-Sperren".
- **Erwartung:** Tabelle mit IPs, Grund, Strikes und Ablaufzeit (oder Hinweis „keine aktiven Sperren").

### 6. Link zu Django Admin
- Klicke in der Sidebar auf „Django Admin".
- **Erwartung:** Django-Admin-Interface öffnet sich unter `/admin/`.

### 7. Zugriffskontrolle testen
- Öffne ein privates/anonymes Browser-Fenster.
- Navigiere direkt zu `/admin-overview/`.
- **Erwartung:** Redirect zur Login-Seite (kein Zugriff ohne Staff-Rolle).

### 8. Als normaler Recruiter einloggen und versuchen
- Login als `recruiter1@example.com`.
- Navigiere zu `/admin-overview/`.
- **Erwartung:** Zugriff verweigert (Redirect zu Login oder 403).

---

**Ergebnis:** PASS wenn Admin-Dashboard korrekte Daten zeigt und Zugriffsschutz funktioniert.
