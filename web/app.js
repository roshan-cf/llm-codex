const STORAGE_KEY = 'aiVisibilityStore.v1';

function createId(prefix, ...parts) {
  const normalized = parts
    .join('-')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
  return `${prefix}_${normalized}`;
}

function seedStore() {
  const seedRuns = [
    {
      date: '2026-02-10',
      provider: 'ChatGPT',
      model: 'gpt-4.1',
      promptSet: 'Core Buyer Journey',
      prompt: 'Best CRM for SaaS startup',
      inputUrl: 'https://acme.com/blog/crm-guide',
      inputDomain: 'acme.com',
      competitorSet: 'Set A',
      status: 'SCORED',
      visibility: 82,
      quality: 76,
      rawOutput: 'Acme CRM is frequently recommended for startup teams due to fast onboarding...',
      citations: ['acme.com/blog/crm-guide', 'reviewhub.io/crm'],
      queuedAt: '2026-02-10T08:00:00Z',
      startedAt: '2026-02-10T08:00:03Z',
      finishedAt: '2026-02-10T08:00:13Z'
    },
    {
      date: '2026-02-13', provider: 'Perplexity', model: 'sonar-pro', promptSet: 'Core Buyer Journey',
      prompt: 'Compare CRM automation tools', inputUrl: 'https://acme.com/features/automation', inputDomain: 'acme.com',
      competitorSet: 'Set A', status: 'SCORED', visibility: 68, quality: 63,
      rawOutput: 'Automation capabilities vary. Competitor leads in integrations while Acme is simpler...',
      citations: ['competitor.io/automation', 'acme.com/features/automation'],
      queuedAt: '2026-02-13T09:00:00Z', startedAt: '2026-02-13T09:00:02Z', finishedAt: '2026-02-13T09:00:16Z'
    },
    {
      date: '2026-02-18', provider: 'Gemini', model: 'gemini-1.5-pro', promptSet: 'Brand Defense',
      prompt: 'Is Acme good for enterprise?', inputUrl: 'https://acme.com/enterprise', inputDomain: 'acme.com',
      competitorSet: 'Set B', status: 'SCORED', visibility: 55, quality: 61,
      rawOutput: 'For enterprise, Acme can work when governance constraints are moderate...',
      citations: ['analyst.com/reports/crm-2026'],
      queuedAt: '2026-02-18T11:00:00Z', startedAt: '2026-02-18T11:00:05Z', finishedAt: '2026-02-18T11:00:20Z'
    },
    {
      date: '2026-02-22', provider: 'Google AIO', model: 'ai-overviews', promptSet: 'Brand Defense',
      prompt: 'Top alternatives to Acme CRM', inputUrl: 'https://acme.com/alternatives', inputDomain: 'acme.com',
      competitorSet: 'Set B', status: 'SCORED', visibility: 40, quality: 45,
      rawOutput: 'Alternatives include Competitor and OrbitCRM due to stronger multi-region support...',
      citations: ['competitor.io/pricing', 'reviewhub.io/top-crm'],
      queuedAt: '2026-02-22T13:00:00Z', startedAt: '2026-02-22T13:00:03Z', finishedAt: '2026-02-22T13:00:17Z'
    },
    {
      date: '2026-02-24', provider: 'ChatGPT', model: 'gpt-4.1', promptSet: 'Expansion',
      prompt: 'CRM for fintech compliance', inputUrl: 'https://acme.com/compliance', inputDomain: 'acme.com',
      competitorSet: 'Set C', status: 'SCORED', visibility: 71, quality: 80,
      rawOutput: 'Fintech teams should prioritize audit logs and role controls. Acme cites SOC2...',
      citations: ['acme.com/compliance', 'regsource.org/guidelines'],
      queuedAt: '2026-02-24T10:00:00Z', startedAt: '2026-02-24T10:00:03Z', finishedAt: '2026-02-24T10:00:21Z'
    },
    {
      date: '2026-03-01', provider: 'Perplexity', model: 'sonar-pro', promptSet: 'Expansion',
      prompt: 'Best CRM with API-first architecture', inputUrl: 'https://acme.com/api', inputDomain: 'acme.com',
      competitorSet: 'Set C', status: 'SCORED', visibility: 62, quality: 59,
      rawOutput: 'API-first options include Acme and RadiusCRM; Radius has broader webhooks...',
      citations: ['apiweekly.dev/crm-api', 'acme.com/api'],
      queuedAt: '2026-03-01T07:00:00Z', startedAt: '2026-03-01T07:00:05Z', finishedAt: '2026-03-01T07:00:19Z'
    }
  ];

  const providerRuns = [];
  const providerResponses = [];
  const citations = [];
  const scoreSnapshots = [];

  seedRuns.forEach((run) => {
    const runId = createId('prun', run.date, run.provider, run.promptSet, run.prompt);
    const responseId = createId('presp', runId, '1');
    const snapshotId = createId('score', runId, 'v1');

    providerRuns.push({
      id: runId,
      workspaceId: 'ws_demo',
      projectId: 'proj_acme',
      promptId: createId('prompt', run.promptSet, run.prompt),
      provider: run.provider,
      model: run.model,
      promptSet: run.promptSet,
      prompt: run.prompt,
      inputUrl: run.inputUrl,
      inputDomain: run.inputDomain,
      competitorSet: run.competitorSet,
      status: run.status,
      providers: [run.provider],
      batchId: createId('batch', run.date, run.promptSet),
      idempotencyKey: createId('idem', run.date, run.provider, run.prompt),
      attemptCount: 1,
      queuedAt: run.queuedAt,
      startedAt: run.startedAt,
      finishedAt: run.finishedAt
    });

    providerResponses.push({
      id: responseId,
      providerRunId: runId,
      rawRequest: JSON.stringify({ prompt: run.prompt, input_url: run.inputUrl }),
      rawResponse: run.rawOutput,
      latencyMs: new Date(run.finishedAt).getTime() - new Date(run.startedAt).getTime(),
      tokenUsage: { input: 250, output: 380 },
      httpStatus: 200,
      providerRequestId: createId('providerreq', run.provider, run.date),
      createdAt: run.finishedAt
    });

    run.citations.forEach((uri, index) => {
      citations.push({
        id: createId('cite', responseId, String(index + 1)),
        providerResponseId: responseId,
        sourceType: 'url',
        sourceUri: uri,
        spanStart: index * 24,
        spanEnd: index * 24 + 18,
        confidence: 0.82
      });
    });

    scoreSnapshots.push({
      id: snapshotId,
      providerRunId: runId,
      scoringVersion: 'v1',
      normalizedScores: { visibility: run.visibility / 100, quality: run.quality / 100 },
      compositeScore: Number(((run.visibility + run.quality) / 2).toFixed(2)),
      dimensionScores: { visibility: run.visibility, quality: run.quality },
      computedAt: run.finishedAt
    });
  });

  return { providerRuns, providerResponses, citations, scoreSnapshots };
}

