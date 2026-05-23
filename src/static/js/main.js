/* TrueLens — app.js
 * Loaded before Alpine (no defer) so all functions are available at Alpine init time.
 */

/* ── HTMX: attach CSRF + gate token to every request ── */
document.addEventListener("DOMContentLoaded", function () {
  document.body.addEventListener("htmx:configRequest", function (event) {
    const token = document.querySelector("[name=csrfmiddlewaretoken]");
    if (token) event.detail.headers["X-CSRFToken"] = token.value;
    const gate = localStorage.getItem("tl_js_gate_token");
    if (gate) event.detail.headers["X-JS-Gate"] = gate;
  });
});

/* ── Captcha (image-based, lepture/captcha) ── */
function captchaFlow() {
  return {
    captchaId: "",
    captchaUrl: "",
    code: "",
    message: "",
    verified: false,
    gateToken: "",
    captchaLoading: false,
    verifying: false,
    loadError: "",
    async init() {
      const savedToken = localStorage.getItem("tl_js_gate_token");
      if (savedToken) {
        try {
          const res = await fetch("/api/security/gate/check", {
            headers: { "X-JS-Gate": savedToken, "X-Requested-With": "XMLHttpRequest" },
          });
          const data = await res.json();
          if (data.valid) {
            this.verified = true;
            this.gateToken = savedToken;
            return;
          }
        } catch (_) { /* fall through to captcha */ }
      }
      await this.loadCaptcha();
    },
    async loadCaptcha() {
      this.captchaLoading = true;
      this.captchaUrl = "";
      this.loadError = "";
      this.code = "";
      this.message = "";
      try {
        const res = await fetch("/api/security/captcha/start", {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        if (!data.ok) {
          this.loadError = data.error || "Captcha konnte nicht geladen werden.";
          return;
        }
        this.captchaId = data.captcha_id;
        this.captchaUrl = data.image_url;
      } catch (e) {
        this.loadError = "Captcha konnte nicht geladen werden. Bitte erneut versuchen.";
      } finally {
        this.captchaLoading = false;
      }
    },
    async verify() {
      if (!this.code.trim() || this.verifying) return;
      this.verifying = true;
      this.message = "";
      try {
        const res = await fetch("/api/security/captcha/verify", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({ captcha_id: this.captchaId, code: this.code }),
        });
        const data = await res.json();
        if (data.ok) {
          this.verified = true;
          this.gateToken = data.js_gate_token || "";
          if (data.js_gate_token) {
            localStorage.setItem("tl_js_gate_token", data.js_gate_token);
          }
        } else {
          this.message = data.error || "Prüfung fehlgeschlagen.";
          await this.loadCaptcha();
        }
      } catch (e) {
        this.message = "Verbindungsfehler. Bitte Seite neu laden.";
      } finally {
        this.verifying = false;
      }
    },
  };
}

/* ── Search flow ── */
function searchFlow(config) {
  return {
    loading: false,
    message: "",
    country: "",
    region: "",
    first_name: "",
    gender: "female",
    candidateCount: null,
    sessionToken: "",
    selectedCase: "",
    caseIndex: 0,
    currentField: "",
    stepValue: "",
    currentStepNumber: 2,
    stepMessage: "",
    stepTimeout: config.stepTimeout,
    stepTimer: config.stepTimeout,
    timerHandle: null,
    profile: null,
    selectedAttributes: [],
    anonymousVote: false,
    attributes: config.attributes,
    hairColors: config.hairColors,
    countrySuggestions: [],
    regionSuggestions: [],
    citySuggestions: [],
    firstNameSuggestions: [],
    showCountrySuggestions: false,
    showRegionSuggestions: false,
    showFirstNameSuggestions: false,
    showCreateForm: false,
    createMessage: "",
    newProfile: { last_name: "", birth_date: "", hair_color: "", city: "", email: "", phone: "" },
    cases: [
      { key: "birthdate", label: "Geburtsdatum + Stadt + Haarfarbe", fields: ["birth_date", "city", "hair_color"] },
      { key: "email", label: "E-Mail + Stadt", fields: ["email", "city"] },
      { key: "phone", label: "Telefon + Stadt", fields: ["phone", "city"] },
      { key: "age", label: "Alter + Stadt", fields: ["age", "city"] },
      { key: "social", label: "Dating-Link + Stadt + Alter", fields: ["social_url", "city", "age"] },
      { key: "lastname", label: "Nachname + Stadt", fields: ["last_name", "city"] },
    ],
    init() {
      this.loadCountries();
    },
    stepPillClass(stepNumber) {
      const state = this.currentUiStep();
      if (state === stepNumber) return "ow-step-pill active";
      if (state > stepNumber) return "ow-step-pill done";
      return "ow-step-pill";
    },
    currentUiStep() {
      if (this.profile) return 3;
      if (this.candidateCount !== null) return 2;
      return 1;
    },
    canStart() {
      return Boolean(this.country && this.region && this.first_name && this.gender);
    },
    async submitCreateProfile() {
      this.loading = true;
      this.createMessage = "";
      try {
        const payload = {
          first_name: this.first_name,
          last_name: this.newProfile.last_name,
          gender: this.gender,
          country: this.country,
          region: this.region,
          city: this.newProfile.city,
          birth_date: this.newProfile.birth_date || undefined,
          hair_color: this.newProfile.hair_color || undefined,
          email: this.newProfile.email || undefined,
          phone: this.newProfile.phone || undefined,
        };
        const res = await this.apiFetch("/api/candidates/create", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!data.ok) {
          this.createMessage = this._userMsg(data.error) || "Fehler beim Erstellen.";
          return;
        }
        this.createMessage = "Profil erstellt (ID " + data.candidate_id + "). " + data.credits_awarded + " Credits gutgeschrieben.";
        this.showCreateForm = false;
        this.newProfile = { last_name: "", birth_date: "", hair_color: "", city: "", email: "", phone: "" };
      } catch (e) {
        this.createMessage = "Verbindungsfehler. Bitte erneut versuchen.";
      } finally {
        this.loading = false;
      }
    },
    resetSearch() {
      clearInterval(this.timerHandle);
      this.loading = false;
      this.message = "";
      this.country = "";
      this.region = "";
      this.first_name = "";
      this.gender = "female";
      this.candidateCount = null;
      this.sessionToken = "";
      this.selectedCase = "";
      this.caseIndex = 0;
      this.currentField = "";
      this.stepValue = "";
      this.currentStepNumber = 2;
      this.stepMessage = "";
      this.stepTimer = this.stepTimeout;
      this.profile = null;
      this.selectedAttributes = [];
      this.anonymousVote = false;
      this.citySuggestions = [];
      this.firstNameSuggestions = [];
      this.showCountrySuggestions = false;
      this.showRegionSuggestions = false;
      this.showFirstNameSuggestions = false;
      this.showCreateForm = false;
      this.createMessage = "";
      this.newProfile = { last_name: "", birth_date: "", hair_color: "", city: "", email: "", phone: "" };
      this.loadCountries();
    },
    csrfToken() {
      const inputToken = document.querySelector("[name=csrfmiddlewaretoken]");
      if (inputToken && inputToken.value) return inputToken.value;
      const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
      return match ? decodeURIComponent(match[1]) : "";
    },
    requestHeaders(extra) {
      const headers = Object.assign({ "X-Requested-With": "XMLHttpRequest" }, extra || {});
      const csrf = this.csrfToken();
      if (csrf) headers["X-CSRFToken"] = csrf;
      const gate = localStorage.getItem("tl_js_gate_token");
      if (gate) headers["X-JS-Gate"] = gate;
      return headers;
    },
    timerPercent() {
      if (!this.stepTimeout || this.stepTimeout <= 0) return 0;
      return Math.max(0, Math.min(100, Math.round((this.stepTimer / this.stepTimeout) * 100)));
    },
    genderLabel() {
      if (this.gender === "female") return "Weiblich";
      if (this.gender === "male") return "Männlich";
      if (this.gender === "diverse") return "Divers";
      return "Unbekannt";
    },
    resultHeadline() {
      const name = this.first_name || "Unbekannt";
      return name + ", " + this.genderLabel();
    },
    resetTimer() {
      clearInterval(this.timerHandle);
      this.stepTimer = this.stepTimeout;
      this.timerHandle = setInterval(() => {
        this.stepTimer -= 1;
        if (this.stepTimer <= 0) {
          clearInterval(this.timerHandle);
          this.stepMessage = "Step-Timeout erreicht. Bitte Suche neu starten.";
          this.selectedCase = "";
        }
      }, 1000);
    },
    _userMsg(error) {
      if (!error) return "";
      if (error.includes("JS gate token")) return "Bitte zuerst das Captcha auf der Startseite lösen.";
      return error;
    },
    async loadCountries() {
      try {
        const res = await this.apiFetch("/api/search/countries?q=" + encodeURIComponent(this.country || ""));
        const data = await res.json();
        this.countrySuggestions = data.suggestions || [];
        this.showCountrySuggestions = this.countrySuggestions.length > 0;
      } catch (e) {
        this.countrySuggestions = [];
      }
    },
    async loadFirstNames() {
      const q = (this.first_name || "").trim();
      if (q.length < 2) { this.firstNameSuggestions = []; this.showFirstNameSuggestions = false; return; }
      try {
        const res = await this.apiFetch("/api/search/first-names?q=" + encodeURIComponent(q));
        const data = await res.json();
        this.firstNameSuggestions = data.suggestions || [];
        this.showFirstNameSuggestions = this.firstNameSuggestions.length > 0;
      } catch (e) {
        this.firstNameSuggestions = [];
      }
    },
    async loadRegions() {
      if (!this.country) return;
      try {
        const res = await this.apiFetch(
          "/api/search/regions?country=" + encodeURIComponent(this.country) + "&q=" + encodeURIComponent(this.region || "")
        );
        const data = await res.json();
        this.regionSuggestions = data.suggestions || [];
        this.showRegionSuggestions = this.regionSuggestions.length > 0;
      } catch (e) {
        this.regionSuggestions = [];
      }
    },
    async loadCities() {
      if (!this.country || !this.region || !this.stepValue || this.stepValue.length < 2) return;
      try {
        const params = new URLSearchParams({ q: this.stepValue, country: this.country, region: this.region });
        const res = await this.apiFetch("/api/search/cities?" + params.toString());
        const data = await res.json();
        this.citySuggestions = data.suggestions || [];
      } catch (e) {
        this.citySuggestions = [];
      }
    },
    async apiFetch(url, options) {
      const opts = options || {};
      const headers = this.requestHeaders(opts.headers || {});
      return fetch(url, Object.assign({}, opts, { headers: headers }));
    },
    async startSearch() {
      this.loading = true;
      this.message = "";
      this.profile = null;
      this.selectedCase = "";
      this.candidateCount = null;
      try {
        const res = await this.apiFetch("/api/search/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            country: this.country,
            region: this.region,
            first_name: this.first_name,
            gender: this.gender,
          }),
        });
        const data = await res.json();
        if (!data.ok) {
          this.message = this._userMsg(data.error) || "Suche fehlgeschlagen";
          return;
        }
        this.sessionToken = data.session_token;
        this.candidateCount = data.candidate_count;
        this.message = data.message || "";
      } catch (e) {
        this.message = "Verbindungsfehler. Bitte Seite neu laden.";
      } finally {
        this.loading = false;
      }
    },
    chooseCase(key) {
      this.selectedCase = key;
      this.caseIndex = 0;
      this.currentStepNumber = 2;
      this.currentField = this.caseByKey().fields[this.caseIndex];
      this.stepValue = "";
      this.stepMessage = "";
      this.resetTimer();
    },
    caseByKey() {
      return this.cases.find(function (c) { return c.key === this.selectedCase; }, this);
    },
    currentFieldLabel() {
      const labels = {
        birth_date: "Geburtsdatum",
        email: "E-Mail",
        phone: "Telefon",
        age: "Alter",
        social_url: "Dating-Profil-URL",
        last_name: "Nachname",
        city: "Stadt",
        hair_color: "Haarfarbe",
      };
      return labels[this.currentField] || this.currentField;
    },
    async submitStep() {
      if (!this.sessionToken || !this.selectedCase || !this.currentField) return;
      this.loading = true;
      try {
        const payload = {
          session_token: this.sessionToken,
          case_type: this.selectedCase,
        };
        payload[this.currentField] = this.stepValue;
        const res = await this.apiFetch("/api/search/step/" + this.currentStepNumber, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!data.ok) {
          this.stepMessage = this._userMsg(data.error) || "Schritt fehlgeschlagen";
          return;
        }
        if (data.resolved) {
          clearInterval(this.timerHandle);
          this.stepMessage = "Profil erfolgreich verifiziert.";
          await this.loadProfile();
          return;
        }
        this.caseIndex += 1;
        this.currentStepNumber += 1;
        this.currentField = this.caseByKey().fields[this.caseIndex];
        this.stepValue = "";
        this.stepMessage = "Noch " + data.remaining_candidates + " mögliche Treffer.";
        this.resetTimer();
      } catch (e) {
        this.stepMessage = "Verbindungsfehler. Bitte erneut versuchen.";
      } finally {
        this.loading = false;
      }
    },
    async loadProfile() {
      try {
        const res = await this.apiFetch("/api/search/session/" + this.sessionToken + "/profile");
        const data = await res.json();
        if (!data.ok) {
          this.stepMessage = this._userMsg(data.error) || "Profil konnte nicht geladen werden";
          return;
        }
        this.profile = data;
        await this.refreshVotes();
      } catch (e) {
        this.stepMessage = "Verbindungsfehler beim Laden des Profils.";
      }
    },
    async refreshVotes() {
      if (!this.profile) return;
      try {
        const res = await this.apiFetch("/api/candidates/" + this.profile.id + "/votes");
        const data = await res.json();
        if (data.ok) this.profile.vote_breakdown = data.votes;
      } catch (e) { /* non-critical */ }
    },
    async submitVote() {
      if (!this.profile) return;
      if (this.selectedAttributes.length > 3) {
        this.stepMessage = "Maximal 3 Kategorien erlaubt.";
        return;
      }
      try {
        const res = await this.apiFetch("/api/candidates/" + this.profile.id + "/vote", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            attribute_codes: this.selectedAttributes,
            anonymous: this.anonymousVote,
          }),
        });
        const data = await res.json();
        if (!data.ok) {
          this.stepMessage = this._userMsg(data.error) || "Vote fehlgeschlagen.";
          return;
        }
        this.stepMessage = "Vote gespeichert.";
        this.selectedAttributes = [];
        this.anonymousVote = false;
        await this.refreshVotes();
      } catch (e) {
        this.stepMessage = "Verbindungsfehler beim Speichern des Votes.";
      }
    },
  };
}

