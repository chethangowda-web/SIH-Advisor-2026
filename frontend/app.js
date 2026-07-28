'use strict';

// ── Config ───────────────────────────────────────────────────────────
const API = 'https://sih-ai-advisor.onrender.com';

const DOMAINS = [
  { name:'Agriculture',       count: 5 },
  { name:'Healthcare',        count: 8 },
  { name:'Education',         count: 4 },
  { name:'Governance',        count: 5 },
  { name:'Clean Technology',  count: 4 },
  { name:'Smart Cities',      count: 2 },
  { name:'Disaster Management',count: 3 },
  { name:'Transportation',    count: 3 },
  { name:'Finance',           count: 1 },
  { name:'Cybersecurity',     count: 2 },
  { name:'Environment',       count: 2 },
  { name:'Smart Automation',  count: 1 },
];

const state = {
  chatHistory:  [],
  blueprintData: null,
  trendsLoaded: false,
};

// ── Utils ─────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

function showToast(msg, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span style="font-weight:600;font-size:11px;font-family:var(--font-mono)">[${type.toUpperCase()}]</span> <span>${msg}</span>`;
  $('toastContainer').appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function scoreClass(n) { return n >= 8 ? 'high' : n >= 6 ? 'mid' : 'low'; }

async function apiFetch(path, opts = {}) {
  const url = (API + path).replace(/([^:]\/)\/+/g, "$1");
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...opts
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API request failed');
  }
  return res.json();
}

function animateCounter(el, target, suffix = '') {
  let current = 0;
  const step = target / 50;
  const interval = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = Math.round(current) + suffix;
    if (current >= target) clearInterval(interval);
  }, 30);
}

// ── Navigation ─────────────────────────────────────────────────────────
function navigate(section) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const sectionEl = $(`section-${section}`);
  const navEl = $(`nav-${section}`);
  if (sectionEl) sectionEl.classList.add('active');
  if (navEl) navEl.classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Lazy-load sections
  if (section === 'trends' && !state.trendsLoaded) loadTrends(false);
}

// ── Backend Status ───────────────────────────────────────────────────
async function checkStatus() {
  const dot  = $('statusDot');
  const text = $('statusText');
  try {
    const data = await apiFetch('/');
    dot.className  = 'status-dot online';
    text.textContent = 'Backend Online';
  } catch {
    dot.className  = 'status-dot offline';
    text.textContent = 'Backend Offline';
  }
}

// ── Dashboard ─────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const data = await apiFetch('/api/stats');
    animateCounter($('cnt-projects'), data.total_projects || 35, '+');
    animateCounter($('cnt-domains'),  data.domains_count  || 12);
    animateCounter($('cnt-years'),    7);
    animateCounter($('cnt-techs'),    data.top_technologies?.length * 4 || 40, '+');
  } catch {
    animateCounter($('cnt-projects'), 35, '+');
    animateCounter($('cnt-domains'),  12);
    animateCounter($('cnt-years'),    7);
    animateCounter($('cnt-techs'),    40, '+');
  }
}

function renderDomains() {
  const grid = $('domainsGrid');
  grid.innerHTML = DOMAINS.map(d => `
    <div class="domain-card" onclick="quickGenerate('${d.name}')">
      <div class="domain-name">${d.name}</div>
      <div class="domain-count">${d.count} Historical Entries</div>
    </div>
  `).join('');
}

function quickGenerate(domain) {
  navigate('ideas');
  $('domainSelect').value = domain;
  showToast(`Domain set to "${domain}". Click Generate Ideas!`, 'info');
}

// ── Trends ────────────────────────────────────────────────────────────
async function loadTrends(force = false) {
  if (state.trendsLoaded && !force) return;

  $('trendsLoader').classList.remove('hidden');
  $('trendsContent').classList.add('hidden');

  try {
    const { data } = await apiFetch('/api/trends');
    renderTrendCharts(data);
    renderTrendDetails(data);
    state.trendsLoaded = true;
    $('trendsLoader').classList.add('hidden');
    $('trendsContent').classList.remove('hidden');
  } catch (err) {
    $('trendsLoader').innerHTML = `
      <div style="font-size:40px">⚠️</div>
      <p style="color:#f43f5e">Backend not connected. Start the backend first!</p>
      <p style="font-size:12px;color:#55556a">Run: cd backend → setup.bat</p>`;
    showToast('Backend offline. Start the server first.', 'error');
  }
}

function renderTrendCharts(data) {
  // Domain Chart
  const domainCtx = $('domainChart')?.getContext('2d');
  if (domainCtx && data.top_domains) {
    new Chart(domainCtx, {
      type: 'bar',
      data: {
        labels: data.top_domains.map(d => d.domain),
        datasets: [{
          label: 'Winning Projects',
          data: data.top_domains.map(d => d.win_count),
          backgroundColor: [
            'rgba(99,102,241,0.7)','rgba(139,92,246,0.7)','rgba(45,212,191,0.7)',
            'rgba(251,191,36,0.7)','rgba(244,63,94,0.7)','rgba(34,197,94,0.7)',
            'rgba(6,182,212,0.7)','rgba(248,113,113,0.7)',
          ],
          borderRadius: 8, borderWidth: 0,
        }],
      },
      options: {
        responsive: true, plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#9090b8' } },
          y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#9090b8', stepSize: 1 } },
        },
      }
    });
  }

  // Year Chart - use static data for now
  const yearCtx = $('yearChart')?.getContext('2d');
  if (yearCtx) {
    new Chart(yearCtx, {
      type: 'line',
      data: {
        labels: ['2017','2018','2019','2020','2021','2022','2023','2024'],
        datasets: [{
          label: 'Projects',
          data: [2,3,3,3,4,5,7,8],
          borderColor: 'rgba(99,102,241,1)',
          backgroundColor: 'rgba(99,102,241,0.1)',
          fill: true, tension: 0.4, pointBackgroundColor: '#6366f1',
          pointRadius: 5, pointHoverRadius: 8,
        }],
      },
      options: {
        responsive: true, plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#9090b8' } },
          y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#9090b8', stepSize: 1 } },
        },
      }
    });
  }

  // HW/SW Chart
  const hwswCtx = $('hwswChart')?.getContext('2d');
  if (hwswCtx) {
    new Chart(hwswCtx, {
      type: 'doughnut',
      data: {
        labels: ['Software', 'Hardware'],
        datasets: [{
          data: [70, 30],
          backgroundColor: ['rgba(99,102,241,0.8)', 'rgba(251,191,36,0.8)'],
          borderWidth: 0, hoverOffset: 8,
        }],
      },
      options: {
        responsive: true, cutout: '70%',
        plugins: { legend: { labels: { color: '#9090b8', padding: 16 } } },
      }
    });
  }
}

function renderTrendDetails(data) {
  // Tech badges
  const techContainer = $('techBadges');
  if (techContainer && data.rising_technologies) {
    techContainer.innerHTML = data.rising_technologies
      .map(t => `<span class="tech-badge">${t}</span>`)
      .join('');
  }

  // Hot domains
  const hotContainer = $('hotDomains');
  if (hotContainer && data.predicted_hot_domains_2025) {
    hotContainer.innerHTML = data.predicted_hot_domains_2025
      .map((d, i) => `
        <div class="hot-domain-item">
          <span class="hot-domain-rank">0${i+1}</span>
          <span class="hot-domain-name">${d}</span>
          <span class="tech-chip" style="margin-left:auto;font-size:10px">HIGH TRAJECTORY</span>
        </div>`)
      .join('');
  }

  // Key insights
  const insightsContainer = $('keyInsights');
  if (insightsContainer && data.key_insights) {
    insightsContainer.innerHTML = data.key_insights
      .map(i => `
        <div class="insight-item">
          <i class="fa-solid fa-arrow-right insight-icon"></i>
          <span>${i}</span>
        </div>`)
      .join('');
  }
}

// ── Idea Generator ────────────────────────────────────────────────────
async function generateIdeas() {
  const domain = $('domainSelect').value;
  if (!domain) { showToast('Please select a domain first!', 'warn'); return; }

  const btn = $('generateIdeasBtn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px"></div> Generating...';

  $('ideasLoader').classList.remove('hidden');
  $('ideasGrid').innerHTML = '';

  try {
    const res = await apiFetch('/api/generate-ideas', {
      method: 'POST',
      body: JSON.stringify({
        domain,
        theme: $('themeInput').value || '',
        num_ideas: parseInt($('numIdeas').value || '3'),
      })
    });

    $('ideasLoader').classList.add('hidden');
    $('ideasGrid').innerHTML = res.ideas.map((idea, i) => renderIdeaCard(idea, i)).join('');
    showToast(`Generated ${res.ideas.length} novel ideas! 🚀`, 'success');
  } catch (err) {
    $('ideasLoader').innerHTML = `
      <div style="font-size:40px">⚠️</div>
      <p style="color:#f43f5e">${err.message}</p>`;
    showToast(err.message, 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate Ideas';
}

function renderIdeaCard(idea, index) {
  const techs = (idea.technologies || []).slice(0, 5)
    .map(t => `<span class="tech-chip">${t}</span>`).join('');

  return `
    <div class="idea-card" style="animation-delay:${index * 0.1}s">
      <div class="idea-header">
        <span class="idea-domain-badge">${idea.domain || ''}</span>
        <div class="idea-title">${idea.title || 'Untitled Idea'}</div>
        <div class="idea-tagline">${idea.tagline || ''}</div>
      </div>

      <div class="scores-row">
        <div class="score-pill">
          <div class="score-label">Novelty</div>
          <div class="score-value ${scoreClass(idea.novelty_score)}">${idea.novelty_score || '?'}<span style="font-size:14px">/10</span></div>
        </div>
        <div class="score-pill">
          <div class="score-label">Feasibility</div>
          <div class="score-value ${scoreClass(idea.feasibility_score)}">${idea.feasibility_score || '?'}<span style="font-size:14px">/10</span></div>
        </div>
        <div class="score-pill">
          <div class="score-label">Impact</div>
          <div class="score-value ${scoreClass(idea.impact_score)}">${idea.impact_score || '?'}<span style="font-size:14px">/10</span></div>
        </div>
      </div>

      <div>
        <div class="idea-section-label">Problem</div>
        <div class="idea-text">${idea.problem_statement || ''}</div>
      </div>
      <div>
        <div class="idea-section-label">Solution</div>
        <div class="idea-text">${idea.solution || ''}</div>
      </div>
      <div>
        <div class="idea-section-label">Why Novel</div>
        <div class="idea-text" style="color:#a5b4fc">${idea.novelty_reason || ''}</div>
      </div>
      <div>
        <div class="idea-section-label">Beneficiaries</div>
        <div class="idea-text">${idea.target_beneficiaries || ''}</div>
      </div>
      <div>
        <div class="idea-section-label">Tech Stack</div>
        <div class="tech-chips">${techs}</div>
      </div>
      <div class="idea-actions">
        <button class="btn-primary" onclick="useIdeaForBlueprint(${JSON.stringify(idea).replace(/"/g,'&quot;')})">
          <i class="fa-solid fa-file-code"></i> Generate Blueprint
        </button>
        <button class="btn-secondary" onclick="useIdeaForChat(${JSON.stringify(idea).replace(/"/g,'&quot;')})">
          <i class="fa-solid fa-robot"></i> Discuss with AI
        </button>
      </div>
    </div>`;
}

function useIdeaForBlueprint(idea) {
  navigate('blueprint');
  $('bp-title').value    = idea.title || '';
  $('bp-problem').value  = idea.problem_statement || '';
  $('bp-solution').value = idea.solution || '';
  $('bp-domain').value   = idea.domain || '';
  $('bp-tech').value     = (idea.technologies || []).join(', ');
  showToast('Idea loaded! Click "Generate Full Blueprint"', 'success');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function useIdeaForChat(idea) {
  navigate('chat');
  $('chatInput').value = `Give me more details and improvements for this idea: "${idea.title}". Problem: ${idea.problem_statement}`;
  showToast('Idea loaded in chat!', 'info');
}

// ── Blueprint Generator ───────────────────────────────────────────────
async function generateBlueprint() {
  const title    = $('bp-title').value.trim();
  const problem  = $('bp-problem').value.trim();
  const solution = $('bp-solution').value.trim();
  const domain   = $('bp-domain').value;
  const techRaw  = $('bp-tech').value;
  const team     = parseInt($('bp-team').value || '6');
  const duration = parseInt($('bp-duration').value || '4');

  if (!title || !problem || !solution || !domain) {
    showToast('Fill in all required fields (*)!', 'warn');
    return;
  }

  const techs = techRaw ? techRaw.split(',').map(t => t.trim()).filter(Boolean) : ['Python', 'React', 'FastAPI'];
  const btn = $('generateBlueprintBtn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px"></div> Building Blueprint...';
  $('blueprintLoader').classList.remove('hidden');
  $('blueprintOutput').classList.add('hidden');

  try {
    const res = await apiFetch('/api/blueprint', {
      method: 'POST',
      body: JSON.stringify({ title, problem_statement: problem, solution, domain, technologies: techs, team_size: team, duration_weeks: duration })
    });

    state.blueprintData = res.blueprint;
    renderBlueprint(res.blueprint);
    $('blueprintLoader').classList.add('hidden');
    $('blueprintOutput').classList.remove('hidden');
    showToast('Blueprint generated! 📋', 'success');
    $('blueprintOutput').scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    $('blueprintLoader').innerHTML = `<div style="font-size:40px">⚠️</div><p style="color:#f43f5e">${err.message}</p>`;
    showToast(err.message, 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '<i class="fa-solid fa-file-code"></i> Generate Full Blueprint';
}

function renderBlueprint(bp) {
  const output = $('blueprintOutput');
  if (!bp || bp.error) {
    output.innerHTML = `<div class="glass-card"><p style="color:#f43f5e">⚠️ ${bp?.error || 'Blueprint generation failed'}</p></div>`;
    return;
  }

  const ov = bp.project_overview || {};
  const pr = bp.problem_analysis || {};
  const so = bp.proposed_solution || {};
  const ta = bp.technical_architecture || {};
  const ip = bp.implementation_plan || {};
  const ts = bp.team_structure || {};
  const ia = bp.impact_assessment || {};
  const bu = bp.budget_estimate || {};
  const ra = bp.risk_analysis || {};
  const dp = bp.demo_plan || {};
  const cn = bp.conclusion || {};

  output.innerHTML = `
    <!-- Toolbar -->
    <div class="blueprint-toolbar">
      <button class="btn-primary" onclick="downloadBlueprint()"><i class="fa-solid fa-download"></i> Download JSON</button>
      <button class="btn-secondary" onclick="window.print()"><i class="fa-solid fa-print"></i> Print</button>
    </div>

    <div class="blueprint-sections">

      <!-- Overview -->
      <div class="bp-section">
        <div class="bp-section-header"><i class="fa-solid fa-flag"></i> Project Overview</div>
        <div class="bp-section-body">
          <div style="margin-bottom:16px">
            <div style="font-size:22px;font-weight:800;margin-bottom:6px">${ov.title || ''}</div>
            <div style="color:#a5b4fc;font-style:italic;margin-bottom:12px">"${ov.tagline || ''}"</div>
            <p style="font-size:14px;color:#9090b8;line-height:1.7">${ov.executive_summary || ''}</p>
          </div>
          <div class="bp-overview-grid">
            <div class="bp-field"><div class="bp-field-label">Domain</div><div class="bp-field-value">${ov.domain || ''}</div></div>
            <div class="bp-field"><div class="bp-field-label">Type</div><div class="bp-field-value">${ov.problem_type || ''}</div></div>
          </div>
        </div>
      </div>

      <!-- Problem Analysis -->
      <div class="bp-section">
        <div class="bp-section-header"><i class="fa-solid fa-magnifying-glass"></i> Problem Analysis</div>
        <div class="bp-section-body">
          <div class="bp-field" style="margin-bottom:16px">
            <div class="bp-field-label">Current Situation</div>
            <div class="bp-field-value" style="line-height:1.7;color:#9090b8">${pr.current_situation || ''}</div>
          </div>
          <div class="bp-field" style="margin-bottom:16px">
            <div class="bp-field-label">Why Urgent Now</div>
            <div class="bp-field-value" style="line-height:1.7;color:#9090b8">${pr.why_urgent_now || ''}</div>
          </div>
          ${pr.root_causes ? `
          <div class="bp-field">
            <div class="bp-field-label">Root Causes</div>
            <ul style="list-style:none;margin-top:8px">
              ${pr.root_causes.map(c => `<li style="padding:4px 0;color:#9090b8;font-size:14px;display:flex;gap:8px"><span style="color:#6366f1">→</span>${c}</li>`).join('')}
            </ul>
          </div>` : ''}
        </div>
      </div>

      <!-- Solution -->
      <div class="bp-section">
        <div class="bp-section-header"><i class="fa-solid fa-lightbulb"></i> Proposed Solution</div>
        <div class="bp-section-body">
          <p style="font-size:14px;color:#9090b8;line-height:1.7;margin-bottom:20px">${so.solution_overview || ''}</p>
          ${so.key_features ? `
          <div class="bp-field-label" style="margin-bottom:12px">Key Features</div>
          ${so.key_features.map(f => `
            <div class="feature-card">
              <div class="feature-name">${f.feature || ''}</div>
              <div class="feature-desc">${f.description || ''}</div>
              ${f.impact ? `<div style="font-size:11px;color:var(--text-muted);margin-top:6px;font-family:var(--font-mono)">IMPACT: ${f.impact}</div>` : ''}
            </div>`).join('')}` : ''}
          <div class="bp-field" style="margin-top:16px">
            <div class="bp-field-label">Unique Value Proposition</div>
            <div class="bp-field-value" style="color:#a5b4fc;font-style:italic;line-height:1.6">"${so.unique_value_proposition || ''}"</div>
          </div>
        </div>
      </div>

      <!-- Tech Architecture -->
      <div class="bp-section">
        <div class="bp-section-header"><i class="fa-solid fa-sitemap"></i> Technical Architecture</div>
        <div class="bp-section-body">
          ${ta.tech_stack ? `
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px;margin-bottom:20px">
            ${Object.entries(ta.tech_stack).map(([cat, items]) => items?.length ? `
              <div class="tech-category">
                <div class="tech-category-label">${cat.replace(/_/g,' ')}</div>
                <div class="tech-chips">${items.map(t=>`<span class="tech-chip">${t}</span>`).join('')}</div>
              </div>` : '').join('')}
          </div>` : ''}
          ${ta.data_flow ? `
          <div class="bp-field">
            <div class="bp-field-label">Data Flow</div>
            <div class="bp-field-value" style="color:#9090b8;line-height:1.7;font-size:13px">${ta.data_flow}</div>
          </div>` : ''}
        </div>
      </div>

      <!-- Implementation Plan -->
      <div class="bp-section">
        <div class="bp-section-header"><i class="fa-solid fa-calendar-check"></i> Implementation Plan</div>
        <div class="bp-section-body">
          ${ip.phases ? ip.phases.map((p, i) => `
            <div class="timeline-phase">
              <div class="phase-marker">
                <div class="phase-dot"></div>
                ${i < ip.phases.length - 1 ? '<div class="phase-line"></div>' : ''}
              </div>
              <div class="phase-content">
                <div class="phase-week">${p.week || ''}</div>
                <div class="phase-name">${p.phase || ''}</div>
                <ul class="phase-tasks">${(p.tasks||[]).map(t=>`<li>${t}</li>`).join('')}</ul>
                ${p.deliverable ? `<div style="font-size:12px;color:#2dd4bf;margin-top:8px">📦 ${p.deliverable}</div>` : ''}
              </div>
            </div>`).join('') : ''}
        </div>
      </div>

      <!-- Impact -->
      <div class="bp-section">
        <div class="bp-section-header"><i class="fa-solid fa-earth-asia"></i> Impact Assessment</div>
        <div class="bp-section-body">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">
            <div class="bp-field"><div class="bp-field-label">Primary Beneficiaries</div><div class="bp-field-value">${ia.primary_beneficiaries||''}</div></div>
            <div class="bp-field"><div class="bp-field-label">Estimated Count</div><div class="bp-field-value" style="color:#2dd4bf;font-weight:700">${ia.beneficiary_count||''}</div></div>
          </div>
          ${ia.measurable_outcomes ? `
          <div class="bp-field-label" style="margin-bottom:10px">Measurable Outcomes</div>
          ${ia.measurable_outcomes.map(o=>`<div class="impact-item"><div class="impact-dot"></div><span style="font-size:13px;color:#9090b8">${o}</span></div>`).join('')}` : ''}
          ${ia.sdg_goals_addressed ? `
          <div style="margin-top:16px">
            <div class="bp-field-label" style="margin-bottom:10px">SDG Goals</div>
            ${ia.sdg_goals_addressed.map(s=>`<span class="sdg-badge">${s}</span>`).join('')}
          </div>` : ''}
        </div>
      </div>

      <!-- Budget -->
      <div class="bp-section">
        <div class="bp-section-header"><i class="fa-solid fa-indian-rupee-sign"></i> Budget Estimate</div>
        <div class="bp-section-body">
          ${bu.breakdown ? bu.breakdown.map(b => `
            <div class="budget-row">
              <div>
                <div style="font-size:14px">${b.item||''}</div>
                <div style="font-size:12px;color:#55556a">${b.justification||''}</div>
              </div>
              <div class="budget-cost">${b.cost||''}</div>
            </div>`).join('') : ''}
          ${bu.total_budget ? `<div class="budget-row"><span>Total Budget</span><span class="budget-cost" style="font-size:17px">${bu.total_budget}</span></div>` : ''}
        </div>
      </div>

      <!-- Risks -->
      <div class="bp-section">
        <div class="bp-section-header"><i class="fa-solid fa-triangle-exclamation"></i> Risk Analysis</div>
        <div class="bp-section-body">
          ${ra.risks ? ra.risks.map(r => `
            <div class="risk-card">
              <span class="risk-level ${r.probability}">${r.probability} Risk</span>
              <div style="font-size:14px;font-weight:600;margin-bottom:6px">${r.risk||''}</div>
              <div style="font-size:13px;color:#9090b8">🛡️ ${r.mitigation||''}</div>
            </div>`).join('') : ''}
        </div>
      </div>

      <!-- Demo Plan -->
      <div class="bp-section">
        <div class="bp-section-header"><i class="fa-solid fa-display"></i> Demo Plan</div>
        <div class="bp-section-body">
          ${dp.demo_flow ? `
          <div class="bp-field-label" style="margin-bottom:10px">Demo Flow</div>
          ${dp.demo_flow.map((step,i) => `
            <div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:14px">
              <span style="color:#6366f1;font-weight:700;min-width:20px">${i+1}.</span>
              <span style="color:#9090b8">${step}</span>
            </div>`).join('')}` : ''}
          ${dp.key_wow_moments ? `
          <div style="margin-top:16px">
            <div class="bp-field-label" style="margin-bottom:10px">WOW Moments for Judges</div>
            ${dp.key_wow_moments.map(m=>`<div class="impact-item"><span style="font-size:18px">⭐</span><span style="font-size:13px;color:#9090b8">${m}</span></div>`).join('')}
          </div>` : ''}
        </div>
      </div>

      <!-- Conclusion -->
      <div class="bp-section">
        <div class="bp-section-header"><i class="fa-solid fa-trophy"></i> Why This Will Win</div>
        <div class="bp-section-body">
          <div style="background:rgba(99,102,241,0.08);border-left:4px solid #6366f1;padding:20px;border-radius:8px;margin-bottom:16px">
            <p style="font-size:14px;color:#e8e8f0;line-height:1.7">${cn.why_this_will_win||''}</p>
          </div>
          <div class="bp-field">
            <div class="bp-field-label">Government Adoption Path</div>
            <div class="bp-field-value" style="color:#9090b8;line-height:1.7;font-size:13px">${cn.government_adoption_path||''}</div>
          </div>
        </div>
      </div>

    </div>`;
}

function downloadBlueprint() {
  if (!state.blueprintData) return;
  const blob = new Blob([JSON.stringify(state.blueprintData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url;
  a.download = `sih_blueprint_${Date.now()}.json`; a.click();
  URL.revokeObjectURL(url);
  showToast('Blueprint downloaded!', 'success');
}

// ── Chat ─────────────────────────────────────────────────────────────
async function sendChatMessage() {
  const input = $('chatInput');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  $('chatSuggestions').style.display = 'none';
  appendMessage('user', msg);
  showTyping();
  state.chatHistory.push({ role: 'human', content: msg });

  try {
    const res = await apiFetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message: msg, history: state.chatHistory.slice(-8) })
    });
    hideTyping();
    appendMessage('bot', res.response);
    state.chatHistory.push({ role: 'assistant', content: res.response });
  } catch (err) {
    hideTyping();
    appendMessage('bot', `⚠️ **Backend not connected!**\n\nPlease start the backend server first:\n1. Open a new terminal\n2. cd to \`backend\` folder\n3. Run \`setup.bat\``);
  }
}

