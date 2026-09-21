const demoModels = [
  { id: 'm1', name: 'SpamGuard-v1', status: 'HEALTHY', health: 92.3, action: 'CONTINUE_MONITORING', drift: 'Low', evidence: 'F1 stable at 0.92' },
  { id: 'm2', name: 'MarketingFilter', status: 'WARNING', health: 66.7, action: 'HUMAN_REVIEW', drift: 'Moderate', evidence: 'Vocabulary shift detected' },
  { id: 'm3', name: 'FraudTextGuard', status: 'CRITICAL', health: 48.2, action: 'RETRAIN', drift: 'High', evidence: 'Concept drift + low recall' },
];

const state = {
  loggedIn: false,
  activeView: 'overview',
  models: [...demoModels],
};

const loginForm = document.getElementById('loginForm');
const loginScreen = document.getElementById('loginScreen');
const dashboardScreen = document.getElementById('dashboardScreen');
const alertBox = document.getElementById('alertBox');
const overviewTab = document.getElementById('overviewTab');
const modelTab = document.getElementById('modelTab');
const metricsContainer = document.getElementById('metricsContainer');
const modelTableBody = document.getElementById('modelTableBody');
const explanationText = document.getElementById('explanationText');
const modelForm = document.getElementById('modelForm');
const monitoringForm = document.getElementById('monitoringForm');
const generationForm = document.getElementById('generationForm');
const selectedModel = document.getElementById('selectedModel');
const evaluateBtn = document.getElementById('evaluateBtn');
const logoutBtn = document.getElementById('logoutBtn');

async function generateImages(event) {
  event.preventDefault();
  const token = localStorage.getItem('phoenixml-token');
  const style = document.getElementById('generationStyle').value;
  const count = Number(document.getElementById('generationCount').value || 1);
  const response = await fetch('/api/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ style, count })
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Image generation failed');
  }

  const data = await response.json();
  document.getElementById('generatedImages').innerHTML = data.images.map((image) => `
    <div>
      <img src="${image.url}" alt="Generated ${data.style} image" />
      <a href="${image.url}" download>Download PNG</a>
    </div>
  `).join('');
  alertBox.textContent = `${data.images.length} ${data.style} image(s) generated.`;
  alertBox.hidden = false;
}

function renderMetrics() {
  const healthy = state.models.filter((m) => m.status === 'HEALTHY').length;
  const warning = state.models.filter((m) => m.status === 'WARNING').length;
  const critical = state.models.filter((m) => m.status === 'CRITICAL').length;

  const cards = [
    { label: 'Healthy', value: healthy, tone: 'safe' },
    { label: 'Warning', value: warning, tone: 'warning' },
    { label: 'Critical', value: critical, tone: 'critical' },
    { label: 'Total models', value: state.models.length, tone: 'info' }
  ];

  metricsContainer.innerHTML = cards.map(card => `
    <div class="card ${card.tone}">
      <span>${card.label}</span>
      <strong>${card.value}</strong>
    </div>
  `).join('');
}

function renderTable() {
  modelTableBody.innerHTML = state.models.map(model => `
    <tr>
      <td>${model.name}</td>
      <td><span class="badge ${model.status.toLowerCase()}">${model.status}</span></td>
      <td>${model.health}/100</td>
      <td>${model.action}</td>
      <td>${model.drift}</td>
    </tr>
  `).join('');
}

function renderModelOptions() {
  selectedModel.innerHTML = state.models.map(model => `<option value="${model.id}" data-algorithm="${model.algorithm || ''}">${model.name} (${model.algorithm || 'model'})</option>`).join('');
  updateTelemetryFields();
}

function updateTelemetryFields() {
  const model = state.models.find(item => String(item.id) === String(selectedModel.value));
  const regression = model?.algorithm === 'linear-regression';
  document.getElementById('metricOneLabel').textContent = regression ? 'R2 Score' : 'Accuracy';
  document.getElementById('metricTwoLabel').textContent = regression ? 'RMSE (reference)' : 'F1 Score';
  document.getElementById('metricOne').value = regression ? '0.90' : '0.90';
  document.getElementById('metricTwo').value = regression ? '0.10' : '0.88';
}

function setActiveTab(tab) {
  state.activeView = tab;
  overviewTab.classList.toggle('active', tab === 'overview');
  modelTab.classList.toggle('active', tab === 'models');

  if (tab === 'overview') {
    explanationText.textContent = 'PhoenixML evaluates model health across drift, performance, and explainability signals before recommending maintenance actions.';
  } else {
    explanationText.textContent = 'Model ownership, evaluation history, and approval states are tracked to support safe human-in-the-loop decisions.';
  }
}

async function loginUser(username, password) {
  const formBody = new URLSearchParams({ username, password });
  const response = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formBody
  });

  if (!response.ok) {
    throw new Error('Invalid credentials');
  }

  const data = await response.json();
  localStorage.setItem('phoenixml-token', data.access_token);
  return data;
}

