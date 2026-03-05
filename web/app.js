const runs = [
  { id: 'r1', date: '2026-02-10', provider: 'ChatGPT', promptSet: 'Core Buyer Journey', domain: 'acme.com', competitorSet: 'Set A', prompt: 'Best CRM for SaaS startup', visibility: 82, quality: 76, citations: ['acme.com/blog/crm-guide','reviewhub.io/crm'], rawOutput: 'Acme CRM is frequently recommended for startup teams due to fast onboarding...' },
  { id: 'r2', date: '2026-02-13', provider: 'Perplexity', promptSet: 'Core Buyer Journey', domain: 'acme.com', competitorSet: 'Set A', prompt: 'Compare CRM automation tools', visibility: 68, quality: 63, citations: ['competitor.io/automation','acme.com/features/automation'], rawOutput: 'Automation capabilities vary. Competitor leads in integrations while Acme is simpler...' },
  { id: 'r3', date: '2026-02-18', provider: 'Gemini', promptSet: 'Brand Defense', domain: 'acme.com', competitorSet: 'Set B', prompt: 'Is Acme good for enterprise?', visibility: 55, quality: 61, citations: ['analyst.com/reports/crm-2026'], rawOutput: 'For enterprise, Acme can work when governance constraints are moderate...' },
  { id: 'r4', date: '2026-02-22', provider: 'Google AIO', promptSet: 'Brand Defense', domain: 'acme.com', competitorSet: 'Set B', prompt: 'Top alternatives to Acme CRM', visibility: 40, quality: 45, citations: ['competitor.io/pricing','reviewhub.io/top-crm'], rawOutput: 'Alternatives include Competitor and OrbitCRM due to stronger multi-region support...' },
  { id: 'r5', date: '2026-02-24', provider: 'ChatGPT', promptSet: 'Expansion', domain: 'acme.com', competitorSet: 'Set C', prompt: 'CRM for fintech compliance', visibility: 71, quality: 80, citations: ['acme.com/compliance', 'regsource.org/guidelines'], rawOutput: 'Fintech teams should prioritize audit logs and role controls. Acme cites SOC2...' },
  { id: 'r6', date: '2026-03-01', provider: 'Perplexity', promptSet: 'Expansion', domain: 'acme.com', competitorSet: 'Set C', prompt: 'Best CRM with API-first architecture', visibility: 62, quality: 59, citations: ['apiweekly.dev/crm-api','acme.com/api'], rawOutput: 'API-first options include Acme and RadiusCRM; Radius has broader webhooks...' }
];

const ids = ['providerFilter','promptSetFilter','domainFilter','competitorFilter','runSelector'];
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

function unique(field) {
  return [...new Set(runs.map(r => r[field]))];
}

function fillFilters() {
  for (const id of ids) {
    const el = document.getElementById(id);
    if (id === 'runSelector') continue;
    const field = id.replace('Filter', '');
    unique(field).forEach(v => {
      const opt = document.createElement('option');
      opt.value = v;
      opt.textContent = v;
      el.appendChild(opt);
    });
  }
  runs.forEach(run => {
    const opt = document.createElement('option');
    opt.value = run.id;
    opt.textContent = `${run.id} · ${run.provider} · ${run.prompt}`;
    runSelector.appendChild(opt);
  });
}

function filteredRuns() {
  const days = Number(dateRange.value);
  const end = new Date('2026-03-02');
  const start = new Date(end);
  start.setDate(end.getDate() - days);
  return runs.filter(r => {
    const d = new Date(r.date);
    return d >= start && d <= end
      && (providerFilter.value === 'all' || r.provider === providerFilter.value)
      && (promptSetFilter.value === 'all' || r.promptSet === promptSetFilter.value)
      && (domainFilter.value === 'all' || r.domain === domainFilter.value)
      && (competitorFilter.value === 'all' || r.competitorSet === competitorFilter.value);
  });
}

function avg(nums) { return nums.length ? (nums.reduce((a,b)=>a+b,0)/nums.length) : 0; }

function renderScorecards(data) {
  const visibility = avg(data.map(d => d.visibility));
  const quality = avg(data.map(d => d.quality));
  const mentionRate = data.length ? (data.filter(d => d.visibility >= 60).length / data.length) * 100 : 0;
  const citationShare = data.length ? (data.filter(d => d.citations.some(c=>c.includes('acme.com'))).length / data.length) * 100 : 0;

  scorecards.innerHTML = [
    ['Visibility Score', visibility.toFixed(1)],
    ['Performance Score', quality.toFixed(1)],
    ['Mention Rate', `${mentionRate.toFixed(0)}%`],
    ['Citation Share', `${citationShare.toFixed(0)}%`],
  ].map(([label,value]) => `<div class="metric"><div class="label">${label}</div><div class="value">${value}</div></div>`).join('');
}

