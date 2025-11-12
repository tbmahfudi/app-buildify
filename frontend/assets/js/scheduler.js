/**
 * Scheduler Management Module
 * Handles configuration and job management for the hierarchical scheduler
 */

// Tab management
document.querySelectorAll('.scheduler-tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;

    // Update tab buttons
    document.querySelectorAll('.scheduler-tab-btn').forEach(b => {
      b.classList.remove('border-blue-600', 'text-blue-600');
      b.classList.add('border-transparent', 'text-gray-500');
    });
    btn.classList.remove('border-transparent', 'text-gray-500');
    btn.classList.add('border-blue-600', 'text-blue-600');

    // Update tab content
    document.querySelectorAll('.scheduler-tab-content').forEach(content => {
      content.classList.add('hidden');
    });
    document.getElementById(`tab-${tab}`).classList.remove('hidden');

    // Load data for the active tab
    if (tab === 'configurations') {
      loadConfigurations();
    } else if (tab === 'jobs') {
      loadJobs();
    } else if (tab === 'executions') {
      loadExecutions();
    }
  });
});

// Configuration CRUD
document.getElementById('btn-create-config').addEventListener('click', () => {
  document.getElementById('modal-config-title').textContent = 'Create Configuration';
  document.getElementById('form-config').reset();
  document.getElementById('config-id').value = '';
  document.getElementById('modal-config').classList.remove('hidden');
  document.getElementById('modal-config').classList.add('flex');
});

document.getElementById('btn-cancel-config').addEventListener('click', () => {
  document.getElementById('modal-config').classList.add('hidden');
  document.getElementById('modal-config').classList.remove('flex');
});

document.getElementById('form-config').addEventListener('submit', async (e) => {
  e.preventDefault();

  const configId = document.getElementById('config-id').value;
  const data = {
    config_level: document.getElementById('config-level').value,
    name: document.getElementById('config-name').value,
    description: document.getElementById('config-description').value,
    is_enabled: document.getElementById('config-enabled').checked,
    max_concurrent_jobs: parseInt(document.getElementById('config-max-jobs').value),
    default_timezone: document.getElementById('config-timezone').value,
    max_retries: parseInt(document.getElementById('config-max-retries').value),
    retry_delay_seconds: parseInt(document.getElementById('config-retry-delay').value),
    job_timeout_seconds: parseInt(document.getElementById('config-timeout').value),
    notify_on_failure: document.getElementById('config-notify-failure').checked,
    notify_on_success: document.getElementById('config-notify-success').checked
  };

  try {
    let response;
    if (configId) {
      response = await api.put(`/scheduler/configs/${configId}`, data);
    } else {
      response = await api.post('/scheduler/configs', data);
    }

    showNotification(configId ? 'Configuration updated successfully' : 'Configuration created successfully', 'success');
    document.getElementById('modal-config').classList.add('hidden');
    document.getElementById('modal-config').classList.remove('flex');
    loadConfigurations();
  } catch (error) {
    showNotification('Error saving configuration: ' + error.message, 'error');
  }
});

// Job CRUD
document.getElementById('btn-create-job').addEventListener('click', async () => {
  document.getElementById('modal-job-title').textContent = 'Create Scheduled Job';
  document.getElementById('form-job').reset();
  document.getElementById('job-id').value = '';

  // Load configurations for dropdown
  await loadConfigurationsDropdown();

  document.getElementById('modal-job').classList.remove('hidden');
  document.getElementById('modal-job').classList.add('flex');
});

document.getElementById('btn-cancel-job').addEventListener('click', () => {
  document.getElementById('modal-job').classList.add('hidden');
  document.getElementById('modal-job').classList.remove('flex');
});

document.getElementById('form-job').addEventListener('submit', async (e) => {
  e.preventDefault();

  const jobId = document.getElementById('job-id').value;
  const data = {
    config_id: parseInt(document.getElementById('job-config-id').value),
    job_type: document.getElementById('job-type').value,
    name: document.getElementById('job-name').value,
    description: document.getElementById('job-description').value,
    is_active: document.getElementById('job-active').checked,
    cron_expression: document.getElementById('job-cron').value || null,
    interval_seconds: parseInt(document.getElementById('job-interval').value) || null,
    timezone: document.getElementById('job-timezone').value
  };

  try {
    let response;
    if (jobId) {
      response = await api.put(`/scheduler/jobs/${jobId}`, data);
    } else {
      response = await api.post('/scheduler/jobs', data);
    }

    showNotification(jobId ? 'Job updated successfully' : 'Job created successfully', 'success');
    document.getElementById('modal-job').classList.add('hidden');
    document.getElementById('modal-job').classList.remove('flex');
    loadJobs();
  } catch (error) {
    showNotification('Error saving job: ' + error.message, 'error');
  }
});