async function loadDashboard() {
  const token = localStorage.getItem('phoenixml-token');
  if (!token) return;

  const response = await fetch('/api/dashboard', {
    headers: { Authorization: `Bearer ${token}` }
  });

  if (!response.ok) {
    throw new Error('Dashboard load failed');
  }

  const data = await response.json();
  if (Array.isArray(data.models) && data.models.length > 0) {
    state.models = data.models.map((model, index) => ({
      id: model.id,
      name: model.model,
      algorithm: model.algorithm,
      status: model.latest_health === 'UNKNOWN' ? 'WARNING' : model.latest_health,
      health: Number(model.latest_health_score || 0),
      action: model.latest_health === 'UNKNOWN' ? 'INCREASED_MONITORING' : 'CONTINUE_MONITORING',
      drift: model.latest_health === 'UNKNOWN' ? 'Moderate' : 'Low',
    }));
  }

  renderMetrics();
  renderTable();
  renderModelOptions();
}

async function createModel(event) {
  event.preventDefault();
  const token = localStorage.getItem('phoenixml-token');
  const name = document.getElementById('modelName').value.trim();
  const algorithm = document.getElementById('modelAlgorithm').value;

  if (!token || !name) return;

  const response = await fetch('/api/models', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ name, algorithm, status: 'ACTIVE' })
  });

  if (response.ok) {
    const model = await response.json();
    state.models.push({
      id: model.id,
      name: model.name,
      algorithm: model.algorithm,
      status: 'UNKNOWN',
      health: 0,
      action: 'AWAITING_TELEMETRY',
      drift: 'Unknown'
    });
    renderMetrics();
    renderTable();
    renderModelOptions();
    document.getElementById('modelForm').reset();
    alertBox.textContent = `Model ${model.name} registered successfully.`;
    alertBox.hidden = false;
  }
}

async function sendTelemetry(event) {
  event.preventDefault();
  const token = localStorage.getItem('phoenixml-token');
  const modelId = selectedModel.value;
  const model = state.models.find(item => String(item.id) === String(modelId));
  const metricOne = Number(document.getElementById('metricOne').value || 0);
  const metricTwo = Number(document.getElementById('metricTwo').value || 0);
  const regression = model?.algorithm === 'linear-regression';

  if (!token || !modelId) return;

  const payload = {
    total_predictions: 1200,
    spam_predictions: 540,
    ham_predictions: 660,
    accuracy: regression ? metricOne : metricOne,
    precision: 0.82,
    recall: 0.8,
    f1_score: regression ? Math.max(0, 1 - metricTwo) : metricTwo,
    r2_score: regression ? metricOne : undefined,
    notes: regression ? 'Linear regression R2 and RMSE telemetry.' : `${model?.algorithm || 'model'} accuracy and F1 telemetry.`
  };

  const response = await fetch(`/api/models/${modelId}/monitoring`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });

  if (response.ok) {
    const entry = await response.json();
    const model = state.models.find((item) => item.id === modelId);
    if (model) {
      model.health = Number(entry.health_score.toFixed(1));
      model.status = model.health >= 80 ? 'HEALTHY' : model.health >= 60 ? 'WARNING' : 'CRITICAL';
      model.action = model.status === 'HEALTHY' ? 'CONTINUE_MONITORING' : model.status === 'WARNING' ? 'HUMAN_REVIEW' : 'RETRAIN';
      model.drift = model.status === 'HEALTHY' ? 'Low' : model.status === 'WARNING' ? 'Moderate' : 'High';
    }

    renderMetrics();
    renderTable();
    alertBox.textContent = `Telemetry received for ${entry.model_id}.`;
    alertBox.hidden = false;
  }
}

function evaluateModels() {
  state.models = state.models.map((m) => {
    let status = 'HEALTHY';
    let action = 'CONTINUE_MONITORING';
    let drift = 'Low';

    if (m.health < 60) {
      status = 'CRITICAL';
      action = 'RETRAIN';
      drift = 'High';
    } else if (m.health < 80) {
      status = 'WARNING';
      action = 'HUMAN_REVIEW';
      drift = 'Moderate';
    }

    return { ...m, status, action, drift };
  });

  renderMetrics();
  renderTable();
  explanationText.textContent = 'AIMD decision evaluation complete: the system recommends maintenance actions based on the latest health and drift signals.';
}

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;

  if (!username || !password) {
    alertBox.textContent = 'Please enter both username and password.';
    alertBox.hidden = false;
    return;
  }

  try {
    await loginUser(username, password);
    state.loggedIn = true;
    loginScreen.hidden = true;
    dashboardScreen.hidden = false;
    alertBox.hidden = true;
    await loadDashboard();
    renderModelOptions();
    setActiveTab('overview');
  } catch (error) {
    alertBox.textContent = 'Demo login: username = admin, password = admin123';
    alertBox.hidden = false;
  }
});

modelForm.addEventListener('submit', createModel);
monitoringForm.addEventListener('submit', sendTelemetry);
generationForm.addEventListener('submit', async (event) => {
  try {
    await generateImages(event);
  } catch (error) {
    alertBox.textContent = error.message;
    alertBox.hidden = false;
  }
});
overviewTab.addEventListener('click', () => setActiveTab('overview'));
modelTab.addEventListener('click', () => setActiveTab('models'));
evaluateBtn.addEventListener('click', evaluateModels);
selectedModel.addEventListener('change', updateTelemetryFields);
logoutBtn.addEventListener('click', () => {
  localStorage.removeItem('phoenixml-token');
  state.loggedIn = false;
  loginScreen.hidden = false;
  dashboardScreen.hidden = true;
  document.getElementById('loginForm').reset();
});

renderMetrics();
renderTable();
renderModelOptions();
setActiveTab('overview');
dashboardScreen.hidden = true;
alertBox.hidden = true;
