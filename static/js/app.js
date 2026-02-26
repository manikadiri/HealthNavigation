/**
 * AI Smart Health Navigator — Frontend App Logic
 * ================================================
 * Guest Mode: No login required.
 * LocalStorage keys:
 *   hn_session_id   — unique guest session ID
 *   hn_history      — array of search strings
 *   hn_token        — current booked token object
 */

const App = (() => {
  'use strict';

  // ── State ───────────────────────────────────────────────────────────────
  let state = {
    currentPage: 'auth',
    previousPage: 'auth',
    lang: 'en',
    sessionId: null,
    user: null,                // logged in user info
    hospitals: [],
    currentHospital: null,
    currentHospitalSchemes: [],
    token: null,
    queueInterval: null,
    specFilter: '',
    schemeFilter: 'all',
    loginMode: 'password',
  };

  // ── Translations ────────────────────────────────────────────────────────
  const T = {
    en: {
      greeting: '👋 Good day! How can we help?',
      hero_title: 'Your AI Health Navigator',
      quick_actions: 'Quick Actions',
      qa_disease: 'Disease Search', qa_disease_sub: 'AI explanation & tips',
      qa_hospitals: 'Find Hospitals', qa_hospitals_sub: 'Rated & verified near you',
      qa_token: 'Book Token', qa_token_sub: 'Skip the queue smartly',
      qa_schemes: 'Gov. Schemes', qa_schemes_sub: 'Free healthcare benefits',
      health_tips: 'Daily Health Tips',
      emg_numbers: 'Emergency Numbers',
      recent_searches: 'Recent Searches', clear: 'Clear',
      disease_title: 'AI Disease Info',
      hospitals_title: 'Find Hospitals',
      token_title: 'Smart Queue',
      all: 'All',
      your_token: 'TOKEN',
      people_ahead: 'People Ahead',
      est_wait: 'Estimated Wait',
      current_token: 'Current Token',
      select_hospital: 'Select Hospital',
      cancel_token: '✕ Cancel Token',
      nav_home: 'Home', nav_disease: 'Disease', nav_hospitals: 'Hospitals',
      nav_token: 'Token', nav_schemes: 'Schemes',
    },
    te: {
      greeting: '👋 నమస్కారం! మీకు ఎలా సహాయం చేయగలను?',
      hero_title: 'మీ AI ఆరోగ్య నావిగేటర్',
      quick_actions: 'శీఘ్ర చర్యలు',
      qa_disease: 'వ్యాధి శోధన', qa_disease_sub: 'AI వివరణ & సూచనలు',
      qa_hospitals: 'ఆసుపత్రులు కనుగొనండి', qa_hospitals_sub: 'రేటింగ్ & ధృవీకరించబడ్డాయి',
      qa_token: 'టోకెన్ బుక్', qa_token_sub: 'క్యూ దాటి సమయం ఆదా',
      qa_schemes: 'ప్రభుత్వ పథకాలు', qa_schemes_sub: 'ఉచిత ఆరోగ్య సేవలు',
      health_tips: 'రోజువారీ చిట్కాలు',
      emg_numbers: 'అత్యవసర నంబర్లు',
      recent_searches: 'ఇటీవలి శోధనలు', clear: 'తొలగించు',
      disease_title: 'AI వ్యాధి సమాచారం',
      hospitals_title: 'ఆసుపత్రులు కనుగొనండి',
      token_title: 'స్మార్ట్ క్యూ',
      all: 'అన్నీ',
      your_token: 'టోకెన్',
      people_ahead: 'ముందు వ్యక్తులు',
      est_wait: 'వేచి ఉండే సమయం',
      current_token: 'ప్రస్తుత టోకెన్',
      select_hospital: 'ఆసుపత్రి ఎంచుకోండి',
      cancel_token: '✕ టోకెన్ రద్దు',
      nav_home: 'హోమ్', nav_disease: 'వ్యాధి', nav_hospitals: 'ఆసుపత్రులు',
      nav_token: 'టోకెన్', nav_schemes: 'పథకాలు',
    },
    hi: {
      greeting: '👋 नमस्ते! आपकी कैसे मदद करें?',
      hero_title: 'आपका AI स्वास्थ्य नेविगेटर',
      quick_actions: 'त्वरित कार्य',
      qa_disease: 'रोग खोज', qa_disease_sub: 'AI जानकारी व सुझाव',
      qa_hospitals: 'अस्पताल खोजें', qa_hospitals_sub: 'रेटेड और सत्यापित',
      qa_token: 'टोकन बुक करें', qa_token_sub: 'कतार से बचें',
      qa_schemes: 'सरकारी योजनाएं', qa_schemes_sub: 'मुफ्त स्वास्थ्य लाभ',
      health_tips: 'दैनिक स्वास्थ्य सुझाव',
      emg_numbers: 'आपातकालीन नंबर',
      recent_searches: 'हाल की खोजें', clear: 'साफ करें',
      disease_title: 'AI रोग जानकारी',
      hospitals_title: 'अस्पताल खोजें',
      token_title: 'स्मार्ट कतार',
      all: 'सभी',
      your_token: 'टोकन',
      people_ahead: 'आगे लोग',
      est_wait: 'अनुमानित प्रतीक्षा',
      current_token: 'वर्तमान टोकन',
      select_hospital: 'अस्पताल चुनें',
      cancel_token: '✕ टोकन रद्द करें',
      nav_home: 'होम', nav_disease: 'रोग', nav_hospitals: 'अस्पताल',
      nav_token: 'टोकन', nav_schemes: 'योजनाएं',
    }
  };

  // ── Init ────────────────────────────────────────────────────────────────
  async function init() {
    await playSplash();

    // Generate or load session ID
    state.sessionId = localStorage.getItem('hn_session_id') || generateId();
    localStorage.setItem('hn_session_id', state.sessionId);

    // attempt to fetch current user
    await fetchCurrentUser();
    updateAuthNav();

    // Restore token from storage
    const savedToken = localStorage.getItem('hn_token');
    if (savedToken) {
      try { state.token = JSON.parse(savedToken); } catch(e) {}
    }

    loadCities();
    loadHospitals();
    renderRecentSearches();
    loadAllSchemes();

    // If there's an active token, start status polling
    if (state.token) {
      startQueuePolling();
    }

    // Mark token nav if token exists
    updateTokenNav();

    if (state.user) {
      navTo('home');
    } else {
      showLogin();
      navTo('auth');
    }
  }

  async function playSplash() {
    const splash = document.getElementById('app-splash');
    if (!splash) return;
    const holdMs = 4000 + Math.floor(Math.random() * 3001); // 4s to 7s
    splash.classList.add('animate');
    await new Promise(resolve => setTimeout(resolve, holdMs));
    splash.classList.add('hidden');
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  function generateId() {
    return 'guest_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  }

  // ── Navigation ──────────────────────────────────────────────────────────
  function navTo(page, btn) {
    // whenever navigation happens, ensure auth nav updated (login status may change)
    updateAuthNav();
    state.previousPage = state.currentPage;
    state.currentPage = page;

    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const target = document.getElementById('page-' + page);
    if (target) target.classList.add('active');

    // Update bottom nav
    document.querySelectorAll('.bnav-item').forEach(b => b.classList.remove('active'));
    if (btn) {
      btn.classList.add('active');
    } else {
      // Auto-highlight correct nav item
      const navMap = { home: 0, disease: 1, hospitals: 2, token: 3, schemes: 4 };
      const idx = navMap[page];
      if (idx !== undefined) {
        const btns = document.querySelectorAll('.bnav-item');
        if (btns[idx]) btns[idx].classList.add('active');
      }
    }

    // Page-specific loading
    if (page === 'token' && state.token) {
      renderActiveToken();
    }
    if (page === 'schemes') {
      loadAllSchemes();
    }

    const appShell = document.getElementById('app');
    if (appShell) appShell.classList.toggle('auth-view', page === 'auth');
  }

  function goBack() {
    navTo(state.previousPage || 'home');
  }

  // ── Language ─────────────────────────────────────────────────────────────
  function changeLang(lang) {
    state.lang = lang;
    const translations = T[lang] || T['en'];
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (translations[key]) el.textContent = translations[key];
    });
    toast(`Language changed`);
  }

  // ── Authentication ──────────────────────────────────────────────────────
  async function fetchCurrentUser() {
    try {
      const resp = await fetch('/api/user');
      const json = await resp.json();
      state.user = json.user || null;
    } catch(e) { state.user = null; }
  }

  function updateAuthNav() {
    const wrap = document.getElementById('user-auth');
    if (!wrap) return;
    if (state.user) {
      wrap.innerHTML = `
        <span style="font-size:0.85rem;color:var(--muted)">Hi, ${state.user.name}</span>
        <button class="text-btn" style="margin-left:8px;padding:4px 8px;font-size:0.75rem;" onclick="App.logout()">Logout</button>
      `;
    } else {
      wrap.innerHTML = `<button class="text-btn" onclick="App.navTo('auth')">Login</button>`;
    }
  }

  function showLogin() {
    document.getElementById('auth-title').textContent = 'Login';
    document.getElementById('login-form').classList.remove('hidden');
    document.getElementById('signup-form').classList.add('hidden');
    setLoginMode('password');
  }

  function showSignup() {
    document.getElementById('auth-title').textContent = 'Sign Up';
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('signup-form').classList.remove('hidden');
  }

  function setLoginMode(mode) {
    state.loginMode = (mode === 'otp') ? 'otp' : 'password';
    const passBtn = document.getElementById('mode-password');
    const otpBtn = document.getElementById('mode-otp');
    const otpRow = document.getElementById('otp-row');
    const passRow = document.getElementById('password-row');
    if (!passBtn || !otpBtn || !otpRow || !passRow) return;

    passBtn.classList.toggle('active', state.loginMode === 'password');
    otpBtn.classList.toggle('active', state.loginMode === 'otp');
    otpRow.classList.toggle('hidden', state.loginMode !== 'otp');
    passRow.classList.toggle('hidden', state.loginMode !== 'password');
  }

  async function requestOtp() {
    const mobile = (document.getElementById('login-mobile').value || '').trim();
    if (!mobile) return toast('Mobile number is required');
    try {
      const resp = await fetch('/api/login/request-otp', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ mobile })
      });
      const json = await resp.json();
      if (json.success) {
        toast(`OTP sent. Demo OTP: ${json.otp}`);
      } else if (json.error) {
        toast(json.error);
      }
    } catch(e) { toast('Could not send OTP'); }
  }

  async function login() {
    const mobile = document.getElementById('login-mobile').value.trim();
    const password = document.getElementById('login-password').value;
    const otp = document.getElementById('login-otp').value.trim();

    if (!mobile) return toast('Mobile number is required');
    if (state.loginMode === 'password' && !password) return toast('Password is required');
    if (state.loginMode === 'otp' && !otp) return toast('OTP is required');

    try {
      const resp = await fetch('/api/login', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({mobile, password, otp, mode: state.loginMode})
      });
      const json = await resp.json();
      if (json.user) {
        state.user = json.user;
        toast('Logged in successfully');
        updateAuthNav();
        navTo('home');
      } else if (json.error) {
        toast(json.error);
      }
    } catch(e) { toast('Login failed'); }
  }

  async function signup() {
    const name = document.getElementById('signup-name').value.trim();
    const mobile = document.getElementById('signup-mobile').value.trim();
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;
    if (!name || !mobile || !password || !confirmPassword) return toast('All fields required');
    if (password !== confirmPassword) return toast('Password and confirm password must match');
    try {
      const resp = await fetch('/api/register', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({name,mobile,password,confirm_password: confirmPassword})
      });
      const json = await resp.json();
      if (json.user) {
        state.user = json.user;
        toast('Account created & logged in');
        updateAuthNav();
        navTo('home');
      } else if (json.error) {
        toast(json.error);
      }
    } catch(e) { toast('Signup failed'); }
  }

  async function logout() {
    try {
      await fetch('/api/logout', {method:'POST'});
    } catch(e) {}
    state.user = null;
    updateAuthNav();
    toast('Logged out');
    showLogin();
    navTo('auth');
  }

  // ── Recent Searches ──────────────────────────────────────────────────────
  function getHistory() {
    try { return JSON.parse(localStorage.getItem('hn_history') || '[]'); } catch(e) { return []; }
  }

  function addToHistory(query) {
    const h = getHistory().filter(q => q.toLowerCase() !== query.toLowerCase());
    h.unshift(query);
    localStorage.setItem('hn_history', JSON.stringify(h.slice(0, 8)));
    renderRecentSearches();
  }

  function clearHistory() {
    localStorage.removeItem('hn_history');
    renderRecentSearches();
  }

  function renderRecentSearches() {
    const history = getHistory();
    const wrap = document.getElementById('recent-wrap');
    const list = document.getElementById('recent-list');
    if (!history.length) { wrap.classList.add('hidden'); return; }
    wrap.classList.remove('hidden');
    list.innerHTML = history.map(q => `
      <span class="r-chip" onclick="App.quickSearch('${q}')">
        <i class="fa-solid fa-clock-rotate-left" style="font-size:11px"></i> ${q}
      </span>
    `).join('');
  }

  // ── Disease Search ───────────────────────────────────────────────────────
  async function searchDisease() {
    const input = document.getElementById('disease-input');
    const query = input.value.trim();
    if (!query) { toast('Please enter a disease or symptom'); return; }

    addToHistory(query);
    setSearchLoading(true);
    document.getElementById('disease-empty').classList.add('hidden');
    document.getElementById('disease-result').classList.add('hidden');

    try {
      const resp = await fetch('/api/ai/disease', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, session_id: state.sessionId })
      });
      const json = await resp.json();
      if (json.data) renderDiseaseResult(json.data);
    } catch(e) {
      toast('Could not fetch result. Check connection.');
    } finally {
      setSearchLoading(false);
    }
  }

  function setSearchLoading(on) {
    const btn = document.getElementById('search-btn');
    const txt = document.getElementById('search-btn-text');
    const spin = document.getElementById('search-spinner');
    btn.disabled = on;
    txt.classList.toggle('hidden', on);
    spin.classList.toggle('hidden', !on);
  }

  function quickSearch(term) {
    navTo('disease');
    document.getElementById('disease-input').value = term;
    searchDisease();
  }

  function quickActionDiseaseSearch() {
    const input = document.getElementById('qa-disease-input');
    const term = (input?.value || '').trim();
    navTo('disease');
    if (!term) return;
    document.getElementById('disease-input').value = term;
    searchDisease();
  }

  function quickActionHospitalSearch() {
    const input = document.getElementById('qa-hospital-input');
    const locationInput = document.getElementById('qa-location-filter');
    const term = (input?.value || '').trim();
    const location = (locationInput?.value || '').trim();
    navTo('hospitals');
    document.getElementById('hosp-search').value = term;
    const cityFilter = document.getElementById('city-filter');
    if (cityFilter) cityFilter.value = location;
    filterHospitals();
  }

  function quickActionHealthAdvice() {
    const input = document.getElementById('qa-advice-input');
    const term = (input?.value || '').trim();
    navTo('advice');
    if (!term) return;
    document.getElementById('advice-input').value = term;
    searchHealthAdvice();
  }

  async function searchHealthAdvice() {
    const input = document.getElementById('advice-input');
    const query = input.value.trim();
    if (!query) { toast('Please enter your health goal'); return; }

    setAdviceLoading(true);
    document.getElementById('advice-empty').classList.add('hidden');
    document.getElementById('advice-result').classList.add('hidden');

    try {
      const resp = await fetch('/api/ai/advice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const json = await resp.json();
      if (json.data) renderHealthAdvice(json.data);
    } catch(e) {
      toast('Could not fetch health advice');
    } finally {
      setAdviceLoading(false);
    }
  }

  function setAdviceLoading(on) {
    const btn = document.getElementById('advice-search-btn');
    const txt = document.getElementById('advice-btn-text');
    const spin = document.getElementById('advice-spinner');
    btn.disabled = on;
    txt.classList.toggle('hidden', on);
    spin.classList.toggle('hidden', !on);
  }

  function renderHealthAdvice(data) {
    document.getElementById('advice-title').textContent = data.title || 'Health Advice';
    document.getElementById('advice-summary').textContent = data.summary || '';
    document.getElementById('advice-dos').innerHTML = (data.recommended || [])
      .map(item => `<li>${item}</li>`).join('');
    document.getElementById('advice-donts').innerHTML = (data.avoid || [])
      .map(item => `<li>${item}</li>`).join('');
    document.getElementById('advice-when-doctor').textContent =
      data.when_to_consult || 'If symptoms are severe or continue for more than a few days.';
    document.getElementById('advice-result').classList.remove('hidden');
  }

  function askStarterQuestion(question) {
    const input = document.getElementById('chat-input');
    if (!input) return;
    input.value = question;
    sendChatMessage();
  }

  async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const btn = document.getElementById('chat-send-btn');
    const query = (input?.value || '').trim();
    if (!query) return;

    appendChatMessage('user', query);
    input.value = '';
    if (btn) btn.disabled = true;

    try {
      const resp = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const json = await resp.json();
      const reply = json.reply || 'Please share a bit more detail, and I will guide you.';
      appendChatMessage('bot', reply);
    } catch (e) {
      appendChatMessage('bot', 'Could not respond now. Please try again in a moment.');
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  function appendChatMessage(role, text) {
    const wrap = document.getElementById('chat-messages');
    if (!wrap) return;
    const msg = document.createElement('div');
    msg.className = `chat-msg ${role === 'user' ? 'user' : 'bot'}`;
    msg.textContent = text;
    wrap.appendChild(msg);
    wrap.scrollTop = wrap.scrollHeight;
  }

  function renderDiseaseResult(data) {
    document.getElementById('res-title').textContent = data.title || '';
    document.getElementById('res-desc').textContent = data.description || '';
    document.getElementById('res-specialist').textContent = data.specialist || 'General Physician';

    // Emergency
    const emgEl = document.getElementById('res-emergency');
    if (data.emergency) emgEl.classList.remove('hidden');
    else emgEl.classList.add('hidden');

    // Do's
    const dosList = document.getElementById('res-dos');
    dosList.innerHTML = (data.dos || []).map(d => `<li>${d}</li>`).join('');

    // Don'ts
    const dontsList = document.getElementById('res-donts');
    dontsList.innerHTML = (data.donts || []).map(d => `<li>${d}</li>`).join('');

    // Food
    const foodEl = document.getElementById('res-food');
    foodEl.innerHTML = (data.food || []).map(f =>
      `<div class="ls-item"><span class="ls-ico">${f.icon}</span><p>${f.text}</p></div>`
    ).join('');

    // Prevention
    const prevEl = document.getElementById('res-prevention');
    prevEl.innerHTML = (data.prevention || []).map(p =>
      `<div class="ls-item"><span class="ls-ico">${p.icon}</span><p>${p.text}</p></div>`
    ).join('');

    document.getElementById('disease-result').classList.remove('hidden');
  }

  function findHospitalsForDisease() {
    const query = document.getElementById('disease-input').value.trim();
    document.getElementById('hosp-search').value = query;
    navTo('hospitals');
    filterHospitals();
  }

  // ── Hospitals ────────────────────────────────────────────────────────────
  async function loadCities() {
    try {
      const resp = await fetch('/api/cities');
      const cities = await resp.json();
      const cityFilter = document.getElementById('city-filter');
      const qaLocationFilter = document.getElementById('qa-location-filter');
      if (cityFilter) {
        cityFilter.innerHTML = '<option value="">All Cities</option>';
      }
      if (qaLocationFilter) {
        qaLocationFilter.innerHTML = '<option value="">All Locations</option>';
      }

      (cities || []).forEach(c => {
        if (cityFilter) {
          const opt = document.createElement('option');
          opt.value = c;
          opt.textContent = c;
          cityFilter.appendChild(opt);
        }
        if (qaLocationFilter) {
          const qaOpt = document.createElement('option');
          qaOpt.value = c;
          qaOpt.textContent = c;
          qaLocationFilter.appendChild(qaOpt);
        }
      });
    } catch(e) {}
  }

  async function loadHospitals(params = {}) {
    const listEl = document.getElementById('hospital-list');
    const loadingEl = document.getElementById('hospitals-loading');
    const emptyEl = document.getElementById('hospitals-empty');
    listEl.innerHTML = '';
    loadingEl.classList.remove('hidden');
    emptyEl.classList.add('hidden');

    const qs = new URLSearchParams(params).toString();
    try {
      const resp = await fetch('/api/hospitals' + (qs ? '?' + qs : ''));
      const hospitals = await resp.json();
      state.hospitals = hospitals;
      loadingEl.classList.add('hidden');

      if (!hospitals.length) {
        emptyEl.classList.remove('hidden');
        return;
      }
      listEl.innerHTML = hospitals.map(h => renderHospitalCard(h)).join('');

      // Also render token hospital list (subset)
      const tokList = document.getElementById('token-hosp-list');
      if (tokList) {
        tokList.innerHTML = hospitals.slice(0, 8).map(h => renderHospitalCard(h, 'token')).join('');
      }
    } catch(e) {
      loadingEl.classList.add('hidden');
      listEl.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><p>Could not load hospitals.</p></div>';
    }
  }

  function renderHospitalCard(h, mode) {
    const onClick = mode === 'token'
      ? `App.bookTokenById(${h.id})`
      : `App.openHospital(${h.id})`;

    const btnText = mode === 'token' ? 'Book Token' : 'View Details';

    const aarogyasriTag = h.aarogyasri
      ? `<span class="stag yes"><i class="fa-solid fa-check"></i> Aarogyasri</span>`
      : `<span class="stag no"><i class="fa-solid fa-xmark"></i> Aarogyasri</span>`;

    const ayushmanTag = h.ayushman
      ? `<span class="stag yes"><i class="fa-solid fa-check"></i> Ayushman</span>`
      : '';

    const emergTag = h.emergency
      ? `<span class="stag neutral"><i class="fa-solid fa-truck-medical"></i> 24×7 Emergency</span>`
      : '';

    return `
    <div class="hosp-card" onclick="${onClick}">
      <div class="hc-top">
        <div class="hc-icon">${h.icon || '🏥'}</div>
        <div class="hc-info">
          <h3>${h.name}</h3>
          <div class="hc-loc"><i class="fa-solid fa-location-dot"></i> ${h.city}</div>
          <div class="hc-spec">${h.specialization}</div>
        </div>
        <div class="hc-rating"><i class="fa-solid fa-star"></i> ${h.rating}</div>
      </div>
      <div class="scheme-tags">
        ${aarogyasriTag}
        ${ayushmanTag}
        ${emergTag}
      </div>
      <div class="hc-footer">
        <span class="scheme-count">${h.beds || 0} beds · ${h.city}</span>
        <button class="view-btn" onclick="event.stopPropagation();${onClick}">${btnText}</button>
      </div>
    </div>`;
  }

  function filterHospitals() {
    const search = document.getElementById('hosp-search').value.trim();
    const city = document.getElementById('city-filter').value;
    const params = {};
    if (search) params.search = search;
    if (city) params.city = city;
    if (state.specFilter) params.spec = state.specFilter;
    loadHospitals(params);
  }

  function filterSpec(spec, btn) {
    state.specFilter = spec;
    document.querySelectorAll('.spec-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterHospitals();
  }

  // ── Hospital Detail ──────────────────────────────────────────────────────
  async function openHospital(id) {
    state.previousPage = state.currentPage;
    try {
      const resp = await fetch(`/api/hospitals/${id}`);
      const h = await resp.json();
      state.currentHospital = h;
      state.currentHospitalSchemes = h.schemes || [];

      // Hero
      document.getElementById('detail-icon').textContent = h.icon || '🏥';
      document.getElementById('detail-name').textContent = h.name;
      document.getElementById('detail-address').innerHTML = `<i class="fa-solid fa-location-dot"></i> ${h.address || h.city}`;
      document.getElementById('detail-rating').textContent = h.rating;
      document.getElementById('detail-spec-badge').textContent = h.specialization;
      document.getElementById('detail-emergency-badge').textContent = h.emergency ? '🚨 24×7 Emergency' : '';

      // Phone
      const phoneBtn = document.getElementById('detail-phone-btn');
      phoneBtn.href = `tel:${h.phone || '108'}`;
      phoneBtn.onclick = (e) => { e.preventDefault(); alert(`Calling ${h.phone || h.name}...`); };

      // Render tabs
      renderSpecialists(h.specialists || []);
      renderDepartments(h.departments || []);
      renderSchemesCat('all');

      // Switch to first tab
      switchTab('specialists', document.querySelector('.d-tab'));

      // Show detail page
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      document.getElementById('page-hospital-detail').classList.add('active');
      window.scrollTo(0, 0);
    } catch(e) {
      toast('Could not load hospital details.');
    }
  }

  function renderSpecialists(specialists) {
    const el = document.getElementById('tab-specialists');
    if (!specialists.length) {
      el.innerHTML = '<div class="empty-state"><div class="empty-icon">👨‍⚕️</div><p>No specialists listed.</p></div>';
      return;
    }
    el.innerHTML = specialists.map(s => `
      <div class="spec-card">
        <div class="spec-avatar"><i class="fa-solid fa-user-doctor"></i></div>
        <div class="spec-info">
          <h4>${s.name}</h4>
          <p>${s.department} · ${s.qualification}</p>
          <div class="spec-avail"><i class="fa-solid fa-clock"></i> ${s.availability}</div>
        </div>
        <div class="spec-fee">₹${s.fee || 500}</div>
      </div>
    `).join('');
  }

  function renderDepartments(depts) {
    const el = document.getElementById('tab-departments');
    if (!depts.length) {
      el.innerHTML = '<div class="empty-state"><div class="empty-icon">🏛️</div><p>No departments listed.</p></div>';
      return;
    }
    el.innerHTML = `<div class="dept-grid">` +
      depts.map(d => `
        <div class="dept-item">
          <span class="di">${d.icon || '🏥'}</span>
          <span>${d.name}</span>
        </div>
      `).join('') +
      `</div>`;
  }

  function renderSchemesCat(cat) {
    const allSchemes = state.currentHospitalSchemes;
    const filtered = cat === 'all' ? allSchemes : allSchemes.filter(s => s.category === cat || s.category === 'all');
    const el = document.getElementById('schemes-content');

    if (!filtered.length) {
      el.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><p>No schemes for this category.</p></div>';
      return;
    }
    el.innerHTML = filtered.map(s => `
      <div class="scheme-card">
        <div class="scheme-header">
          <h4>${s.scheme_name}</h4>
          <span class="scheme-status ${s.is_available ? 'yes' : 'no'}">
            ${s.is_available ? '✔ Available' : '✖ Not Available'}
          </span>
        </div>
        <p class="scheme-benefit"><strong>Benefits:</strong> ${s.benefit}</p>
        <div class="scheme-elig"><strong>Eligibility:</strong> ${s.eligibility}</div>
        ${s.is_available ? `
          <div class="scheme-steps">
            <strong style="font-size:0.8rem;color:#1a2f3e;display:block;margin-bottom:6px">How to Apply:</strong>
            <ol>${(s.steps || []).map(st => `<li>${st}</li>`).join('')}</ol>
          </div>
        ` : ''}
      </div>
    `).join('');
  }

  function filterSchemesCat(cat, btn) {
    document.querySelectorAll('#tab-schemes .scat-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderSchemesCat(cat);
  }

  function switchTab(tab, btn) {
    document.querySelectorAll('.d-tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    if (btn) btn.classList.add('active');
    else {
      const allTabBtns = document.querySelectorAll('.d-tab');
      const idx = ['specialists','departments','schemes'].indexOf(tab);
      if (allTabBtns[idx]) allTabBtns[idx].classList.add('active');
    }
    document.getElementById('tab-' + tab).classList.add('active');
  }

  function bookTokenForCurrent() {
    if (state.currentHospital) bookTokenById(state.currentHospital.id);
  }

  // ── Token System ─────────────────────────────────────────────────────────
  async function bookTokenById(hospitalId) {
    try {
      const resp = await fetch('/api/tokens', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hospital_id: hospitalId, session_id: state.sessionId })
      });
      const data = await resp.json();
      if (data.error) { toast(data.error); return; }

      state.token = data;
      localStorage.setItem('hn_token', JSON.stringify(data));
      updateTokenNav();
      navTo('token');
      renderActiveToken();
      startQueuePolling();
      toast(`Token ${data.token} booked for ${data.hospital_name}!`);
    } catch(e) {
      toast('Could not book token. Try again.');
    }
  }

  function renderActiveToken() {
    if (!state.token) return;
    const tok = state.token;
    document.getElementById('token-active').classList.remove('hidden');
    document.getElementById('token-book').classList.add('hidden');
    document.getElementById('tok-number').textContent = tok.token;
    document.getElementById('tok-hospital').textContent = tok.hospital_name;
    updateQueueDisplay(tok.people_ahead, tok.estimated_wait);
  }

  function updateQueueDisplay(ahead, wait) {
    document.getElementById('tok-ahead').textContent = ahead;
    document.getElementById('tok-wait').textContent = `~${wait} min`;
    const currentNum = state.token ? parseInt(state.token.token.slice(1)) - ahead - 1 : 0;
    const letter = state.token ? state.token.token[0] : 'A';
    document.getElementById('tok-current').textContent = `${letter}${Math.max(1, currentNum)}`;

    const totalSlots = 20;
    const progress = Math.max(5, Math.round(100 - (ahead / totalSlots * 100)));
    document.getElementById('tok-progress').style.width = progress + '%';

    const alertEl = document.getElementById('tok-alert');
    const statusEl = document.getElementById('tok-status-text');

    if (ahead === 0) {
      alertEl.className = 'tok-alert-box success';
      alertEl.innerHTML = `<i class="fa-solid fa-circle-check"></i> <div><strong>🎉 Your turn now!</strong> Please proceed to the counter immediately.</div>`;
      statusEl.textContent = 'IT IS YOUR TURN — GO NOW!';
      document.getElementById('tok-progress').style.width = '100%';
    } else if (ahead <= 3) {
      alertEl.className = 'tok-alert-box warn';
      alertEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <div><strong>Almost your turn!</strong> Only ${ahead} patients ahead. Please be ready near the counter.</div>`;
      statusEl.textContent = `${ahead} more patients before you`;
    } else {
      alertEl.className = 'tok-alert-box info';
      alertEl.innerHTML = `<i class="fa-solid fa-circle-info"></i> <div><strong>Queue is moving.</strong> ${ahead} patients ahead. Estimated wait ~${wait} minutes.</div>`;
      statusEl.textContent = `${ahead} patients before you`;
    }
  }

  function startQueuePolling() {
    if (state.queueInterval) clearInterval(state.queueInterval);
    if (!state.token) return;

    state.queueInterval = setInterval(async () => {
      if (!state.token) { clearInterval(state.queueInterval); return; }
      try {
        const resp = await fetch(`/api/tokens/${state.token.token}/status`);
        const data = await resp.json();
        if (data.people_ahead !== undefined) {
          state.token.people_ahead = data.people_ahead;
          state.token.estimated_wait = data.estimated_wait;
          localStorage.setItem('hn_token', JSON.stringify(state.token));

          // Update UI if on token page
          if (state.currentPage === 'token') {
            updateQueueDisplay(data.people_ahead, data.estimated_wait);
          }

          // Toast alert when close
          if (data.people_ahead === 3) {
            toast(`⚠️ Only 3 patients ahead for token ${state.token.token}!`);
          } else if (data.people_ahead === 0) {
            toast(`🎉 Your turn now! Token ${state.token.token}`);
            clearInterval(state.queueInterval);
          }
        }
      } catch(e) {}
    }, 15000); // poll every 15s
  }

  function cancelToken() {
    if (state.queueInterval) clearInterval(state.queueInterval);
    state.token = null;
    localStorage.removeItem('hn_token');
    document.getElementById('token-active').classList.add('hidden');
    document.getElementById('token-book').classList.remove('hidden');
    updateTokenNav();
    loadHospitals(); // refresh token hospital list
    toast('Token cancelled.');
  }

  function updateTokenNav() {
    const tokBtn = document.querySelectorAll('.bnav-item')[3];
    if (!tokBtn) return;
    if (state.token) {
      tokBtn.innerHTML = `<i class="fa-solid fa-ticket"></i><span>Token ●</span>`;
    } else {
      tokBtn.innerHTML = `<i class="fa-solid fa-ticket"></i><span data-i18n="nav_token">Token</span>`;
    }
  }

  // ── All Schemes Page ──────────────────────────────────────────────────────
  async function loadAllSchemes() {
    try {
      const resp = await fetch('/api/schemes');
      const schemes = await resp.json();
      state.allSchemes = schemes;
      renderAllSchemes(state.schemeFilter || 'all');
    } catch(e) {}
  }

  function renderAllSchemes(cat) {
    const schemes = state.allSchemes || [];
    const query = (document.getElementById('schemes-search')?.value || '').trim().toLowerCase();
    const byCat = cat === 'all' ? schemes : schemes.filter(s => s.category === cat || s.category === 'all');
    const filtered = byCat.filter(s => {
      if (!query) return true;
      const docs = (s.documents_required || []).join(' ').toLowerCase();
      const apply = (s.how_to_apply || []).join(' ').toLowerCase();
      const text = `${s.scheme_name} ${s.category} ${s.benefit || ''} ${s.eligibility || ''} ${s.income_limit || ''} ${docs} ${apply}`.toLowerCase();
      return text.includes(query);
    });
    const el = document.getElementById('all-schemes-list');
    if (!filtered.length) {
      el.innerHTML = '<div class="empty-state" style="padding:40px 20px"><div class="empty-icon">📋</div><p>No schemes found.</p></div>';
      return;
    }

    const catLabels = { all: 'General', women: '👩 Women', men: '👨 Men', child: '👶 Child', pregnant: '🤱 Pregnant' };
    el.innerHTML = filtered.map(s => `
      <div class="scheme-page-card">
        <div class="spc-head">
          <h3>${s.scheme_name}</h3>
          <span class="spc-cat">${catLabels[s.category] || s.category}</span>
        </div>
        <p class="spc-benefit">${s.benefit || 'Available at empanelled hospitals.'}</p>

        <div class="spc-box">
          <h4><i class="fa-regular fa-circle-check"></i> Eligibility</h4>
          <p>${s.eligibility || 'As per scheme guidelines.'}</p>
        </div>

        <div class="spc-box">
          <h4><i class="fa-solid fa-indian-rupee-sign"></i> Income Limit</h4>
          <p>${s.income_limit || 'As per government scheme rules.'}</p>
        </div>

        <div class="spc-box">
          <h4><i class="fa-regular fa-file-lines"></i> Documents Required</h4>
          <ul class="spc-list">
            ${(s.documents_required || []).map(d => `<li>${d}</li>`).join('')}
          </ul>
        </div>

        <div class="spc-box">
          <h4><i class="fa-solid fa-list-check"></i> How to Apply</h4>
          <ol class="spc-steps">
            ${(s.how_to_apply || []).map(st => `<li>${st}</li>`).join('')}
          </ol>
        </div>

        <div class="spc-footer"><i class="fa-regular fa-clock"></i> Approval: ${s.approval_time || 'Depends on verification process.'}</div>
      </div>
    `).join('');
  }

  function filterAllSchemes(cat, btn) {
    state.schemeFilter = cat;
    document.querySelectorAll('#page-schemes .scat-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderAllSchemes(cat);
  }

  function searchAllSchemes() {
    renderAllSchemes(state.schemeFilter || 'all');
  }

  // ── Emergency ─────────────────────────────────────────────────────────────
  function openEmergency() {
    document.getElementById('emg-overlay').classList.add('open');
  }
  function closeEmergency() {
    document.getElementById('emg-overlay').classList.remove('open');
  }

  // ── Toast ──────────────────────────────────────────────────────────────────
  function toast(msg, duration = 3000) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), duration);
  }

  // ── Boot ──────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', init);

  // ── Public API ────────────────────────────────────────────────────────────
  return {
    navTo, goBack, changeLang,
    showLogin, showSignup, setLoginMode, requestOtp, login, signup, logout,
    searchDisease, quickSearch, quickActionDiseaseSearch, quickActionHospitalSearch, quickActionHealthAdvice, searchHealthAdvice, findHospitalsForDisease,
    askStarterQuestion, sendChatMessage,
    filterHospitals, filterSpec,
    openHospital, switchTab, filterSchemesCat, bookTokenForCurrent,
    bookTokenById, cancelToken,
    openEmergency, closeEmergency,
    clearHistory,
    filterAllSchemes, searchAllSchemes, filterSchemes: filterSchemesCat,
  };
})();
