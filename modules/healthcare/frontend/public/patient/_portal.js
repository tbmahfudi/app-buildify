/*
 * Healthcare patient-portal shared bootstrap (public-portal Phase 2).
 *
 * Served at /portal/healthcare/patient/_portal.js and loaded FIRST on every
 * patient page. It provides the runtime contract the individual patient page
 * scripts assume but never define themselves:
 *
 *   - window.apiFetch(url, opts?)  -> parsed JSON, Bearer-authed, 401 -> login
 *   - window.t(localeOrKey, key?)  -> tolerant i18n lookup (no hard dep)
 *   - patient-token guard          -> redirect to the portal login when absent
 *   - link normalization           -> authored /patient/<x> links are rewritten
 *                                      to the served /portal/healthcare/patient/
 *                                      tree so navigation works statically.
 *
 * Token storage: reuses the SAME key the live Phase-1 portal sets on login
 * (localStorage 'hc_patient_token'); also accepts sessionStorage 'access_token'
 * for forward-compat with the richer pages' own assumption.
 *
 * Static / no-SSR: pure browser JS, no build step. Real backticks only.
 */
(function () {
  'use strict';

  var PORTAL_BASE = '/portal/healthcare/';
  var PATIENT_BASE = PORTAL_BASE + 'patient/';
  var LOGIN_URL = PORTAL_BASE + '#login';

  function getToken() {
    return (
      window.localStorage.getItem('hc_patient_token') ||
      window.sessionStorage.getItem('access_token') ||
      ''
    );
  }

  function redirectToLogin() {
    window.location.href = LOGIN_URL;
  }

  // Token-key bridge: the live Phase-1 portal stores the patient JWT under
  // localStorage 'hc_patient_token', but the richer pages' own inline guards
  // read sessionStorage 'access_token'. Mirror the value across both keys so
  // every page (whichever key it checks) sees the same authenticated session.
  (function bridgeTokenKeys() {
    var ls = window.localStorage.getItem('hc_patient_token');
    var ss = window.sessionStorage.getItem('access_token');
    if (ls && !ss) window.sessionStorage.setItem('access_token', ls);
    else if (ss && !ls) window.localStorage.setItem('hc_patient_token', ss);
  })();

  // ----- token guard ---------------------------------------------------------
  // Pages opt out by setting window.__PATIENT_PUBLIC = true before this loads.
  if (!window.__PATIENT_PUBLIC && !getToken()) {
    redirectToLogin();
  }

  // ----- apiFetch ------------------------------------------------------------
  // Returns parsed JSON (the majority contract across patient page scripts).
  // On 401 the patient token is cleared and we bounce to login.
  window.apiFetch = async function apiFetch(url, opts) {
    opts = opts || {};
    var headers = Object.assign(
      { 'Content-Type': 'application/json' },
      opts.headers || {}
    );
    var token = getToken();
    if (token) headers['Authorization'] = 'Bearer ' + token;

    var res = await fetch(url, Object.assign({}, opts, { headers: headers }));

    if (res.status === 401) {
      window.localStorage.removeItem('hc_patient_token');
      window.sessionStorage.removeItem('access_token');
      redirectToLogin();
      throw new Error('unauthorized');
    }
    if (!res.ok) {
      var detail = '';
      try {
        detail = (await res.json()).detail || '';
      } catch (e) {
        detail = res.statusText;
      }
      throw new Error(detail || ('HTTP ' + res.status));
    }
    if (res.status === 204) return null;
    var ct = res.headers.get('content-type') || '';
    return ct.indexOf('application/json') !== -1 ? res.json() : res.text();
  };

  // ----- i18n shim -----------------------------------------------------------
  // The page scripts call t(locale, key) OR t(key). Be tolerant: if a real
  // i18n module later defines window.HC_T, defer to it; otherwise echo a
  // humanized fallback so the UI is never blank.
  if (typeof window.t !== 'function') {
    window.t = function t(a, b) {
      var key = b !== undefined ? b : a;
      if (typeof window.HC_T === 'function') {
        try {
          return window.HC_T(key);
        } catch (e) {
          /* fall through */
        }
      }
      if (typeof key !== 'string') return '';
      var leaf = key.split('.').pop().replace(/_/g, ' ');
      return leaf.charAt(0).toUpperCase() + leaf.slice(1);
    };
  }

  // ----- link normalization --------------------------------------------------
  // Authored pages link to /patient/<name> (extensionless). Rewrite those to
  // the served static tree: /portal/healthcare/patient/<name>.html. Also map
  // /patient/login -> the portal login hash route.
  function normalizeHref(href) {
    if (!href) return href;
    var m = /^\/patient\/([a-z0-9-]+)\/?$/i.exec(href);
    if (!m) return href;
    var name = m[1];
    if (name === 'login') return LOGIN_URL;
    return PATIENT_BASE + name + '.html';
  }

  function rewriteLinks(root) {
    var anchors = (root || document).querySelectorAll('a[href^="/patient/"]');
    for (var i = 0; i < anchors.length; i++) {
      anchors[i].setAttribute('href', normalizeHref(anchors[i].getAttribute('href')));
    }
  }

  // Intercept programmatic navigation to /patient/* too.
  var _assign = window.location.assign.bind(window.location);
  document.addEventListener('DOMContentLoaded', function () {
    rewriteLinks(document);
    var obs = new MutationObserver(function (muts) {
      muts.forEach(function (mut) {
        for (var i = 0; i < mut.addedNodes.length; i++) {
          var n = mut.addedNodes[i];
          if (n.nodeType === 1) rewriteLinks(n);
        }
      });
    });
    obs.observe(document.body, { childList: true, subtree: true });
  });

  // Expose helpers for pages that want them explicitly.
  window.HC_PATIENT = {
    getToken: getToken,
    logout: function () {
      window.localStorage.removeItem('hc_patient_token');
      window.sessionStorage.removeItem('access_token');
      redirectToLogin();
    },
    normalizeHref: normalizeHref,
    PATIENT_BASE: PATIENT_BASE,
    PORTAL_BASE: PORTAL_BASE,
  };
})();
