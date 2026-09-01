// Background video autoplay (CSP-safe external script)
(function () {
  function playVideosOnce(ids, delay) {
    const elems = ids.map(id => document.getElementById(id)).filter(Boolean);
    if (!elems.length) return;
    elems.forEach(e => { e.muted = true; e.playsInline = true; e.setAttribute('muted', ''); e.setAttribute('playsinline', ''); });
    setTimeout(() => {
      elems.forEach(e => {
        // Try to play; ignore rejections
        try { e.play(); } catch (err) {}
        e.classList.add('visible');
      });
    }, delay || 2000);
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Site-wide videos
    playVideosOnce(['site-bg-left', 'site-bg-right'], 2000);
    // Page-specific progress videos (if still present)
    playVideosOnce(['bg-video-left', 'bg-video-right'], 2500);
  });
})();
