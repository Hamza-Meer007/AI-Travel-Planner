/* ============================================================
   AI Travel Planner — app.js
   Coordinates with FastAPI backend at localhost:8000
   ============================================================ */

'use strict';

/* ─── Config ─────────────────────────────────────────────── */
const API_BASE = 'https://hamzameer-travel-ai-planner.hf.space' || 'http://localhost:8000';
const ENDPOINTS = {
  flights: `${API_BASE}/search_flights/`,
  hotels: `${API_BASE}/search_hotels/`,
  complete: `${API_BASE}/complete_search/`,
  itinerary: `${API_BASE}/generate_itinerary/`,
};

const AI_ERROR_PREFIXES = [
  'OpenAI authentication failed.',
  'OpenAI quota exceeded.',
  'OpenAI rate limit reached.',
  'Groq authentication failed.',
  'Groq quota exceeded.',
  'Groq rate limit reached.',
];

function isAiServiceError(msg) {
  if (!msg) return false;
  return AI_ERROR_PREFIXES.some(p => msg.startsWith(p));
}

/* ─── State ──────────────────────────────────────────────── */
let currentMode = 'complete';
let lastResult = null;
let lastMeta = {};

/* ─── DOM refs ───────────────────────────────────────────── */
const $ = id => document.getElementById(id);
const heroSection = $('hero-section');
const loadingSection = $('loading-section');
const resultsSection = $('results-section');

/* ============================================================
   STARS (background decoration)
   ============================================================ */
(function createStars() {
  const container = $('stars');
  if (!container) return;
  for (let i = 0; i < 110; i++) {
    const s = document.createElement('div');
    s.className = 'star';
    const sz = Math.random() * 2 + 0.5;
    s.style.cssText = `
      width:${sz}px; height:${sz}px;
      top:${Math.random() * 100}%;
      left:${Math.random() * 100}%;
      --dur:${(Math.random() * 4 + 2).toFixed(1)}s;
      animation-delay:${(Math.random() * 5).toFixed(1)}s;
    `;
    container.appendChild(s);
  }
})();

/* ============================================================
   DATE DEFAULTS
   ============================================================ */
function toISODate(d) {
  return d.toISOString().split('T')[0];
}

(function setDateDefaults() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);

  const returnDay = new Date(tomorrow);
  returnDay.setDate(returnDay.getDate() + 7);

  $('outbound-date').value = toISODate(tomorrow);
  $('return-date').value = toISODate(returnDay);
  $('check-in-date').value = toISODate(tomorrow);
  $('check-out-date').value = toISODate(returnDay);

  // Set min values
  const todayStr = toISODate(new Date());
  ['outbound-date', 'return-date', 'check-in-date', 'check-out-date']
    .forEach(id => { $(id).min = todayStr; });
})();

// Sync hotel dates to flight dates when they change
$('outbound-date').addEventListener('change', e => {
  if ($('check-in-date').value < e.target.value)
    $('check-in-date').value = e.target.value;
});
$('return-date').addEventListener('change', e => {
  if ($('check-out-date').value < e.target.value)
    $('check-out-date').value = e.target.value;
});

/* ============================================================
   MODE SWITCHING
   ============================================================ */
document.querySelectorAll('.mode-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentMode = btn.dataset.mode;
    applyModeUI();
  });
});

function applyModeUI() {
  const flightSection = $('flight-section');
  const hotelSection = $('hotel-section');
  const useDestRow = $('use-dest-row');

  if (currentMode === 'flights') {
    flightSection.style.display = '';
    hotelSection.style.display = 'none';
  } else if (currentMode === 'hotels') {
    flightSection.style.display = 'none';
    hotelSection.style.display = '';
    useDestRow.style.display = 'none';
    // Always show the location input in hotels-only mode
    $('hotel-location-row').style.display = '';
  } else {
    // complete
    flightSection.style.display = '';
    hotelSection.style.display = '';
    useDestRow.style.display = '';
    // Respect the toggle state
    $('hotel-location-row').style.display = $('use-flight-dest').checked ? 'none' : '';
  }
}