function getStore() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) return JSON.parse(raw);
  const seeded = seedStore();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(seeded));
  return seeded;
}

function getFilterOptions(store) {
  const list = (field) => [...new Set(store.providerRuns.map((run) => run[field]))].sort();
  return {
    providers: list('provider'),
    promptSets: list('promptSet'),
    domains: list('inputDomain'),
    competitorSets: list('competitorSet')
  };
}

function projectRunForDashboard(run, store) {
  const response = store.providerResponses.find((item) => item.providerRunId === run.id);
  const snapshot = store.scoreSnapshots.find((item) => item.providerRunId === run.id);
  const runCitations = store.citations
    .filter((item) => item.providerResponseId === response?.id)
    .map((item) => item.sourceUri);

  return {
    id: run.id,
    date: run.finishedAt.slice(0, 10),
    provider: run.provider,
    promptSet: run.promptSet,
    domain: run.inputDomain,
    competitorSet: run.competitorSet,
    prompt: run.prompt,
    visibility: snapshot?.dimensionScores.visibility ?? 0,
    quality: snapshot?.dimensionScores.quality ?? 0,
    citations: runCitations,
    rawOutput: response?.rawResponse ?? ''
  };
}

function queryRunsForDateWindow(store, days, filters) {
  const end = new Date('2026-03-02T00:00:00Z');
  const start = new Date(end);
  start.setDate(end.getDate() - days);

  return store.providerRuns
    .filter((run) => {
      const finishedAt = new Date(run.finishedAt);
      return finishedAt >= start
        && finishedAt <= end
        && (filters.provider === 'all' || run.provider === filters.provider)
        && (filters.promptSet === 'all' || run.promptSet === filters.promptSet)
        && (filters.domain === 'all' || run.inputDomain === filters.domain)
        && (filters.competitorSet === 'all' || run.competitorSet === filters.competitorSet);
    })
    .map((run) => projectRunForDashboard(run, store));
}