function drawTrend(data) {
  const canvas = trendChart; const ctx = canvas.getContext('2d');
  ctx.clearRect(0,0,canvas.width,canvas.height);
  const sorted = [...data].sort((a,b)=>a.date.localeCompare(b.date));
  if (!sorted.length) return;
  const pad = 28, w = canvas.width - pad*2, h = canvas.height - pad*2;
  ctx.strokeStyle = '#cbd5e1'; ctx.strokeRect(pad,pad,w,h);
  ctx.beginPath(); ctx.strokeStyle = '#2563eb'; ctx.lineWidth = 2;
  sorted.forEach((r,i)=>{
    const x = pad + (i/(sorted.length-1 || 1))*w;
    const y = pad + h - (r.visibility/100)*h;
    if (i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    ctx.fillStyle = '#111827'; ctx.fillText(r.date.slice(5), x-14, canvas.height-7);
  });
  ctx.stroke();
}

function drawDonut(data) {
  const canvas = donutChart; const ctx = canvas.getContext('2d');
  ctx.clearRect(0,0,canvas.width,canvas.height);
  const own = data.reduce((n,r)=>n + r.citations.filter(c=>c.includes('acme.com')).length,0);
  const comp = data.reduce((n,r)=>n + r.citations.filter(c=>!c.includes('acme.com')).length,0);
  const total = Math.max(own + comp, 1);
  const cx=140, cy=130, r=90;
  let a0 = -Math.PI/2;
  [[own,'#2563eb','Tracked'], [comp,'#f59e0b','Competitor']].forEach(([v,color,label], i) => {
    const a1 = a0 + (v/total)*Math.PI*2;
    ctx.beginPath(); ctx.moveTo(cx,cy); ctx.arc(cx,cy,r,a0,a1); ctx.closePath();
    ctx.fillStyle = color; ctx.fill(); a0=a1;
    ctx.fillStyle='#111'; ctx.fillText(`${label}: ${v}`, 8, 20 + i*18);
  });
  ctx.beginPath(); ctx.fillStyle='white'; ctx.arc(cx,cy,45,0,Math.PI*2); ctx.fill();
}

function drawBar(data) {
  const canvas = barChart; const ctx = canvas.getContext('2d');
  ctx.clearRect(0,0,canvas.width,canvas.height);
  const by = {};
  data.forEach(r => by[r.provider] = (by[r.provider] || 0) + r.citations.length);
  const entries = Object.entries(by);
  const max = Math.max(1, ...entries.map(([,v])=>v));
  entries.forEach(([k,v],i)=>{
    const y = 20 + i*56;
    const width = (v / max) * 250;
    ctx.fillStyle = '#3b82f6'; ctx.fillRect(90,y,width,24);
    ctx.fillStyle = '#111'; ctx.fillText(k, 10, y+16); ctx.fillText(String(v), 350, y+16);
  });
}

function renderPromptTable(data) {
  promptTableBody.innerHTML = data.map(r => `<tr><td>${r.prompt}</td><td>${r.provider}</td><td>${r.visibility}</td><td>${r.quality}</td><td>${r.citations.length}</td></tr>`).join('');
}

function renderHeatmap(data) {
  const prompts = [...new Set(data.map(d => d.prompt))];
  const providers = [...new Set(data.map(d => d.provider))];
  heatmap.style.gridTemplateColumns = `180px repeat(${providers.length}, 1fr)`;
  let html = '<div></div>' + providers.map(p => `<div><strong>${p}</strong></div>`).join('');
  prompts.forEach(prompt => {
    html += `<div><strong>${prompt}</strong></div>`;
    providers.forEach(provider => {
      const run = data.find(r => r.prompt === prompt && r.provider === provider);
      const score = run ? run.visibility : 0;
      const alpha = Math.max(0.1, score/100);
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
    const v = avg(rows.map(r=>r.visibility));
    const q = avg(rows.map(r=>r.quality));
    const share = rows.length ? (rows.filter(r => r.citations.some(c=>c.includes('acme.com'))).length / rows.length) * 100 : 0;
    const c = avg(rows.map(r => r.citations.length));
    return `<tr><td>${provider}</td><td>${v.toFixed(1)}</td><td>${q.toFixed(1)}</td><td>${share.toFixed(0)}%</td><td>${c.toFixed(1)}</td></tr>`;
  }).join('');
}

function renderInsights(data) {
  const low = data.filter(r => r.visibility < 60 || r.quality < 60).slice(0,3);
  insights.innerHTML = low.map(r => `
    <article class="insight">
      <strong>${r.prompt}</strong>
      <p>${r.provider} scored ${r.visibility} visibility and ${r.quality} quality. Recommendation: refresh the linked page for ${r.promptSet} with stronger evidence and comparison schema.</p>
      <small>Linked page: /content/${r.prompt.toLowerCase().replace(/\s+/g,'-')}</small>
    </article>
  `).join('') || '<p>No low-scoring prompts in current filter window.</p>';
}

function renderInspector() {
  const run = runs.find(r => r.id === runSelector.value) || runs[0];
  rawOutput.textContent = run.rawOutput;
  citationList.innerHTML = run.citations.map(c => `<li>${c}</li>`).join('');
}

function exportData(type) {
  const data = filteredRuns();
  if (type === 'json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    downloadBlob(blob, 'run-level-data.json');
  } else {
    const headers = ['id','date','provider','promptSet','domain','competitorSet','prompt','visibility','quality','citations'];
    const rows = data.map(r => headers.map(h => (h === 'citations' ? r.citations.join('|') : r[h])));
    const csv = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
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
runSelector.value = runs[0].id;
[dateRange, providerFilter, promptSetFilter, domainFilter, competitorFilter, runSelector].forEach(el => el.addEventListener('change', render));
exportCsv.addEventListener('click', () => exportData('csv'));
exportJson.addEventListener('click', () => exportData('json'));
render();
