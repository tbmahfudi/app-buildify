/**
 * UI Utilities - Toast notifications, loading states, etc.
 */

/**
 * Show toast notification
 */
export function showToast(message, type = 'info', duration = 5000) {
  const container = document.getElementById('toast-container');
  
  const colors = {
    success: 'bg-green-50 border-green-500 text-green-800',
    error: 'bg-red-50 border-red-500 text-red-800',
    warning: 'bg-yellow-50 border-yellow-500 text-yellow-800',
    info: 'bg-blue-50 border-blue-500 text-blue-800'
  };
  
  const icons = {
    success: 'bi-check-circle-fill',
    error: 'bi-exclamation-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    info: 'bi-info-circle-fill'
  };
  
  const toast = document.createElement('div');
  toast.className = `${colors[type]} border-l-4 rounded-lg shadow-lg p-4 min-w-[300px] max-w-md transform transition-all duration-300 translate-x-full`;
  
  toast.innerHTML = `
    <div class="flex items-start gap-3">
      <i class="bi ${icons[type]} text-xl flex-shrink-0 mt-0.5"></i>
      <div class="flex-1">
        <p class="text-sm font-medium">${escapeHtml(message)}</p>
      </div>
      <button class="text-gray-500 hover:text-gray-700 transition flex-shrink-0" onclick="this.closest('[class*=bg-]').remove()">
        <i class="bi bi-x-lg"></i>
      </button>
    </div>
  `;
  
  container.appendChild(toast);
  
  // Trigger animation
  setTimeout(() => {
    toast.classList.remove('translate-x-full');
  }, 10);
  
  // Auto remove
  if (duration > 0) {
    setTimeout(() => {
      toast.classList.add('translate-x-full');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
}

/**
 * Show global loading overlay
 */
export function showLoading() {
  const overlay = document.getElementById('loading-overlay');
  overlay.classList.remove('hidden');
}

/**
 * Hide global loading overlay
 */
export function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  overlay.classList.add('hidden');
}

/**
 * Confirm dialog
 */
export function confirm(message, title = 'Confirm') {
  return window.confirm(`${title}\n\n${message}`);
}

/**
 * Escape HTML to prevent XSS
 */
export function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Format date
 */
export function formatDate(dateString, format = 'short') {
  const date = new Date(dateString);
  
  if (format === 'short') {
    return date.toLocaleDateString();
  }
  
  if (format === 'long') {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
  
  if (format === 'datetime') {
    return date.toLocaleString();
  }
  
  return date.toLocaleDateString();
}

/**
 * Format currency
 */
export function formatCurrency(amount, currency = 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency
  }).format(amount);
}

/**
 * Debounce function
 */
export function debounce(func, wait = 300) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Handle API errors with specific messages for common HTTP status codes
 * @param {Response} response - The fetch response object
 * @param {string} defaultMessage - Default error message if no specific handling
 * @returns {Promise<Error>} - A promise that rejects with an appropriate error
 */
export async function handleApiError(response, defaultMessage = 'An error occurred') {
  let errorMessage = defaultMessage;
  let errorDetail = null;

  try {
    // Try to parse error body
    const errorData = await response.json();
    errorDetail = errorData.detail || errorData.message || null;
  } catch {
    // If JSON parsing fails, ignore and use status-based messages
  }

  // Handle specific HTTP status codes
  switch (response.status) {
    case 400:
      errorMessage = errorDetail || 'Bad request - please check your input';
      break;
    case 401:
      errorMessage = 'Unauthorized - please log in again';
      break;
    case 403:
      errorMessage = errorDetail || 'Access forbidden - you don\'t have permission to access this resource';
      break;
    case 404:
      errorMessage = errorDetail || 'Resource not found';
      break;
    case 409:
      errorMessage = errorDetail || 'Conflict - the resource already exists or there\'s a conflict';
      break;
    case 422:
      errorMessage = errorDetail || 'Validation error - please check your input';
      break;
    case 429:
      errorMessage = 'Too many requests - please slow down';
      break;
    case 500:
      errorMessage = errorDetail || 'Internal server error - please try again later';
      break;
    case 502:
      errorMessage = 'Bad gateway - the server is temporarily unavailable';
      break;
    case 503:
      errorMessage = 'Service unavailable - please try again later';
      break;
    case 504:
      errorMessage = 'Gateway timeout - the request took too long';
      break;
    default:
      errorMessage = errorDetail || `${defaultMessage} (HTTP ${response.status})`;
  }

  return new Error(errorMessage);
}

/**
 * Wrapper for fetch with better error handling
 * @param {string} url - The URL to fetch
 * @param {object} options - Fetch options
 * @returns {Promise<Response>} - The fetch response
 */
export async function fetchWithErrorHandling(url, options = {}) {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const error = await handleApiError(response, 'Request failed');
      throw error;
    }

    return response;
  } catch (error) {
    // Re-throw with context if it's a network error
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error - please check your connection');
    }
    throw error;
  }
}