/* ── Credit purchase stepper ── */
function creditBuy() {
  return {
    qty: 1,
    msg: "",
    inc() { if (this.qty < 100) this.qty += 1; },
    dec() { if (this.qty > 1) this.qty -= 1; },
    requestHeaders(extra) {
      const headers = Object.assign({ "X-Requested-With": "XMLHttpRequest" }, extra || {});
      const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
      if (match) headers["X-CSRFToken"] = decodeURIComponent(match[1]);
      const gate = localStorage.getItem("tl_js_gate_token");
      if (gate) headers["X-JS-Gate"] = gate;
      return headers;
    },
    async buy() {
      const res = await fetch("/api/credits/checkout", {
        method: "POST",
        headers: this.requestHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ quantity: this.qty }),
      });
      const data = await res.json();
      if (!data.ok) {
        this.msg = data.error || "Checkout fehlgeschlagen";
        return;
      }
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    },
  };
}

/* ── Relay panel (recruiter contact requests) ── */
function relayPanel() {
  function headers() {
    const h = { "X-Requested-With": "XMLHttpRequest", "Content-Type": "application/json" };
    const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    if (match) h["X-CSRFToken"] = decodeURIComponent(match[1]);
    const gate = localStorage.getItem("tl_js_gate_token");
    if (gate) h["X-JS-Gate"] = gate;
    return h;
  }
  return {
    relayMsg: "",
    async accept(id) {
      const res = await fetch("/api/recruiters/contact-request/" + id + "/accept", { method: "POST", headers: headers() });
      const data = await res.json();
      this.relayMsg = data.ok ? "Kontakt freigegeben. Beide Recruiter wurden per E-Mail informiert." : (data.error || "Fehler");
      if (data.ok) setTimeout(function () { location.reload(); }, 2000);
    },
    async reject(id) {
      const res = await fetch("/api/recruiters/contact-request/" + id + "/reject", { method: "POST", headers: headers() });
      const data = await res.json();
      this.relayMsg = data.ok ? "Anfrage abgelehnt." : (data.error || "Fehler");
      if (data.ok) setTimeout(function () { location.reload(); }, 1500);
    },
  };
}