function sendSuggestion(btn) {
  $('chatInput').value = btn.textContent;
  sendChatMessage();
}

function appendMessage(role, content) {
  const msgs = $('chatMessages');
  const div = document.createElement('div');
  div.className = `chat-bubble ${role}`;

  const icon = role === 'bot' ? '<i class="fa-solid fa-robot"></i>' : '<i class="fa-solid fa-user"></i>';
  const formatted = content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');

  div.innerHTML = `
    <div class="bubble-avatar">${icon}</div>
    <div class="bubble-content">${formatted}</div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function showTyping() {
  const msgs = $('chatMessages');
  const div = document.createElement('div');
  div.className = 'chat-bubble bot'; div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="bubble-avatar"><i class="fa-solid fa-robot"></i></div>
    <div class="bubble-content">
      <div class="typing-indicator">
        <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
      </div>
    </div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  $('chatSendBtn').disabled = true;
}

function hideTyping() {
  const el = $('typingIndicator');
  if (el) el.remove();
  $('chatSendBtn').disabled = false;
}

function initScratchCard() {
  const canvas = $('scratchCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  // Fill with silver scratch layer
  ctx.fillStyle = '#27272a';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  // Add scratch instructions text on canvas
  ctx.fillStyle = '#71717a';
  ctx.font = '700 12px "Consolas", monospace';
  ctx.textAlign = 'center';
  ctx.fillText('CLICK & DRAG TO SCRATCH AND REVEAL SECRET IDEA', canvas.width / 2, canvas.height / 2 + 4);

  let isScratching = false;

  function scratch(e) {
    if (!isScratching) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
    const y = (e.clientY || e.touches?.[0]?.clientY) - rect.top;

    ctx.globalCompositeOperation = 'destination-out';
    ctx.beginPath();
    ctx.arc(x, y, 24, 0, Math.PI * 2);
    ctx.fill();
  }

  canvas.addEventListener('mousedown', () => isScratching = true);
  canvas.addEventListener('mouseup', () => isScratching = false);
  canvas.addEventListener('mousemove', scratch);
  canvas.addEventListener('touchstart', () => isScratching = true);
  canvas.addEventListener('touchend', () => isScratching = false);
  canvas.addEventListener('touchmove', scratch);
}

function scrollToSection(id) {
  const el = $(id);
  if (el) el.scrollIntoView({ behavior: 'smooth' });
}

// ── Init ─────────────────────────────────────────────────────────────
async function init() {
  // Set Dashboard as default
  navigate('dashboard');
  initScratchCard();

  // Check backend
  await checkStatus();
  setInterval(checkStatus, 30000);

  // Load dashboard data
  await loadDashboard();
  renderDomains();

  // Enter key for chat
  const chatInput = $('chatInput');
  if (chatInput) chatInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendChatMessage(); });
}

window.addEventListener('DOMContentLoaded', init);
