// ============================================================
// DOM references
// ============================================================
const els = {
  body: document.body,
  dropzone: document.getElementById('dropzone'),
  fileInput: document.getElementById('file-input'),
  uploadSection: document.getElementById('upload-section'),
  loadingSection: document.getElementById('loading-section'),
  loadingStep: document.getElementById('loading-step'),
  errorSection: document.getElementById('error-section'),
  errorMessage: document.getElementById('error-message'),
  errorDismiss: document.getElementById('error-dismiss'),
  resultsSection: document.getElementById('results-section'),
  fileName: document.getElementById('file-name'),
  docTypeBadge: document.getElementById('doc-type-badge'),
  modeBadge: document.getElementById('mode-badge'),
  modeLabel: document.getElementById('mode-label'),
  savingsPill: document.getElementById('savings-pill'),
  savingsValue: document.getElementById('savings-value'),
  resetBtn: document.getElementById('reset-btn'),
  copyJsonBtn: document.getElementById('copy-json-btn'),
  downloadJsonBtn: document.getElementById('download-json-btn'),
  missingBanner: document.getElementById('missing-banner'),
  missingList: document.getElementById('missing-list'),
  lineItemsBody: document.getElementById('line-items-body'),
  lineCount: document.getElementById('line-count'),
  jsonView: document.getElementById('json-view'),
  rawView: document.getElementById('raw-view'),
  pdfCanvas: document.getElementById('pdf-canvas'),
  pdfHighlight: document.getElementById('pdf-highlight'),
  pdfContainer: document.getElementById('pdf-container'),
  pdfPrev: document.getElementById('pdf-prev'),
  pdfNext: document.getElementById('pdf-next'),
  pdfPageLabel: document.getElementById('pdf-page-label'),
};

const FIELD_LABELS = {
  invoice_number: 'Document number',
  policy_number: 'Policy number',
  incident_date: 'Incident date',
  issue_date: 'Issue date',
  due_date: 'Due date',
  currency: 'Currency',
  subtotal: 'Subtotal',
  tax_rate: 'VAT rate',
  tax_amount: 'VAT amount',
  total: 'Total',
  issued_to: 'Counterparty',
  pay_to: 'Payment details',
  line_items: 'Line items',
};

const NUM_FIELDS = new Set(['subtotal', 'tax_rate', 'tax_amount', 'total', 'quantity', 'unit_price']);
const SAVINGS_KEY = 'uniqa_doc_intel_savings_seconds';
const SECONDS_PER_DOC = 8 * 60; // ~8 minutes saved per processed document

let state = {
  invoice: null,
  raw_text: '',
  mode: '',
  model: null,
  word_boxes: [],
  pages: [],
  pdf_base64: null,
};

let pdfState = {
  doc: null,
  pageNum: 1,
  pageCount: 1,
  currentBoxes: [], // last-highlighted boxes
  renderTask: null,
};

let pdfjsReady = !!window.pdfjsLib;
window.addEventListener('pdfjs-ready', () => { pdfjsReady = true; });

function refreshIcons() {
  if (window.lucide) window.lucide.createIcons();
}

// ============================================================
// Section toggles
// ============================================================
function show(section) {
  for (const key of ['uploadSection', 'loadingSection', 'errorSection', 'resultsSection']) {
    els[key].classList.toggle('hidden', els[key] !== section);
  }
}

function setMode(mode, model) {
  if (!mode) {
    els.modeBadge.classList.add('hidden');
    els.modeBadge.classList.remove('inline-flex');
    return;
  }
  els.modeBadge.classList.remove('hidden');
  els.modeBadge.classList.add('inline-flex');
  const dot = els.modeBadge.querySelector('span:first-child');
  if (mode === 'llm') {
    els.modeLabel.textContent = `${model || 'Claude'} extraction`;
    dot.className = 'h-1.5 w-1.5 rounded-full bg-emerald-500';
    els.modeBadge.className = 'inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700';
  } else {
    els.modeLabel.textContent = 'Heuristic extraction (no API key)';
    dot.className = 'h-1.5 w-1.5 rounded-full bg-amber-500';
    els.modeBadge.className = 'inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700';
  }
}