// Load functions
async function loadConfigurations() {
  try {
    const level = document.getElementById('filter-config-level').value;
    const params = level ? `?config_level=${level}` : '';

    // Note: You'll need to implement a list endpoint or adjust this
    const tbody = document.getElementById('configurations-table-body');
    tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">Loading configurations...</td></tr>';

    // Placeholder for actual API call
    showNotification('Configuration listing not yet fully implemented', 'info');
  } catch (error) {
    showNotification('Error loading configurations: ' + error.message, 'error');
  }
}

async function loadJobs() {
  try {
    const type = document.getElementById('filter-job-type').value;
    const status = document.getElementById('filter-job-status').value;
    let params = [];
    if (type) params.push(`job_type=${type}`);
    if (status) params.push(`is_active=${status}`);

    const response = await api.get(`/scheduler/jobs?${params.join('&')}`);
    const tbody = document.getElementById('jobs-table-body');

    if (response.items && response.items.length > 0) {
      tbody.innerHTML = response.items.map(job => `
        <tr>
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${job.name}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${job.job_type}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${job.cron_expression || `Every ${job.interval_seconds}s`}</td>
          <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${job.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
              ${job.is_active ? 'Active' : 'Inactive'}
            </span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${job.last_run_at ? new Date(job.last_run_at).toLocaleString() : 'Never'}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${job.next_run_at ? new Date(job.next_run_at).toLocaleString() : '-'}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${job.success_count} / ${job.failure_count}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
            <button onclick="executeJob(${job.id})" class="text-green-600 hover:text-green-900 mr-3">Run</button>
            <button onclick="editJob(${job.id})" class="text-blue-600 hover:text-blue-900 mr-3">Edit</button>
            <button onclick="deleteJob(${job.id})" class="text-red-600 hover:text-red-900">Delete</button>
          </td>
        </tr>
      `).join('');
    } else {
      tbody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 text-center text-gray-500">No jobs found</td></tr>';
    }
  } catch (error) {
    showNotification('Error loading jobs: ' + error.message, 'error');
  }
}

async function loadExecutions() {
  try {
    const jobId = document.getElementById('filter-execution-job').value;
    const status = document.getElementById('filter-execution-status').value;
    let params = [];
    if (jobId) params.push(`job_id=${jobId}`);
    if (status) params.push(`status=${status}`);

    const tbody = document.getElementById('executions-table-body');
    tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500">Select a job to view execution history</td></tr>';
  } catch (error) {
    showNotification('Error loading executions: ' + error.message, 'error');
  }
}

async function loadConfigurationsDropdown() {
  try {
    // Placeholder - would load from API
    const select = document.getElementById('job-config-id');
    select.innerHTML = '<option value="1">System Configuration</option>';
  } catch (error) {
    console.error('Error loading configurations:', error);
  }
}

// Action functions
async function executeJob(jobId) {
  if (!confirm('Are you sure you want to execute this job now?')) return;

  try {
    await api.post(`/scheduler/jobs/${jobId}/execute`, {});
    showNotification('Job execution triggered', 'success');
    loadJobs();
  } catch (error) {
    showNotification('Error executing job: ' + error.message, 'error');
  }
}

async function editJob(jobId) {
  try {
    const job = await api.get(`/scheduler/jobs/${jobId}`);

    document.getElementById('modal-job-title').textContent = 'Edit Scheduled Job';
    document.getElementById('job-id').value = job.id;
    document.getElementById('job-name').value = job.name;
    document.getElementById('job-type').value = job.job_type;
    document.getElementById('job-description').value = job.description || '';
    document.getElementById('job-config-id').value = job.config_id;
    document.getElementById('job-timezone').value = job.timezone;
    document.getElementById('job-cron').value = job.cron_expression || '';
    document.getElementById('job-interval').value = job.interval_seconds || '';
    document.getElementById('job-active').checked = job.is_active;

    await loadConfigurationsDropdown();

    document.getElementById('modal-job').classList.remove('hidden');
    document.getElementById('modal-job').classList.add('flex');
  } catch (error) {
    showNotification('Error loading job: ' + error.message, 'error');
  }
}

async function deleteJob(jobId) {
  if (!confirm('Are you sure you want to delete this job?')) return;

  try {
    await api.delete(`/scheduler/jobs/${jobId}`);
    showNotification('Job deleted successfully', 'success');
    loadJobs();
  } catch (error) {
    showNotification('Error deleting job: ' + error.message, 'error');
  }
}

// Utility function
function showNotification(message, type = 'info') {
  // Use existing notification system if available
  if (window.showNotification) {
    window.showNotification(message, type);
  } else {
    console.log(`[${type}] ${message}`);
    alert(message);
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadConfigurations();
});

// Filter listeners
document.getElementById('filter-config-level').addEventListener('change', loadConfigurations);
document.getElementById('filter-job-type').addEventListener('change', loadJobs);
document.getElementById('filter-job-status').addEventListener('change', loadJobs);