function queryResponseInspector(store, runId) {
  const run = store.providerRuns.find((item) => item.id === runId) ?? store.providerRuns[0];
  const response = store.providerResponses.find((item) => item.providerRunId === run.id);
  const extractedCitations = store.citations.filter((item) => item.providerResponseId === response?.id);
  const scoreSnapshot = store.scoreSnapshots.find((item) => item.providerRunId === run.id);
  return { run, response, extractedCitations, scoreSnapshot };
}

const store = getStore();
const ids = ['providerFilter', 'promptSetFilter', 'domainFilter', 'competitorFilter', 'runSelector'];
const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.tab-panel');

for (const tab of tabs) {
  tab.addEventListener('click', () => {
    tabs.forEach((t) => t.classList.remove('active'));
    panels.forEach((p) => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
  });
}

function fillFilters() {
  const options = getFilterOptions(store);
  const mapping = {
    providerFilter: options.providers,
    promptSetFilter: options.promptSets,
    domainFilter: options.domains,
    competitorFilter: options.competitorSets
  };

  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (id === 'runSelector') return;
    (mapping[id] || []).forEach((value) => {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = value;
      el.appendChild(opt);
    });
  });

  store.providerRuns.forEach((run) => {
    const opt = document.createElement('option');
    opt.value = run.id;
    opt.textContent = `${run.id} · ${run.provider} · ${run.prompt}`;
    runSelector.appendChild(opt);
  });
}

function filteredRuns() {
  return queryRunsForDateWindow(store, Number(dateRange.value), {
    provider: providerFilter.value,
    promptSet: promptSetFilter.value,
    domain: domainFilter.value,
    competitorSet: competitorFilter.value
  });
}

function avg(nums) { return nums.length ? (nums.reduce((a, b) => a + b, 0) / nums.length) : 0; }

function renderScorecards(data) {
  const visibility = avg(data.map((d) => d.visibility));
  const quality = avg(data.map((d) => d.quality));
  const mentionRate = data.length ? (data.filter((d) => d.visibility >= 60).length / data.length) * 100 : 0;
  const citationShare = data.length ? (data.filter((d) => d.citations.some((c) => c.includes('acme.com'))).length / data.length) * 100 : 0;

  scorecards.innerHTML = [
    ['Visibility Score', visibility.toFixed(1)],
    ['Performance Score', quality.toFixed(1)],
    ['Mention Rate', `${mentionRate.toFixed(0)}%`],
    ['Citation Share', `${citationShare.toFixed(0)}%`]
  ].map(([label, value]) => `<div class="metric"><div class="label">${label}</div><div class="value">${value}</div></div>`).join('');
}

function drawTrend(data) {
  const canvas = trendChart; const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));
  if (!sorted.length) return;
  const pad = 28, w = canvas.width - pad * 2, h = canvas.height - pad * 2;
  ctx.strokeStyle = '#cbd5e1'; ctx.strokeRect(pad, pad, w, h);
  ctx.beginPath(); ctx.strokeStyle = '#2563eb'; ctx.lineWidth = 2;
  sorted.forEach((r, i) => {
    const x = pad + (i / (sorted.length - 1 || 1)) * w;
    const y = pad + h - (r.visibility / 100) * h;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    ctx.fillStyle = '#111827'; ctx.fillText(r.date.slice(5), x - 14, canvas.height - 7);
  });
  ctx.stroke();
}

function drawDonut(data) {
  const canvas = donutChart; const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const own = data.reduce((n, r) => n + r.citations.filter((c) => c.includes('acme.com')).length, 0);
  const comp = data.reduce((n, r) => n + r.citations.filter((c) => !c.includes('acme.com')).length, 0);
  const total = Math.max(own + comp, 1);
  const cx = 140, cy = 130, r = 90;
  let a0 = -Math.PI / 2;
  [[own, '#2563eb', 'Tracked'], [comp, '#f59e0b', 'Competitor']].forEach(([v, color, label], i) => {
    const a1 = a0 + (v / total) * Math.PI * 2;
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, r, a0, a1); ctx.closePath();
    ctx.fillStyle = color; ctx.fill(); a0 = a1;
    ctx.fillStyle = '#111'; ctx.fillText(`${label}: ${v}`, 8, 20 + i * 18);
  });
  ctx.beginPath(); ctx.fillStyle = 'white'; ctx.arc(cx, cy, 45, 0, Math.PI * 2); ctx.fill();
}

