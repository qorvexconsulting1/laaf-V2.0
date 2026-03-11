// LAAF Dashboard — Vanilla JS SPA (no build step required)

const API = '';

// ── Section navigation ────────────────────────────────────────────────────────
function showSection(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
  document.getElementById(id).classList.remove('hidden');
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => {
    if (b.textContent.trim().toLowerCase().includes(id.split('-')[0])) {
      b.classList.add('active');
    }
  });
  if (id === 'scans') loadScans();
  if (id === 'techniques') loadTechniques();
}

// ── Scans ─────────────────────────────────────────────────────────────────────
async function loadScans() {
  const container = document.getElementById('scans-table-container');
  container.innerHTML = '<p class="loading">Loading…</p>';
  try {
    const res = await fetch(`${API}/scans`);
    const scans = await res.json();
    if (!scans.length) {
      container.innerHTML = '<p class="empty">No scans yet. Launch one from "New Scan".</p>';
      return;
    }
    container.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Scan ID</th><th>Platform</th><th>Status</th>
            <th>Stages Broken</th><th>Breakthrough Rate</th><th>Created</th>
          </tr>
        </thead>
        <tbody>
          ${scans.map(s => `
            <tr onclick="viewScan('${s.scan_id}')">
              <td class="mono">${s.scan_id}</td>
              <td>${s.platform}</td>
              <td>${statusBadge(s.status)}</td>
              <td>${s.stages_broken}</td>
              <td>${(s.breakthrough_rate * 100).toFixed(0)}%</td>
              <td>${formatDate(s.created_at)}</td>
            </tr>`).join('')}
        </tbody>
      </table>`;
  } catch (e) {
    container.innerHTML = `<p class="loading">Error loading scans: ${e.message}</p>`;
  }
}

function statusBadge(status) {
  const map = {
    completed: 'badge-broken',
    running: 'badge-running',
    pending: 'badge-pending',
    failed: 'badge-failed',
  };
  return `<span class="badge ${map[status] || ''}">${status.toUpperCase()}</span>`;
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}

// ── Scan Detail Modal ─────────────────────────────────────────────────────────
async function viewScan(scanId) {
  const modal = document.getElementById('scan-modal');
  const content = document.getElementById('modal-content');
  modal.classList.remove('hidden');
  content.innerHTML = '<p class="loading">Loading scan details…</p>';

  try {
    const res = await fetch(`${API}/scans/${scanId}`);
    const scan = await res.json();
    const stages = scan.stages || [];
    const totalEx = stages.reduce((a, s) => a + (s.outcomes?.EXECUTED || 0), 0);
    const totalBl = stages.reduce((a, s) => a + (s.outcomes?.BLOCKED || 0), 0);
    const totalWa = stages.reduce((a, s) => a + (s.outcomes?.WARNING || 0), 0);

    content.innerHTML = `
      <h3 style="color:#1f3864;margin-bottom:12px">Scan: ${scanId}</h3>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;font-size:.85rem">
        <div><strong>Platform:</strong> ${scan.platform}</div>
        <div><strong>Model:</strong> ${scan.model}</div>
        <div><strong>Status:</strong> ${statusBadge(scan.status)}</div>
        <div><strong>Breakthrough Rate:</strong> ${(scan.breakthrough_rate * 100).toFixed(0)}%</div>
        <div><strong>Total Attempts:</strong> ${scan.total_attempts}</div>
        <div><strong>Stages Broken:</strong> ${scan.stages_broken} / ${stages.length}</div>
      </div>
      <table>
        <thead><tr><th>Stage</th><th>Status</th><th>Attempts</th><th>Technique</th><th>Confidence</th><th>Duration</th></tr></thead>
        <tbody>
          ${stages.map(s => `<tr>
            <td><strong>${s.stage_id}</strong></td>
            <td>${s.broken ? '<span class="badge badge-broken">BROKEN</span>' : '<span class="badge badge-resistant">RESISTANT</span>'}</td>
            <td>${s.attempts}</td>
            <td>${s.winning_technique || '—'}</td>
            <td>${(s.confidence * 100).toFixed(0)}%</td>
            <td>${s.duration_seconds.toFixed(1)}s</td>
          </tr>`).join('')}
        </tbody>
      </table>
      <div class="chart-row">
        <div class="chart-card">
          <h4>Outcome Distribution</h4>
          <canvas id="modal-outcome-chart"></canvas>
        </div>
        <div class="chart-card">
          <h4>Attempts per Stage</h4>
          <canvas id="modal-attempts-chart"></canvas>
        </div>
      </div>
      <div style="margin-top:16px;display:flex;gap:10px">
        <a href="/reports/${scanId}?format=html" target="_blank" class="btn-primary" style="text-decoration:none;padding:8px 16px;font-size:.85rem">⬇ HTML Report</a>
        <a href="/reports/${scanId}?format=json" target="_blank" class="btn-primary" style="text-decoration:none;padding:8px 16px;font-size:.85rem;background:#375623">⬇ JSON</a>
        <a href="/reports/${scanId}?format=csv" target="_blank" class="btn-primary" style="text-decoration:none;padding:8px 16px;font-size:.85rem;background:#7f6000">⬇ CSV</a>
      </div>`;

    // Render charts
    setTimeout(() => {
      new Chart(document.getElementById('modal-outcome-chart'), {
        type: 'doughnut',
        data: {
          labels: ['EXECUTED', 'BLOCKED', 'WARNING'],
          datasets: [{ data: [totalEx, totalBl, totalWa], backgroundColor: ['#c00000','#375623','#7f6000'] }]
        },
        options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
      });
      new Chart(document.getElementById('modal-attempts-chart'), {
        type: 'bar',
        data: {
          labels: stages.map(s => s.stage_id),
          datasets: [{
            label: 'Attempts',
            data: stages.map(s => s.attempts),
            backgroundColor: stages.map(s => s.broken ? '#c00000' : '#9e9e9e'),
            borderRadius: 4,
          }]
        },
        options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
      });
    }, 100);

  } catch (e) {
    content.innerHTML = `<p class="loading">Error: ${e.message}</p>`;
  }
}

function closeModal() {
  document.getElementById('scan-modal').classList.add('hidden');
}

// ── Platform model hints ───────────────────────────────────────────────────────
const MODEL_HINTS = {
  openrouter: 'arcee-ai/trinity-large-preview:free',
  openai:     'gpt-4o-mini',
  anthropic:  'claude-3-haiku-20240307',
  google:     'gemini-1.5-flash',
  huggingface:'meta-llama/Meta-Llama-3-8B-Instruct',
  mock:       '',
};

document.getElementById('target').addEventListener('change', function() {
  const hint = MODEL_HINTS[this.value] || '';
  const modelInput = document.getElementById('model-input');
  modelInput.placeholder = hint ? `e.g. ${hint}` : 'e.g. gpt-4o';
  if (hint) modelInput.value = hint;
});

// ── New Scan ──────────────────────────────────────────────────────────────────
async function launchScan(event) {
  event.preventDefault();
  const form = document.getElementById('scan-form');
  const feedback = document.getElementById('scan-feedback');
  const data = new FormData(form);

  const checkedStages = Array.from(document.querySelectorAll('.stage-cb:checked')).map(cb => cb.value);
  const body = {
    target: data.get('target'),
    model: data.get('model') || null,
    max_payloads: parseInt(data.get('max_payloads')) || 100,
    rate_delay: parseFloat(data.get('rate_delay')) || 2.0,
    stages: checkedStages.length ? checkedStages : ['S1','S2','S3','S4','S5','S6'],
  };

  feedback.textContent = 'Launching scan…';
  feedback.className = 'scan-feedback';

  try {
    const res = await fetch(`${API}/scans`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const scan = await res.json();
    feedback.textContent = `✓ Scan launched: ${scan.scan_id}. Switch to "Scans" to monitor progress.`;
    feedback.className = 'scan-feedback success';
  } catch (e) {
    feedback.textContent = `✗ Error: ${e.message}`;
    feedback.className = 'scan-feedback error';
  }
}

// ── Techniques ────────────────────────────────────────────────────────────────
let _allTechniques = [];

async function loadTechniques() {
  const container = document.getElementById('techniques-container');
  if (_allTechniques.length) { renderTechniques(_allTechniques); return; }
  container.innerHTML = '<p class="loading">Loading techniques…</p>';
  try {
    const res = await fetch(`${API}/techniques`);
    _allTechniques = await res.json();
    renderTechniques(_allTechniques);
  } catch (e) {
    container.innerHTML = `<p class="loading">Error: ${e.message}</p>`;
  }
}

function filterTechniques(cat) {
  const filtered = cat ? _allTechniques.filter(t => t.category === cat) : _allTechniques;
  renderTechniques(filtered);
}

function renderTechniques(techniques) {
  const container = document.getElementById('techniques-container');
  const catColors = { encoding:'cat-encoding', structural:'cat-structural', semantic:'cat-semantic', layered:'cat-layered', trigger:'cat-trigger' };
  container.innerHTML = `
    <p style="margin-bottom:12px;font-size:.85rem;color:#666">${techniques.length} techniques</p>
    <div class="technique-grid">
      ${techniques.map(t => `
        <div class="technique-card">
          <h4>
            <span class="technique-id">${t.id}</span>
            ${t.name}
            <span class="badge-cat ${catColors[t.category] || ''}">${t.category}</span>
          </h4>
          <p>${t.description}</p>
          <p style="margin-top:6px;font-size:.75rem;color:#999">Stage: ${t.lpci_stage} | Tags: ${t.tags.join(', ')}</p>
        </div>`).join('')}
    </div>`;
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  showSection('scans');

  // Auto-refresh running scans every 10s
  setInterval(() => {
    const scansSection = document.getElementById('scans');
    if (!scansSection.classList.contains('hidden')) loadScans();
  }, 10000);
});