// ============================================================
// Nested getter/setter for paths like "issued_to.name"
// ============================================================
function getNested(obj, path) {
  return path.split('.').reduce((acc, k) => (acc == null ? null : acc[k]), obj);
}
function setNested(obj, path, value) {
  const keys = path.split('.');
  let cur = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    if (cur[keys[i]] == null) cur[keys[i]] = {};
    cur = cur[keys[i]];
  }
  cur[keys[keys.length - 1]] = value;
}

// ============================================================
// Time-saved counter (localStorage)
// ============================================================
function loadSavings() {
  const v = parseInt(localStorage.getItem(SAVINGS_KEY) || '0', 10);
  return Number.isFinite(v) ? v : 0;
}
function saveSavings(seconds) {
  localStorage.setItem(SAVINGS_KEY, String(seconds));
}
function formatSavings(seconds) {
  if (!seconds) return '0 min';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m} min`;
}
function renderSavings(animate = false) {
  const seconds = loadSavings();
  els.savingsValue.textContent = formatSavings(seconds);
  if (seconds > 0) {
    els.savingsPill.classList.remove('hidden');
    els.savingsPill.classList.add('md:flex');
  }
  if (animate) {
    els.savingsPill.classList.remove('bumped');
    // force reflow then re-add to restart animation
    void els.savingsPill.offsetWidth;
    els.savingsPill.classList.add('bumped');
  }
}
function bumpSavings() {
  const current = loadSavings();
  saveSavings(current + SECONDS_PER_DOC);
  renderSavings(true);
}

// ============================================================
// PDF.js rendering
// ============================================================
function base64ToUint8Array(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function loadPdf(base64) {
  if (!pdfjsReady) {
    await new Promise((resolve) => window.addEventListener('pdfjs-ready', resolve, { once: true }));
  }
  const data = base64ToUint8Array(base64);
  pdfState.doc = await window.pdfjsLib.getDocument({ data }).promise;
  pdfState.pageCount = pdfState.doc.numPages;
  pdfState.pageNum = 1;
  updatePagerUI();
  await renderPage(1);
}

function updatePagerUI() {
  els.pdfPageLabel.textContent = `${pdfState.pageNum} / ${pdfState.pageCount}`;
  els.pdfPrev.disabled = pdfState.pageNum <= 1;
  els.pdfNext.disabled = pdfState.pageNum >= pdfState.pageCount;
}

async function renderPage(num) {
  if (!pdfState.doc) return;
  if (pdfState.renderTask) {
    try { pdfState.renderTask.cancel(); } catch (e) {}
  }
  const page = await pdfState.doc.getPage(num);
  const containerWidth = els.pdfContainer.clientWidth || 480;
  const baseViewport = page.getViewport({ scale: 1 });
  const scale = containerWidth / baseViewport.width;
  const viewport = page.getViewport({ scale });

  const canvas = els.pdfCanvas;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(viewport.width * dpr);
  canvas.height = Math.floor(viewport.height * dpr);
  canvas.style.height = `${viewport.height}px`;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  pdfState.renderTask = page.render({ canvasContext: ctx, viewport });
  try {
    await pdfState.renderTask.promise;
  } catch (err) {
    if (err && err.name !== 'RenderingCancelledException') console.error(err);
  }

  // Resize highlight overlay to match
  const hl = els.pdfHighlight;
  hl.width = canvas.width;
  hl.height = canvas.height;
  hl.style.height = `${viewport.height}px`;

  drawHighlights();
}

// ============================================================
// Click-to-highlight: find PDF word boxes matching a field value
// ============================================================
function normalizeForSearch(s) {
  return String(s).toLowerCase().replace(/[$€£,]/g, '').replace(/\s+/g, ' ').trim();
}

function searchTermsForValue(value) {
  const v = String(value).trim();
  if (!v) return [];
  const terms = [];

  // ISO date -> DD.MM.YYYY (common in SK/AT/DE docs)
  const dateMatch = v.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (dateMatch) {
    const [, y, m, d] = dateMatch;
    terms.push(`${d}.${m}.${y}`);
    terms.push(`${parseInt(d, 10)}.${parseInt(m, 10)}.${y}`);
    terms.push(`${m}/${d}/${y}`);
    return terms;
  }

  // Numeric value: strip currency + commas
  const numeric = v.replace(/[$€£,\s]/g, '');
  if (/^-?\d+(\.\d+)?$/.test(numeric)) {
    terms.push(numeric);
    const asFloat = parseFloat(numeric);
    if (Number.isInteger(asFloat)) {
      terms.push(`${asFloat}.00`);
    } else {
      terms.push(String(Math.trunc(asFloat)));
    }
    return terms;
  }

  // Generic string: tokenize, drop trivial tokens
  const tokens = v.split(/[\s,]+/).filter((t) => t.length >= 2);
  return tokens.length ? tokens : [v];
}

function findBoxesForValue(value) {
  const terms = searchTermsForValue(value);
  if (!terms.length) return [];
  const matches = [];
  for (const term of terms) {
    const t = normalizeForSearch(term);
    if (!t) continue;
    for (const box of state.word_boxes) {
      if (box.page !== pdfState.pageNum - 1) continue;
      const boxText = normalizeForSearch(box.text);
      if (!boxText) continue;
      if (boxText === t || boxText.includes(t) || t.includes(boxText)) {
        matches.push(box);
      }
    }
    if (matches.length) break; // first matching term is enough
  }
  return matches;
}

function highlightField(fieldPath) {
  if (!state.invoice) return;
  const value = getNested(state.invoice, fieldPath);
  if (value == null || value === '') {
    pdfState.currentBoxes = [];
    drawHighlights();
    return;
  }
  pdfState.currentBoxes = findBoxesForValue(value);
  drawHighlights();
}

function drawHighlights() {
  const hl = els.pdfHighlight;
  const ctx = hl.getContext('2d');
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, hl.width, hl.height);
  if (!pdfState.currentBoxes.length || !state.pages.length) return;

  const page = state.pages[pdfState.pageNum - 1];
  if (!page) return;
  const sx = hl.width / page.width;
  const sy = hl.height / page.height;

  ctx.fillStyle = 'rgba(255, 196, 0, 0.32)';
  ctx.strokeStyle = '#FF9F00';
  ctx.lineWidth = 1.5;

  for (const box of pdfState.currentBoxes) {
    if (box.page !== pdfState.pageNum - 1) continue;
    const x = box.x0 * sx;
    const y = box.y0 * sy;
    const w = (box.x1 - box.x0) * sx;
    const h = (box.y1 - box.y0) * sy;
    const pad = 1.5;
    ctx.fillRect(x - pad, y - pad, w + pad * 2, h + pad * 2);
    ctx.strokeRect(x - pad, y - pad, w + pad * 2, h + pad * 2);
  }
}

// ============================================================
// Results rendering
// ============================================================
function renderResults(payload) {
  state = {
    invoice: payload.invoice,
    raw_text: payload.raw_text || '',
    mode: payload.mode || '',
    model: payload.model || null,
    word_boxes: payload.word_boxes || [],
    pages: payload.pages || [],
    pdf_base64: payload.pdf_base64 || null,
  };

  // Document type styling toggles
  const docType = payload.invoice.document_type || 'invoice';
  els.body.dataset.docType = docType;
  if (docType === 'claim_form') {
    els.docTypeBadge.textContent = 'Claim form';
    els.docTypeBadge.classList.remove('hidden');
  } else if (docType === 'invoice') {
    els.docTypeBadge.textContent = 'Invoice';
    els.docTypeBadge.classList.remove('hidden');
  } else {
    els.docTypeBadge.classList.add('hidden');
  }

  setMode(payload.mode, payload.model);

  // Bind fields
  document.querySelectorAll('[data-bind]').forEach((input) => {
    const path = input.dataset.bind;
    const value = getNested(state.invoice, path);
    input.value = value == null ? '' : value;

    input.oninput = () => {
      const v = input.value.trim();
      const leaf = path.split('.').pop();
      const parsed = v === '' ? null : (NUM_FIELDS.has(leaf) ? Number(v) : v);
      setNested(state.invoice, path, parsed);
      updateJsonView();
    };
    input.onfocus = () => highlightField(path);
    input.onclick = () => highlightField(path);
  });

  // Missing field highlights
  const missing = new Set(payload.invoice.missing_fields || []);
  document.querySelectorAll('.field[data-field]').forEach((field) => {
    const name = field.dataset.field;
    const topLevel = name.split('.')[0];
    field.classList.toggle('missing', missing.has(topLevel) || missing.has(name));
  });
  if (missing.size > 0) {
    els.missingBanner.classList.remove('hidden');
    els.missingBanner.classList.add('flex');
    const names = [...missing].map((m) => FIELD_LABELS[m] || m).join(', ');
    els.missingList.textContent = `Model could not confidently extract: ${names}.`;
  } else {
    els.missingBanner.classList.add('hidden');
    els.missingBanner.classList.remove('flex');
  }

  // Line items
  const items = payload.invoice.line_items || [];
  els.lineCount.textContent = `${items.length} ${items.length === 1 ? 'item' : 'items'}`;
  els.lineItemsBody.innerHTML = '';
  items.forEach((item, idx) => {
    const tr = document.createElement('tr');
    tr.className = 'line-item-row';
    tr.innerHTML = `
      <td class="py-1 pr-4"><input type="text" value="${esc(item.description)}" data-line="${idx}" data-key="description" /></td>
      <td class="py-1 pr-4 w-20"><input type="number" step="0.01" value="${esc(item.quantity)}" data-line="${idx}" data-key="quantity" /></td>
      <td class="py-1 pr-4 w-28"><input type="number" step="0.01" value="${esc(item.unit_price)}" data-line="${idx}" data-key="unit_price" /></td>
      <td class="py-1 w-28"><input type="number" step="0.01" value="${esc(item.total)}" data-line="${idx}" data-key="total" /></td>
    `;
    els.lineItemsBody.appendChild(tr);
  });
  els.lineItemsBody.querySelectorAll('input').forEach((inp) => {
    inp.oninput = () => {
      const i = Number(inp.dataset.line);
      const k = inp.dataset.key;
      const v = inp.value.trim();
      state.invoice.line_items[i][k] = v === '' ? null : (NUM_FIELDS.has(k) ? Number(v) : v);
      updateJsonView();
    };
    inp.onfocus = () => {
      const v = inp.value;
      if (v) {
        pdfState.currentBoxes = findBoxesForValue(v);
        drawHighlights();
      }
    };
  });

  els.rawView.textContent = state.raw_text || '(no text extracted)';
  updateJsonView();
  show(els.resultsSection);
  refreshIcons();

  // Load the PDF preview
  if (state.pdf_base64) {
    loadPdf(state.pdf_base64).catch((err) => {
      console.error('PDF render failed:', err);
    });
  }

  // Bump time-saved counter
  bumpSavings();
}

function esc(value) {
  if (value == null) return '';
  return String(value).replace(/"/g, '&quot;');
}

function updateJsonView() {
  els.jsonView.textContent = JSON.stringify(state.invoice, null, 2);
}

// ============================================================
// Upload pipeline
// ============================================================
async function uploadFile(file) {
  if (!file) return;
  els.fileName.textContent = file.name;
  show(els.loadingSection);
  els.loadingStep.textContent = 'Uploading PDF…';

  const formData = new FormData();
  formData.append('file', file);

  try {
    els.loadingStep.textContent = 'Extracting structured data…';
    const resp = await fetch('/extract', { method: 'POST', body: formData });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    const payload = await resp.json();
    renderResults(payload);
  } catch (err) {
    els.errorMessage.textContent = err.message || String(err);
    show(els.errorSection);
  }
}

async function loadSample(kind) {
  show(els.loadingSection);
  els.loadingStep.textContent = `Loading sample ${kind}…`;
  try {
    const resp = await fetch(`/sample/${kind}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const blob = await resp.blob();
    const file = new File([blob], `${kind}.pdf`, { type: 'application/pdf' });
    await uploadFile(file);
  } catch (err) {
    els.errorMessage.textContent = `Could not load sample: ${err.message}`;
    show(els.errorSection);
  }
}