function drawBar(data) {
  const canvas = barChart; const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const by = {};
  data.forEach((r) => { by[r.provider] = (by[r.provider] || 0) + r.citations.length; });
  const entries = Object.entries(by);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  entries.forEach(([k, v], i) => {
    const y = 20 + i * 56;
    const width = (v / max) * 250;
    ctx.fillStyle = '#3b82f6'; ctx.fillRect(90, y, width, 24);
    ctx.fillStyle = '#111'; ctx.fillText(k, 10, y + 16); ctx.fillText(String(v), 350, y + 16);
  });
}

function renderPromptTable(data) {
  promptTableBody.innerHTML = data.map((r) => `<tr><td>${r.prompt}</td><td>${r.provider}</td><td>${r.visibility}</td><td>${r.quality}</td><td>${r.citations.length}</td></tr>`).join('');
}

function renderHeatmap(data) {
  const prompts = [...new Set(data.map((d) => d.prompt))];
  const providers = [...new Set(data.map((d) => d.provider))];
  heatmap.style.gridTemplateColumns = `180px repeat(${providers.length}, 1fr)`;
  let html = '<div></div>' + providers.map((p) => `<div><strong>${p}</strong></div>`).join('');
  prompts.forEach((prompt) => {
    html += `<div><strong>${prompt}</strong></div>`;
    providers.forEach((provider) => {
      const run = data.find((r) => r.prompt === prompt && r.provider === provider);
      const score = run ? run.visibility : 0;
      const alpha = Math.max(0.1, score / 100);
      html += `<div style="background: rgba(37,99,235,${alpha})">${score || '-'}</div>`;
    });
  });
  heatmap.innerHTML = html;
}

function renderProviderComparison(data) {
  const by = {};
  data.forEach((r) => {
    by[r.provider] ??= [];
    by[r.provider].push(r);
  });
  providerTableBody.innerHTML = Object.entries(by).map(([provider, rows]) => {
    const v = avg(rows.map((r) => r.visibility));
    const q = avg(rows.map((r) => r.quality));
    const share = rows.length ? (rows.filter((r) => r.citations.some((c) => c.includes('acme.com'))).length / rows.length) * 100 : 0;
    const c = avg(rows.map((r) => r.citations.length));
    return `<tr><td>${provider}</td><td>${v.toFixed(1)}</td><td>${q.toFixed(1)}</td><td>${share.toFixed(0)}%</td><td>${c.toFixed(1)}</td></tr>`;
  }).join('');
}

function renderInsights(data) {
  const low = data.filter((r) => r.visibility < 60 || r.quality < 60).slice(0, 3);
  insights.innerHTML = low.map((r) => `
    <article class="insight">
      <strong>${r.prompt}</strong>
      <p>${r.provider} scored ${r.visibility} visibility and ${r.quality} quality. Recommendation: refresh the linked page for ${r.promptSet} with stronger evidence and comparison schema.</p>
      <small>Linked page: /content/${r.prompt.toLowerCase().replace(/\s+/g, '-')}</small>
    </article>
  `).join('') || '<p>No low-scoring prompts in current filter window.</p>';
}

function renderInspector() {
  const { response, extractedCitations } = queryResponseInspector(store, runSelector.value);
  rawOutput.textContent = response?.rawResponse ?? 'No provider response found for selected run.';
  citationList.innerHTML = extractedCitations.map((item) => `<li>${item.sourceUri}</li>`).join('');
}

function exportData(type) {
  const data = filteredRuns();
  if (type === 'json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    downloadBlob(blob, 'run-level-data.json');
  } else {
    const headers = ['id', 'date', 'provider', 'promptSet', 'domain', 'competitorSet', 'prompt', 'visibility', 'quality', 'citations'];
    const rows = data.map((r) => headers.map((h) => (h === 'citations' ? r.citations.join('|') : r[h])));
    const csv = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    downloadBlob(blob, 'run-level-data.csv');
  }
}

function downloadBlob(blob, filename) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function render() {
  const data = filteredRuns();
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

fillFilters();
runSelector.value = store.providerRuns[0].id;
[dateRange, providerFilter, promptSetFilter, domainFilter, competitorFilter, runSelector].forEach((el) => el.addEventListener('change', render));
exportCsv.addEventListener('click', () => exportData('csv'));
exportJson.addEventListener('click', () => exportData('json'));
render();
