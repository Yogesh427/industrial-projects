const state = { token: localStorage.getItem('phoenixml-token'), mode: 'similar' };
const $ = (id) => document.getElementById(id);

function show(message, type = 'info') {
  const target = $('trainingResult');
  target.className = type === 'error' ? 'empty' : '';
  target.textContent = message;
}

async function api(path, body) {
  if (!state.token) throw new Error('Connect the workspace first.');
  const response = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${state.token}` },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (response.status === 401) {
    localStorage.removeItem('phoenixml-token');
    state.token = null;
    $('authPanel').style.display = 'flex';
    $('sessionState').textContent = 'Session expired. Connect again.';
    throw new Error('Your session expired. Click Connect workspace and try again.');
  }
  if (!response.ok) throw new Error(data.detail || 'Request failed.');
  return data;
}

function csvData() { return $('dataset').value.trim(); }
function algorithm() { return document.querySelector('input[name="algorithm"]:checked').value; }
function isImageAlgorithm() { return ['image-recognition', 'vision-classifier'].includes(algorithm()); }

function updateDatasetMode() {
  const imageMode = isImageAlgorithm();
  $('imageUploadArea').hidden = !imageMode;
  $('dataset').hidden = imageMode;
  $('inspectButton').disabled = imageMode && !$('imageInput').files.length;
}

function renderPreview(data) {
  const sample = data.sample.map(row => `<tr>${Object.values(row).map(value => `<td>${value}</td>`).join('')}</tr>`).join('');
  $('datasetSummary').textContent = `${data.rows} rows / ${data.columns.length} columns / ${data.labels.length || 'no'} labels`;
  $('dataset').insertAdjacentHTML('afterend', `<div class="table-preview" id="preview"><table><thead><tr>${data.columns.map(column => `<th>${column}</th>`).join('')}</tr></thead><tbody>${sample}</tbody></table></div>`);
}

$('loginButton').addEventListener('click', async () => {
  try {
    const body = new URLSearchParams({ username: $('username').value, password: $('password').value });
    const response = await fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
    if (!response.ok) throw new Error('Invalid login.');
    const data = await response.json();
    state.token = data.access_token;
    localStorage.setItem('phoenixml-token', state.token);
    $('sessionState').textContent = 'Connected as admin';
    $('authPanel').style.display = 'none';
  } catch (error) { $('sessionState').textContent = error.message; }
});

$('fileInput').addEventListener('change', (event) => {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => { $('dataset').value = reader.result; $('datasetSummary').textContent = `${file.name} loaded`; };
  reader.readAsText(file);
});

document.querySelectorAll('input[name="algorithm"]').forEach(input => input.addEventListener('change', updateDatasetMode));

$('imageInput').addEventListener('change', async () => {
  const files = [...$('imageInput').files];
  if (!files.length) return;
  $('trainButton').disabled = true;
  $('generateButton').disabled = true;
  $('continueTrainingButton').hidden = true;
  try {
    if (!state.token) throw new Error('Connect the workspace first.');
    const csvRows = [];
    const sampleRows = [];
    const labels = new Set();
    let columns = [];
    for (let start = 0; start < files.length; start += 100) {
      const form = new FormData();
      files.slice(start, start + 100).forEach(file => form.append('files', file));
      const response = await fetch('/api/training/image-preview', { method: 'POST', headers: { Authorization: `Bearer ${state.token}` }, body: form });
      const data = await response.json().catch(() => ({}));
      if (response.status === 401) {
        localStorage.removeItem('phoenixml-token');
        state.token = null;
        $('authPanel').style.display = 'flex';
        throw new Error('Your session expired. Connect again and retry the upload.');
      }
      if (!response.ok) throw new Error(data.detail || 'Image upload failed.');
      columns = data.columns;
      csvRows.push(...data.data.split(/\r?\n/).slice(1).filter(Boolean));
      sampleRows.push(...data.sample);
      data.labels.forEach(label => labels.add(label));
      $('imageSummary').textContent = `${Math.min(start + 100, files.length)} of ${files.length} image files checked`;
    }
    const csv = [columns.join(','), ...csvRows].join('\n');
    $('dataset').value = csv;
    $('imageSummary').textContent = `${files.length} images loaded in batches / choose Train model to continue`;
    $('datasetSummary').textContent = `${files.length} image rows ready`;
    $('continueTrainingButton').hidden = false;
    $('trainButton').disabled = false;
    $('generateButton').disabled = false;
    document.getElementById('preview')?.remove();
    renderPreview({ rows: files.length, columns, labels: [...labels], sample: sampleRows.slice(0, 5) });
  } catch (error) {
    $('trainButton').disabled = false;
    $('generateButton').disabled = false;
    $('imageSummary').textContent = error.message;
  }
});

$('continueTrainingButton').addEventListener('click', () => {
  $('trainButton').scrollIntoView({ behavior: 'smooth', block: 'center' });
  $('trainButton').focus();
});

$('inspectButton').addEventListener('click', async () => {
  try {
    const data = await api('/training/preview', { data: csvData() });
    document.getElementById('preview')?.remove();
    renderPreview(data);
  } catch (error) { $('datasetSummary').textContent = error.message; }
});

$('trainButton').addEventListener('click', async () => {
  try {
    show('Training in progress...');
    const data = await api('/training/train', { data: csvData(), algorithm: algorithm() });
    const compute = data.compute ? `${data.compute.backend.toUpperCase()} / ${data.compute.device}` : 'CPU parallel';
    const metrics = data.metric_type === 'regression'
      ? `<div class="metric"><small>R2 score</small><strong>${data.metrics.r2}</strong></div><div class="metric"><small>MAE</small><strong>${data.metrics.mae}</strong></div><div class="metric"><small>RMSE</small><strong>${data.metrics.rmse}</strong></div>`
      : `<div class="metric"><small>Accuracy</small><strong>${data.metrics.accuracy}</strong></div><div class="metric"><small>F1 score</small><strong>${data.metrics.validation_score}</strong></div><div class="metric"><small>Rows</small><strong>${data.rows_used}</strong></div>`;
    $('trainingResult').innerHTML = `<div class="metric-row">${metrics}</div><p class="hint">${data.message} Compute: ${compute}. Features: ${data.features.join(', ')}</p><p class="hint">Saved artifact: ${data.artifact_id}</p>`;
  } catch (error) { show(error.message, 'error'); }
});

document.querySelectorAll('.mode').forEach(button => button.addEventListener('click', () => {
  state.mode = button.dataset.mode;
  document.querySelectorAll('.mode').forEach(item => item.classList.toggle('active', item === button));
}));

$('generateButton').addEventListener('click', async () => {
  try {
    if (isImageAlgorithm() && $('imageInput').files.length) {
      const form = new FormData();
      [...$('imageInput').files].slice(0, 100).forEach(file => form.append('files', file));
      form.append('mode', state.mode);
      form.append('count', $('rowCount').value);
      const response = await fetch('/api/training/generate-images', { method: 'POST', headers: { Authorization: `Bearer ${state.token}` }, body: form });
      const imageData = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(imageData.detail || 'Image generation failed.');
      $('generatedResult').innerHTML = `<p>${imageData.count} real ${imageData.mode} image(s) created.</p><div class="generated-images">${imageData.images.map(image => `<a href="${image.url}" download><img src="${image.url}" alt="Generated ${imageData.mode} image" /><small>${image.filename}</small></a>`).join('')}</div>`;
      $('downloadLink').hidden = true;
      return;
    }
    const data = await api('/training/generate', { data: csvData(), mode: state.mode, count: Number($('rowCount').value) });
    $('generatedResult').textContent = `${data.count} ${data.mode} rows ready. Add them to your next training cycle.`;
    const blob = new Blob([data.csv], { type: 'text/csv' });
    const link = $('downloadLink');
    link.href = URL.createObjectURL(blob);
    link.download = `phoenixml_${data.mode}_dataset.csv`;
    link.hidden = false;
    link.textContent = `Download ${data.count} generated rows`;
  } catch (error) { $('generatedResult').textContent = error.message; }
});

async function validateSession() {
  if (!state.token) return;
  const response = await fetch('/api/me', { headers: { Authorization: `Bearer ${state.token}` } });
  if (response.ok) {
    $('sessionState').textContent = 'Connected from PhoenixML';
    $('authPanel').style.display = 'none';
    return;
  }
  localStorage.removeItem('phoenixml-token');
  state.token = null;
  $('authPanel').style.display = 'flex';
  $('sessionState').textContent = 'Session expired. Connect workspace again.';
}

validateSession();
updateDatasetMode();