/* ============================================================
   USE-FLIGHT-DESTINATION TOGGLE
   ============================================================ */
$('use-flight-dest').addEventListener('change', function () {
  $('hotel-location-row').style.display = this.checked ? 'none' : '';
});

/* IATA — auto uppercase */
['origin', 'destination'].forEach(id => {
  $(id).addEventListener('input', function () {
    this.value = this.value.toUpperCase().replace(/[^A-Z]/g, '');
  });
});

/* ============================================================
   FORM VALIDATION
   ============================================================ */
function showError(msg) {
  const el = $('form-error');
  el.textContent = msg;
  el.style.display = 'flex';
}
function clearError() {
  const el = $('form-error');
  el.textContent = '';
  el.style.display = 'none';
}

function validateForm() {
  const origin = $('origin').value.trim().toUpperCase();
  const destination = $('destination').value.trim().toUpperCase();
  const outbound = $('outbound-date').value;
  const ret = $('return-date').value;
  const checkIn = $('check-in-date').value;
  const checkOut = $('check-out-date').value;
  const location = $('hotel-location').value.trim();
  const useFlightDest = $('use-flight-dest').checked;

  if (currentMode !== 'hotels') {
    if (!origin || origin.length < 2)
      return { ok: false, msg: 'Please enter a valid origin airport code (e.g. BLR).' };
    if (!destination || destination.length < 2)
      return { ok: false, msg: 'Please enter a valid destination airport code (e.g. DEL).' };
    if (!outbound)
      return { ok: false, msg: 'Please select a departure date.' };
    if (!ret)
      return { ok: false, msg: 'Please select a return date.' };
    if (outbound >= ret)
      return { ok: false, msg: 'Return date must be after departure date.' };
  }

  if (currentMode !== 'flights') {
    if (!useFlightDest && currentMode === 'complete' && !location)
      return { ok: false, msg: 'Please enter a hotel location.' };
    if (currentMode === 'hotels' && !location)
      return { ok: false, msg: 'Please enter a hotel location.' };
    if (!checkIn)
      return { ok: false, msg: 'Please select a check-in date.' };
    if (!checkOut)
      return { ok: false, msg: 'Please select a check-out date.' };
    if (checkIn >= checkOut)
      return { ok: false, msg: 'Check-out date must be after check-in date.' };
  }

  return { ok: true };
}

function gatherPayload() {
  const origin = $('origin').value.trim().toUpperCase();
  const destination = $('destination').value.trim().toUpperCase();
  const outbound = $('outbound-date').value;
  const ret = $('return-date').value;
  const checkIn = $('check-in-date').value;
  const checkOut = $('check-out-date').value;
  const useFlightDest = $('use-flight-dest').checked;
  // In hotels-only mode always use the explicit location field
  const hotelLoc = (currentMode === 'hotels')
    ? $('hotel-location').value.trim()
    : (useFlightDest ? destination : $('hotel-location').value.trim());

  return {
    flightRequest: { origin, destination, outbound_date: outbound, return_date: ret },
    hotelRequest: { location: hotelLoc, check_in_date: checkIn, check_out_date: checkOut },
    meta: { origin, destination, hotelLoc, outbound, ret, checkIn, checkOut },
  };
}

/* ============================================================
   LOADING ANIMATION
   ============================================================ */
function showLoading(mode) {
  heroSection.style.display = 'none';
  resultsSection.style.display = 'none';
  loadingSection.style.display = 'flex';

  // Show/hide steps based on mode
  const steps = {
    'step-flights': mode !== 'hotels',
    'step-hotels': mode !== 'flights',
    'step-ai': true,
    'step-itinerary': mode === 'complete',
  };
  Object.entries(steps).forEach(([id, show]) => {
    $(id).style.display = show ? 'flex' : 'none';
    $(id).classList.remove('done');
    $(id).classList.add('active');
  });
}