// ============================================================
// Event wiring
// ============================================================
els.dropzone.addEventListener('click', (e) => {
  if (e.target.closest('button')) return;
  els.fileInput.click();
});

['dragover', 'drop'].forEach((evt) => {
  window.addEventListener(evt, (e) => e.preventDefault());
});

els.dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'copy';
  els.dropzone.classList.add('drag-over');
});
els.dropzone.addEventListener('dragleave', (e) => {
  if (e.target === els.dropzone) els.dropzone.classList.remove('drag-over');
});
els.dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  els.dropzone.classList.remove('drag-over');
  const file = e.dataTransfer.files && e.dataTransfer.files[0];
  if (file) uploadFile(file);
});

els.fileInput.addEventListener('change', (e) => {
  const file = e.target.files && e.target.files[0];
  if (file) uploadFile(file);
});

document.querySelectorAll('.sample-btn').forEach((btn) => {
  btn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    loadSample(btn.dataset.sample || 'claim');
  });
});

els.resetBtn.addEventListener('click', () => {
  state = { invoice: null, raw_text: '', mode: '', model: null, word_boxes: [], pages: [], pdf_base64: null };
  pdfState = { doc: null, pageNum: 1, pageCount: 1, currentBoxes: [], renderTask: null };
  els.fileInput.value = '';
  setMode(null);
  show(els.uploadSection);
});

