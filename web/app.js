const state = {
  runs: [],
  loading: false,
  error: '',
  selectedRunId: '',
  inspectorRun: null,
};

const ids = ['providerFilter', 'promptSetFilter', 'domainFilter', 'competitorFilter'];
const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.tab-panel');

for (const tab of tabs) {
  tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
  });
}

function avg(nums) {
  return nums.length ? (nums.reduce((a, b) => a + b, 0) / nums.length) : 0;
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function normalizeRun(run) {
  return {
    ...run,
    citations: safeArray(run.citations),
    rawOutput: run.rawOutput || '',
  };
}

function getDomainQuery() {
  return domainFilter.value && domainFilter.value !== 'all' ? domainFilter.value : '';
}

async function fetchRuns() {
  state.loading = true;
  state.error = '';
  render();

  try {
    const domain = getDomainQuery();
    const url = domain ? `/api/analysis/runs?domain=${encodeURIComponent(domain)}` : '/api/analysis/runs';
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch runs (${response.status})`);
    }

    const payload = await response.json();
    const runs = Array.isArray(payload) ? payload : payload.runs;
    state.runs = safeArray(runs).map(normalizeRun);

    refillFilters();

    if (!state.runs.some(run => run.id === state.selectedRunId)) {
      state.selectedRunId = state.runs[0]?.id || '';
    }

    await fetchInspectorRun(state.selectedRunId);
  } catch (error) {
    state.error = error.message || 'Unable to fetch runs.';
    state.runs = [];
    refillFilters();
    clearInspector();
  } finally {
    state.loading = false;
    render();
  }
}

async function fetchInspectorRun(id) {
  if (!id) {
    clearInspector();
    return;
  }

  try {
    const response = await fetch(`/api/analysis/runs/${encodeURIComponent(id)}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch run details (${response.status})`);
    }

    const payload = await response.json();
    state.inspectorRun = normalizeRun(payload.run || payload);
  } catch {
    state.inspectorRun = state.runs.find(run => run.id === id) || null;
  }
}

function clearInspector() {
  state.inspectorRun = null;
  rawOutput.textContent = '';
  citationList.innerHTML = '';
}

function uniqueRuns(field) {
  return [...new Set(state.runs.map(r => r[field]).filter(Boolean))];
}

function refillFilters() {
  for (const id of ids) {
    const el = document.getElementById(id);
    const previousValue = el.value;
    const field = id.replace('Filter', '');
    const defaultLabel = el.options[0]?.textContent || 'All';

    el.innerHTML = `<option value="all">${defaultLabel}</option>`;
    uniqueRuns(field).forEach(value => {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = value;
      el.appendChild(opt);
    });

    el.value = [...el.options].some(option => option.value === previousValue) ? previousValue : 'all';
  }

  const previousRunValue = runSelector.value;
  runSelector.innerHTML = '';
  state.runs.forEach(run => {
    const opt = document.createElement('option');
    opt.value = run.id;
    opt.textContent = `${run.id} · ${run.provider || 'Unknown'} · ${run.prompt || 'Untitled prompt'}`;
    runSelector.appendChild(opt);
  });

  if (!runSelector.options.length) {
    state.selectedRunId = '';
    return;
  }

  const nextRunId = state.runs.some(run => run.id === previousRunValue)
    ? previousRunValue
    : state.selectedRunId || state.runs[0].id;

  runSelector.value = nextRunId;
  state.selectedRunId = nextRunId;
}

function filteredRuns() {
  const days = Number(dateRange.value);
  const end = new Date();
  end.setHours(23, 59, 59, 999);
  const start = new Date(end);
  start.setDate(end.getDate() - days);

  return state.runs.filter(r => {
    const date = new Date(r.date);
    const inRange = !Number.isNaN(date.valueOf()) ? date >= start && date <= end : true;

    return inRange
      && (providerFilter.value === 'all' || r.provider === providerFilter.value)
      && (promptSetFilter.value === 'all' || r.promptSet === promptSetFilter.value)
      && (domainFilter.value === 'all' || r.domain === domainFilter.value)
      && (competitorFilter.value === 'all' || r.competitorSet === competitorFilter.value);
  });
}

function renderScorecards(data) {
  const visibility = avg(data.map(d => d.visibility || 0));
  const quality = avg(data.map(d => d.quality || 0));
  const mentionRate = data.length ? (data.filter(d => (d.visibility || 0) >= 60).length / data.length) * 100 : 0;
  const citationShare = data.length ? (data.filter(d => safeArray(d.citations).some(c => c.includes(d.domain || ''))).length / data.length) * 100 : 0;

  scorecards.innerHTML = [
    ['Visibility Score', visibility.toFixed(1)],
    ['Performance Score', quality.toFixed(1)],
    ['Mention Rate', `${mentionRate.toFixed(0)}%`],
    ['Citation Share', `${citationShare.toFixed(0)}%`],
  ].map(([label, value]) => `<div class="metric"><div class="label">${label}</div><div class="value">${value}</div></div>`).join('');
}

function drawTrend(data) {
  const canvas = trendChart;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const sorted = [...data].sort((a, b) => (a.date || '').localeCompare(b.date || ''));
  if (!sorted.length) return;
  const pad = 28;
  const w = canvas.width - pad * 2;
  const h = canvas.height - pad * 2;
  ctx.strokeStyle = '#cbd5e1';
  ctx.strokeRect(pad, pad, w, h);
  ctx.beginPath();
  ctx.strokeStyle = '#2563eb';
  ctx.lineWidth = 2;
  sorted.forEach((r, i) => {
    const x = pad + (i / (sorted.length - 1 || 1)) * w;
    const y = pad + h - ((r.visibility || 0) / 100) * h;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
    ctx.fillStyle = '#111827';
    ctx.fillText((r.date || '').slice(5), x - 14, canvas.height - 7);
  });
  ctx.stroke();
}

function drawDonut(data) {
  const canvas = donutChart;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const own = data.reduce((n, r) => n + safeArray(r.citations).filter(c => c.includes(r.domain || '')).length, 0);
  const comp = data.reduce((n, r) => n + safeArray(r.citations).filter(c => !c.includes(r.domain || '')).length, 0);
  const total = Math.max(own + comp, 1);
  const cx = 140;
  const cy = 130;
  const radius = 90;
  let a0 = -Math.PI / 2;
  [[own, '#2563eb', 'Tracked'], [comp, '#f59e0b', 'Competitor']].forEach(([v, color, label], i) => {
    const a1 = a0 + (v / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, a0, a1);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    a0 = a1;
    ctx.fillStyle = '#111';
    ctx.fillText(`${label}: ${v}`, 8, 20 + i * 18);
  });
  ctx.beginPath();
  ctx.fillStyle = 'white';
  ctx.arc(cx, cy, 45, 0, Math.PI * 2);
  ctx.fill();
}

function drawBar(data) {
  const canvas = barChart;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const by = {};
  data.forEach(r => {
    by[r.provider] = (by[r.provider] || 0) + safeArray(r.citations).length;
  });
  const entries = Object.entries(by);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  entries.forEach(([k, v], i) => {
    const y = 20 + i * 56;
    const width = (v / max) * 250;
    ctx.fillStyle = '#3b82f6';
    ctx.fillRect(90, y, width, 24);
    ctx.fillStyle = '#111';
    ctx.fillText(k, 10, y + 16);
    ctx.fillText(String(v), 350, y + 16);
  });
}

function renderPromptTable(data) {
  promptTableBody.innerHTML = data.map(r => `<tr><td>${r.prompt || ''}</td><td>${r.provider || ''}</td><td>${r.visibility || 0}</td><td>${r.quality || 0}</td><td>${safeArray(r.citations).length}</td></tr>`).join('');
}

function renderHeatmap(data) {
  const prompts = [...new Set(data.map(d => d.prompt).filter(Boolean))];
  const providers = [...new Set(data.map(d => d.provider).filter(Boolean))];
  heatmap.style.gridTemplateColumns = `180px repeat(${providers.length}, 1fr)`;
  let html = '<div></div>' + providers.map(p => `<div><strong>${p}</strong></div>`).join('');
  prompts.forEach(prompt => {
    html += `<div><strong>${prompt}</strong></div>`;
    providers.forEach(provider => {
      const run = data.find(r => r.prompt === prompt && r.provider === provider);
      const score = run ? (run.visibility || 0) : 0;
      const alpha = Math.max(0.1, score / 100);
      html += `<div style="background: rgba(37,99,235,${alpha})">${score || '-'}</div>`;
    });
  });
  heatmap.innerHTML = html;
}

function renderProviderComparison(data) {
  const by = {};
  data.forEach(r => {
    by[r.provider] ??= [];
    by[r.provider].push(r);
  });
  providerTableBody.innerHTML = Object.entries(by).map(([provider, rows]) => {
    const v = avg(rows.map(r => r.visibility || 0));
    const q = avg(rows.map(r => r.quality || 0));
    const share = rows.length ? (rows.filter(r => safeArray(r.citations).some(c => c.includes(r.domain || ''))).length / rows.length) * 100 : 0;
    const c = avg(rows.map(r => safeArray(r.citations).length));
    return `<tr><td>${provider}</td><td>${v.toFixed(1)}</td><td>${q.toFixed(1)}</td><td>${share.toFixed(0)}%</td><td>${c.toFixed(1)}</td></tr>`;
  }).join('');
}

function renderInsights(data) {
  const low = data.filter(r => (r.visibility || 0) < 60 || (r.quality || 0) < 60).slice(0, 3);
  insights.innerHTML = low.map(r => `
    <article class="insight">
      <strong>${r.prompt || 'Untitled prompt'}</strong>
      <p>${r.provider || 'Provider'} scored ${r.visibility || 0} visibility and ${r.quality || 0} quality. Recommendation: refresh the linked page for ${r.promptSet || 'this prompt set'} with stronger evidence and comparison schema.</p>
      <small>Linked page: /content/${(r.prompt || 'untitled').toLowerCase().replace(/\s+/g, '-')}</small>
    </article>
  `).join('') || '<p>No low-scoring prompts in current filter window.</p>';
}

function renderInspector() {
  const run = state.inspectorRun || state.runs.find(r => r.id === state.selectedRunId);
  if (!run) {
    rawOutput.textContent = 'No run selected.';
    citationList.innerHTML = '';
    return;
  }

  rawOutput.textContent = run.rawOutput || '';
  citationList.innerHTML = safeArray(run.citations).map(c => `<li>${c}</li>`).join('');
}

function renderStatus(data) {
  if (state.loading) {
    dataStatus.textContent = 'Loading runs…';
    return;
  }

  if (state.error) {
    dataStatus.textContent = state.error;
    return;
  }

  if (!state.runs.length) {
    dataStatus.textContent = 'No runs available yet. Analyze a URL to create one.';
    return;
  }

  if (!data.length) {
    dataStatus.textContent = 'No runs matched your current filters.';
    return;
  }

  dataStatus.textContent = '';
}

function exportData(type) {
  const data = filteredRuns();
  if (type === 'json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    downloadBlob(blob, 'run-level-data.json');
    return;
  }

  const headers = ['id', 'date', 'provider', 'promptSet', 'domain', 'competitorSet', 'prompt', 'visibility', 'quality', 'citations'];
  const rows = data.map(r => headers.map(h => (h === 'citations' ? safeArray(r.citations).join('|') : (r[h] ?? ''))));
  const csv = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  downloadBlob(blob, 'run-level-data.csv');
}

function downloadBlob(blob, filename) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

async function analyzeUrl() {
  const url = analyzeUrlInput.value.trim();
  if (!url) {
    dataStatus.textContent = 'Enter a URL to analyze.';
    return;
  }

  dataStatus.textContent = 'Submitting analysis…';
  try {
    const body = { url };
    if (providerFilter.value !== 'all') body.providers = [providerFilter.value];
    if (promptSetFilter.value !== 'all') body.promptSet = promptSetFilter.value;

    const response = await fetch('/api/analysis/runs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Failed to analyze URL (${response.status})`);
    }

    analyzeUrlInput.value = '';
    await fetchRuns();
  } catch (error) {
    state.error = error.message || 'Unable to start analysis.';
    render();
  }
}

function render() {
  const data = filteredRuns();
  renderStatus(data);

  if (!data.length) {
    scorecards.innerHTML = '';
    promptTableBody.innerHTML = '';
    heatmap.innerHTML = '';
    providerTableBody.innerHTML = '';
    drawTrend([]);
    drawDonut([]);
    drawBar([]);
    renderInsights([]);
    renderInspector();
    return;
  }

  renderScorecards(data);
  drawTrend(data);
  drawDonut(data);
  drawBar(data);
  renderPromptTable(data);
  renderHeatmap(data);
  renderProviderComparison(data);
  renderInsights(data);
  renderInspector();
}

[dateRange, providerFilter, promptSetFilter, competitorFilter].forEach(el => {
  el.addEventListener('change', render);
});

domainFilter.addEventListener('change', fetchRuns);
runSelector.addEventListener('change', async () => {
  state.selectedRunId = runSelector.value;
  await fetchInspectorRun(state.selectedRunId);
  renderInspector();
});

analyzeUrlButton.addEventListener('click', analyzeUrl);
exportCsv.addEventListener('click', () => exportData('csv'));
exportJson.addEventListener('click', () => exportData('json'));

fetchRuns();