function hideLoading() {
  loadingSection.style.display = 'none';
}

/* ============================================================
   FORM SUBMIT
   ============================================================ */
$('search-form').addEventListener('submit', async e => {
  e.preventDefault();
  clearError();

  const v = validateForm();
  if (!v.ok) { showError(v.msg); return; }

  const { flightRequest, hotelRequest, meta } = gatherPayload();
  lastMeta = meta;

  setSearchBtnLoading(true);
  showLoading(currentMode);

  try {
    let result;

    if (currentMode === 'complete') {
      result = await postJSON(ENDPOINTS.complete, {
        flight_request: flightRequest,
        hotel_request: hotelRequest,
      });
    } else if (currentMode === 'flights') {
      result = await postJSON(ENDPOINTS.flights, flightRequest);
    } else {
      result = await postJSON(ENDPOINTS.hotels, hotelRequest);
    }

    lastResult = result;
    hideLoading();
    renderResults(result, currentMode);

  } catch (err) {
    hideLoading();
    heroSection.style.display = '';
    showError(err.message || 'Something went wrong. Make sure the backend server is running on port 8000.');
  } finally {
    setSearchBtnLoading(false);
  }
});

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Server error: ${res.status}`);
  }
  return res.json();
}

function setSearchBtnLoading(loading) {
  const btn = $('search-btn');
  btn.disabled = loading;
  btn.querySelector('.btn-text').textContent = loading ? 'Searching…' : 'Search Now';
}

/* ============================================================
   RENDER RESULTS
   ============================================================ */
function renderResults(data, mode) {
  const { flights = [], hotels = [], ai_flight_recommendation = '',
    ai_hotel_recommendation = '', itinerary = '' } = data;

  // --- AI warning banner ---
  const warnings = [ai_flight_recommendation, ai_hotel_recommendation, itinerary]
    .filter(isAiServiceError);
  if (warnings.length) {
    $('ai-warning').style.display = '';
    $('ai-warning-text').textContent = warnings[0];
  } else {
    $('ai-warning').style.display = 'none';
  }

  // --- Results meta ---
  const { origin, destination, hotelLoc, outbound, ret } = lastMeta;
  let metaText = '';
  if (mode !== 'hotels') metaText += `${origin} → ${destination}  ·  ${outbound} – ${ret}`;
  if (mode === 'complete') metaText += `   |   Hotel: ${hotelLoc}`;
  if (mode === 'hotels') metaText = `Hotel search: ${hotelLoc}`;
  $('results-meta').textContent = metaText;

  // --- Build tabs ---
  buildTabs(mode, flights, hotels);

  // --- Populate panels ---
  renderFlights(flights, origin, destination);
  renderHotels(hotels, hotelLoc || destination);
  renderRecommendations(ai_flight_recommendation, ai_hotel_recommendation, mode);
  renderItinerary(itinerary, destination, outbound);

  // Show results
  resultsSection.style.display = '';
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ─── Tabs ───────────────────────────────────────────────── */
const TAB_CONFIG = {
  complete: [
    { id: 'flights', icon: 'fa-plane', label: 'Flights' },
    { id: 'hotels', icon: 'fa-hotel', label: 'Hotels' },
    { id: 'recommendations', icon: 'fa-star', label: 'AI Picks' },
    { id: 'itinerary', icon: 'fa-calendar-alt', label: 'Itinerary' },
  ],
  flights: [
    { id: 'flights', icon: 'fa-plane', label: 'Flights' },
    { id: 'recommendations', icon: 'fa-star', label: 'AI Picks' },
  ],
  hotels: [
    { id: 'hotels', icon: 'fa-hotel', label: 'Hotels' },
    { id: 'recommendations', icon: 'fa-star', label: 'AI Picks' },
  ],
};

function buildTabs(mode, flights, hotels) {
  const nav = $('tabs-nav');
  nav.innerHTML = '';
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

  const tabs = TAB_CONFIG[mode] || TAB_CONFIG.complete;
  tabs.forEach((t, i) => {
    const btn = document.createElement('button');
    btn.className = 'tab-btn' + (i === 0 ? ' active' : '');
    btn.dataset.tab = t.id;
    btn.setAttribute('role', 'tab');

    let countSpan = '';
    if (t.id === 'flights' && flights.length)
      countSpan = `<span class="tab-count">${flights.length}</span>`;
    if (t.id === 'hotels' && hotels.length)
      countSpan = `<span class="tab-count">${hotels.length}</span>`;

    btn.innerHTML = `<i class="fas ${t.icon}"></i> ${t.label} ${countSpan}`;
    btn.addEventListener('click', () => switchTab(t.id, nav));
    nav.appendChild(btn);
  });

  // Activate first panel
  if (tabs.length) {
    const firstPanel = $(`panel-${tabs[0].id}`);
    if (firstPanel) firstPanel.classList.add('active');
  }
}

function switchTab(tabId, nav) {
  (nav || $('tabs-nav')).querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  const activeBtn = (nav || $('tabs-nav')).querySelector(`[data-tab="${tabId}"]`);
  if (activeBtn) activeBtn.classList.add('active');

  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  const panel = $(`panel-${tabId}`);
  if (panel) panel.classList.add('active');
}

/* ─── Flight Cards ───────────────────────────────────────── */
function renderFlights(flights, origin, destination) {
  $('flights-heading').textContent = `Available Flights: ${origin} → ${destination}`;
  $('flights-count').textContent = flights.length ? `${flights.length} found` : '';

  const grid = $('flights-grid');
  grid.innerHTML = '';

  if (!flights.length) {
    $('flights-empty').style.display = '';
    return;
  }
  $('flights-empty').style.display = 'none';

  flights.forEach((f, i) => {
    const card = document.createElement('div');
    card.className = 'flight-card';
    card.style.animationDelay = `${i * 0.06}s`;

    const stopsClass = getStopsClass(f.stops);
    const logoHtml = f.airline_logo
      ? `<img class="airline-logo" src="${escHtml(f.airline_logo)}" alt="${escHtml(f.airline)}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'" /><div class="airline-logo-fallback" style="display:none"><i class="fas fa-plane"></i></div>`
      : `<div class="airline-logo-fallback"><i class="fas fa-plane"></i></div>`;

    card.innerHTML = `
      <div class="flight-airline">
        ${logoHtml}
        <span class="airline-name">${escHtml(f.airline)}</span>
      </div>
      <div class="flight-route">
        <div class="route-point">
          <span class="route-time">${escHtml(formatTime(f.departure))}</span>
          <span class="route-code">${escHtml(origin)}</span>
        </div>
        <div class="route-mid">
          <div class="route-line">
            <div class="route-dot"></div>
            <div class="route-dashes"></div>
            <i class="fas fa-plane route-plane-icon"></i>
            <div class="route-dashes"></div>
            <div class="route-dot"></div>
          </div>
          <span class="route-duration">${escHtml(formatDuration(f.duration))}</span>
          <span class="stops-badge ${stopsClass}">${escHtml(f.stops)}</span>
        </div>
        <div class="route-point">
          <span class="route-time">${escHtml(formatTime(f.arrival))}</span>
          <span class="route-code">${escHtml(destination)}</span>
        </div>
      </div>
      <div class="flight-price-col">
        <span class="flight-price">${escHtml(formatPrice(f.price))}</span>
        <span class="flight-class">${escHtml(f.travel_class)}</span>
        ${f.return_date ? `<span class="flight-return">Return: ${escHtml(f.return_date)}</span>` : ''}
      </div>
    `;
    grid.appendChild(card);
  });
}

function getStopsClass(stops) {
  if (!stops) return 'direct';
  const s = stops.toLowerCase();
  if (s.includes('nonstop') || s.includes('direct') || s === '0' || s === '0 stop' || s === '0 stops')
    return 'direct';
  if (s.includes('1'))
    return 'one-stop';
  return 'multi-stop';
}

function formatTime(val) {
  if (!val) return '—';
  // Try to extract just HH:MM if full datetime
  const m = val.match(/\b(\d{1,2}:\d{2})\b/);
  return m ? m[1] : val;
}

/* Convert any duration string to "Xh Ym" */
function formatDuration(dur) {
  if (!dur) return '—';
  const s = String(dur).trim();
  // Already "Xh Ym" or "Xh Ymins"
  const hm = s.match(/(\d+)\s*h(?:r|ours?)?\s*(\d+)\s*m(?:in(?:utes?)?)?/i);
  if (hm) return `${hm[1]}h ${hm[2]}m`;
  // Just hours "2h" / "2 hr"
  const ho = s.match(/^(\d+)\s*h(?:r|ours?)?$/i);
  if (ho) return `${ho[1]}h 0m`;
  // Minutes only "950 min" or "950"
  const mi = s.match(/^(\d+)\s*(?:min(?:utes?)?)?$/i);
  if (mi) {
    const total = parseInt(mi[1], 10);
    const h = Math.floor(total / 60);
    const m = total % 60;
    if (h === 0) return `${m}m`;
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  }
  return s;
}

/* Normalise price display to USD format */
function formatPrice(price) {
  if (price == null || price === '') return '—';
  const s = String(price).trim();
  if (!s || s === '—') return s;
  // Already USD
  if (s.startsWith('$')) return s;
  // Strip common non-USD symbols and currency codes, then add $
  const cleaned = s
    .replace(/^[₹€£¥₩＄]/, '')
    .replace(/\s*(USD|EUR|GBP|INR|JPY|CAD|AUD|AED|SGD)\b/gi, '')
    .trim();
  if (/^[\d,. ]+$/.test(cleaned)) return '$' + cleaned;
  // Free / N/A / unknown — return as-is
  return s;
}

/* ─── Hotel Cards ────────────────────────────────────────── */
function renderHotels(hotels, location) {
  $('hotels-heading').textContent = `Available Hotels in ${location}`;
  $('hotels-count').textContent = hotels.length ? `${hotels.length} found` : '';

  const grid = $('hotels-grid');
  grid.innerHTML = '';

  if (!hotels.length) {
    $('hotels-empty').style.display = '';
    return;
  }
  $('hotels-empty').style.display = 'none';

  hotels.forEach((h, i) => {
    const card = document.createElement('div');
    card.className = 'hotel-card';
    card.style.animationDelay = `${i * 0.07}s`;

    const stars = renderStars(h.rating);

    card.innerHTML = `
      <div class="hotel-header">
        <span class="hotel-name">${escHtml(h.name)}</span>
        <span class="hotel-stars" title="${h.rating}/5">${stars}</span>
      </div>
      <div class="hotel-location">
        <i class="fas fa-map-marker-alt" style="color:var(--primary);font-size:0.75rem"></i>
        ${escHtml(h.location)}
      </div>
      <div class="hotel-footer">
        <div class="hotel-price">
          ${escHtml(formatPrice(h.price))}<span> / night</span>
        </div>
        ${h.link
        ? `<a href="${escHtml(h.link)}" target="_blank" rel="noopener noreferrer" class="hotel-link-btn">
               <i class="fas fa-external-link-alt"></i> View
             </a>`
        : ''}
      </div>
    `;
    grid.appendChild(card);
  });
}

function renderStars(rating) {
  // SerpAPI overall_rating is already 0–5 scale
  const r = parseFloat(rating) || 0;
  const stars5 = Math.round(r * 2) / 2; // round to nearest 0.5
  let html = '';
  for (let i = 1; i <= 5; i++) {
    if (stars5 >= i) html += '<i class="fas fa-star"></i>';
    else if (stars5 >= i - 0.5) html += '<i class="fas fa-star-half-alt"></i>';
    else html += '<i class="far fa-star"></i>';
  }
  return html;
}

/* ─── AI Recommendations ─────────────────────────────────── */
function renderRecommendations(flightRec, hotelRec, mode) {
  const flightBlock = $('rec-flight-block');
  const hotelBlock = $('rec-hotel-block');
  const recEmpty = $('rec-empty');

  flightBlock.style.display = 'none';
  hotelBlock.style.display = 'none';
  recEmpty.style.display = 'none';

  let hasContent = false;

  if (mode !== 'hotels' && flightRec) {
    flightBlock.style.display = '';
    const body = $('rec-flight-body');
    if (isAiServiceError(flightRec)) {
      body.innerHTML = `<div class="rec-error"><i class="fas fa-triangle-exclamation"></i>${escHtml(flightRec)}</div>`;
    } else {
      body.innerHTML = safeMarkdown(flightRec);
    }
    hasContent = true;
  }

  if (mode !== 'flights' && hotelRec) {
    hotelBlock.style.display = '';
    const body = $('rec-hotel-body');
    if (isAiServiceError(hotelRec)) {
      body.innerHTML = `<div class="rec-error"><i class="fas fa-triangle-exclamation"></i>${escHtml(hotelRec)}</div>`;
    } else {
      body.innerHTML = safeMarkdown(hotelRec);
    }
    hasContent = true;
  }

  if (!hasContent) recEmpty.style.display = '';
}

/* ─── Itinerary ──────────────────────────────────────────── */
function renderItinerary(itinerary, destination, outboundDate) {
  const body = $('itinerary-body');
  const empty = $('itinerary-empty');
  const dlBtn = $('download-btn');

  if (!itinerary) {
    body.parentElement.style.display = 'none';
    empty.style.display = '';
    dlBtn.style.display = 'none';
    return;
  }

  body.parentElement.style.display = '';
  empty.style.display = 'none';

  if (isAiServiceError(itinerary)) {
    body.innerHTML = `<div class="rec-error"><i class="fas fa-triangle-exclamation"></i>${escHtml(itinerary)}</div>`;
    dlBtn.style.display = 'none';
  } else {
    body.innerHTML = safeMarkdown(itinerary);
    // Wrap every table in a scrollable container so wide tables don't overflow
    body.querySelectorAll('table').forEach(tbl => {
      if (tbl.parentElement.classList.contains('table-scroll')) return;
      const wrap = document.createElement('div');
      wrap.className = 'table-scroll';
      tbl.parentNode.insertBefore(wrap, tbl);
      wrap.appendChild(tbl);
    });
    dlBtn.style.display = 'flex';
    dlBtn.onclick = () => downloadItinerary(itinerary, destination, outboundDate);
  }
}

function downloadItinerary(content, destination, date) {
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `travel_itinerary_${destination}_${date}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

/* ============================================================
   NEW SEARCH
   ============================================================ */
$('new-search-btn').addEventListener('click', () => {
  resultsSection.style.display = 'none';
  heroSection.style.display = '';
  heroSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

/* ============================================================
   HELPERS
   ============================================================ */

// Safe markdown rendering (requires marked.js CDN)
function safeMarkdown(md) {
  if (typeof marked === 'undefined') return `<p>${escHtml(md).replace(/\n/g, '<br>')}</p>`;
  try {
    return marked.parse(md);
  } catch (_) {
    return `<p>${escHtml(md).replace(/\n/g, '<br>')}</p>`;
  }
}

// Basic HTML entity escaping to prevent XSS
function escHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
