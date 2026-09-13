const form = document.querySelector('#forge-form');
const input = document.querySelector('#video-input');
const dropZone = document.querySelector('#drop-zone');
const fileLabel = document.querySelector('#file-label');
const statusPanel = document.querySelector('#status-panel');
const statusText = document.querySelector('#status-text');
const statusDetail = document.querySelector('#status-detail');
const progressBar = document.querySelector('#progress-bar');
const downloadLink = document.querySelector('#download-link');

input.addEventListener('change', () => { if (input.files[0]) fileLabel.textContent = input.files[0].name; });
['dragenter', 'dragover'].forEach(event => dropZone.addEventListener(event, e => { e.preventDefault(); dropZone.classList.add('dragging'); }));
['dragleave', 'drop'].forEach(event => dropZone.addEventListener(event, e => { e.preventDefault(); dropZone.classList.remove('dragging'); }));
dropZone.addEventListener('drop', e => { input.files = e.dataTransfer.files; if (input.files[0]) fileLabel.textContent = input.files[0].name; });

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (!input.files[0]) return;
  statusPanel.hidden = false;
  downloadLink.hidden = true;
  statusText.textContent = 'Uploading...';
  progressBar.style.width = '3%';
  const body = new FormData();
  body.append('file', input.files[0]);
  const fps = document.querySelector('input[name="fps"]:checked').value;
  const response = await fetch(`/api/jobs?target_fps=${fps}`, { method: 'POST', body });
  if (!response.ok) return showError((await response.json()).detail || 'Upload failed.');
  const { id } = await response.json();
  poll(id, fps);
});

async function poll(id, fps) {
  const response = await fetch(`/api/jobs/${id}`);
  const job = await response.json();
  progressBar.style.width = `${job.progress || 5}%`;
  if (job.status === 'complete') {
    statusText.textContent = 'Complete';
    statusDetail.textContent = `Your ${fps} FPS master is ready to download.`;
    downloadLink.href = `/api/jobs/${id}/download`;
    downloadLink.hidden = false;
  } else if (job.status === 'error') showError(job.message);
  else { statusText.textContent = job.status === 'queued' ? 'Queued...' : 'Forging frames...'; setTimeout(() => poll(id, fps), 1200); }
}
function showError(message) { statusText.textContent = 'Could not process video'; statusDetail.textContent = message; progressBar.style.width = '0'; }