els.errorDismiss.addEventListener('click', () => show(els.uploadSection));

els.copyJsonBtn.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(JSON.stringify(state.invoice, null, 2));
    const label = els.copyJsonBtn.querySelector('span');
    const original = label.textContent;
    label.textContent = 'Copied!';
    setTimeout(() => (label.textContent = original), 1500);
  } catch (err) { console.error(err); }
});

els.downloadJsonBtn.addEventListener('click', () => {
  const blob = new Blob([JSON.stringify(state.invoice, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${(els.fileName.textContent || 'document').replace(/\.pdf$/i, '')}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

// PDF pagination
els.pdfPrev.addEventListener('click', async () => {
  if (pdfState.pageNum > 1) {
    pdfState.pageNum--;
    pdfState.currentBoxes = [];
    updatePagerUI();
    await renderPage(pdfState.pageNum);
  }
});
els.pdfNext.addEventListener('click', async () => {
  if (pdfState.pageNum < pdfState.pageCount) {
    pdfState.pageNum++;
    pdfState.currentBoxes = [];
    updatePagerUI();
    await renderPage(pdfState.pageNum);
  }
});

// Re-render PDF on window resize (debounced)
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    if (pdfState.doc) renderPage(pdfState.pageNum);
  }, 200);
});

// Tabs
document.querySelectorAll('.tab-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach((b) => {
      const active = b === btn;
      b.classList.toggle('border-uniqa-blue', active);
      b.classList.toggle('text-uniqa-navy', active);
      b.classList.toggle('border-transparent', !active);
      b.classList.toggle('text-slate-500', !active);
    });
    document.querySelectorAll('.tab-panel').forEach((p) => p.classList.add('hidden'));
    document.getElementById(`tab-${target}`).classList.remove('hidden');
  });
});

// Init
renderSavings(false);
refreshIcons();
