/* WildLens analytics — consent-gated GA4.
   GA4 sets cookies, so it loads ONLY after the visitor accepts.
   Cloudflare Web Analytics (cookieless) can be added separately without consent. */
(function () {
  var GA_ID = 'G-JSB27C2K90';
  var KEY = 'wl_analytics_consent';   // 'granted' | 'denied'

  function loadGA() {
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', GA_ID, { anonymize_ip: true });
  }

  function save(choice) {
    try { localStorage.setItem(KEY, choice); } catch (e) {}
  }

  var consent = null;
  try { consent = localStorage.getItem(KEY); } catch (e) {}

  if (consent === 'granted') { loadGA(); return; }
  if (consent === 'denied') { return; }

  // First visit — show a small, unobtrusive consent bar.
  function showBanner() {
    var bar = document.createElement('div');
    bar.setAttribute('role', 'dialog');
    bar.setAttribute('aria-label', 'Analytics consent');
    bar.style.cssText = [
      'position:fixed', 'left:12px', 'right:12px', 'bottom:12px', 'z-index:100000',
      'max-width:520px', 'margin:0 auto', 'padding:14px 16px',
      'background:#0d2413', 'color:#e6f0e9', 'border:1px solid #2f6b3f',
      'border-radius:12px', 'box-shadow:0 8px 30px rgba(0,0,0,0.45)',
      'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif',
      'font-size:13.5px', 'line-height:1.5',
      'display:flex', 'flex-wrap:wrap', 'gap:10px', 'align-items:center', 'justify-content:space-between'
    ].join(';');

    var text = document.createElement('span');
    text.style.cssText = 'flex:1 1 240px;min-width:200px;';
    text.innerHTML = 'We use privacy-friendly analytics to count visits. ' +
      '<a href="/privacy.html" style="color:#4ade80;text-decoration:underline;">Learn more</a>.';

    var btns = document.createElement('span');
    btns.style.cssText = 'display:flex;gap:8px;flex:0 0 auto;';

    function mkBtn(label, primary) {
      var b = document.createElement('button');
      b.textContent = label;
      b.style.cssText = 'cursor:pointer;border-radius:8px;padding:7px 14px;font-size:13px;font-weight:600;border:1px solid ' +
        (primary ? '#22c55e;background:#16a34a;color:#fff;' : '#2f6b3f;background:transparent;color:#cfe8d6;');
      return b;
    }

    var decline = mkBtn('Decline', false);
    var accept = mkBtn('Accept', true);

    function close() { if (bar.parentNode) bar.parentNode.removeChild(bar); }
    decline.addEventListener('click', function () { save('denied'); close(); });
    accept.addEventListener('click', function () { save('granted'); close(); loadGA(); });

    btns.appendChild(decline);
    btns.appendChild(accept);
    bar.appendChild(text);
    bar.appendChild(btns);
    document.body.appendChild(bar);
  }

  if (document.body) showBanner();
  else document.addEventListener('DOMContentLoaded', showBanner);
})();
