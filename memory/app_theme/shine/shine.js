/* JEELIVE.AI - Shine for the web. Measures every .jl-shine once (and again when its size changes):
   the size of the turning edge, the slope of the face colours and the path of the glint.
   It also rests a piece while it is off screen. No library needed. */
(function () {
  function px(n) { return Math.round(n * 100) / 100 + "px"; }
  function size(el) {
    var ring = el.querySelector(":scope > .jl-ring");
    if (!ring) return;
    var w = ring.offsetWidth, h = ring.offsetHeight;
    if (!w || !h) return;
    var cs = getComputedStyle(el), s = el.style;
    var edge = parseFloat(cs.getPropertyValue("--ring")) || 0, band = parseFloat(cs.getPropertyValue("--band")) || 0;
    var fw = w - edge * 2, fh = h - edge * 2, slope = Math.atan2(fh, fw) * 180 / Math.PI;
    s.setProperty("--d", Math.ceil(Math.hypot(w, h)) + 4 + "px");          /* the turning square = the diagonal + 4 */
    s.setProperty("--ta", (90 + slope).toFixed(2) + "deg");                 /* face colours run exactly corner to corner */
    if (el.hasAttribute("data-corner")) {                                   /* glint: corner to corner */
      var diagonal = Math.hypot(fw, fh), reach = diagonal / 2 + band;
      var x = fw / diagonal * reach, y = fh / diagonal * reach;
      s.setProperty("--gx0", px(-x)); s.setProperty("--gy0", px(-y));
      s.setProperty("--gx1", px(x));  s.setProperty("--gy1", px(y));
      s.setProperty("--ga", slope.toFixed(2) + "deg");
      s.setProperty("--gl", Math.ceil(diagonal) + 40 + "px");
    } else {                                                                /* glint: tilted band, left to right */
      var off = Math.ceil((band + (h + 60) * 0.18) / 10) * 10, to = Math.ceil((w + off) / 60) * 60;
      s.setProperty("--gx0", -off + "px"); s.setProperty("--gx1", to + "px");
      s.setProperty("--gy0", "0px"); s.setProperty("--gy1", "0px"); s.setProperty("--ga", "20deg");
    }
    el.setAttribute("data-ready", "");
  }
  var resized = "ResizeObserver" in window ? new ResizeObserver(function (list) {
    list.forEach(function (e) { size(e.target); });
  }) : null;
  var seen = "IntersectionObserver" in window ? new IntersectionObserver(function (list) {
    list.forEach(function (e) { e.target.toggleAttribute("data-off", !e.isIntersecting); });
  }, { rootMargin: "80px" }) : null;
  /* Call JLShine.watch() again after you add new pieces to the page (for example after a list loads). */
  function watch(root) {
    (root || document).querySelectorAll(".jl-shine").forEach(function (el) {
      if (el.jlShine) return;
      el.jlShine = true;
      size(el);
      if (resized) resized.observe(el);
      if (seen) seen.observe(el);
    });
  }
  window.JLShine = { watch: watch, size: size };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { watch(); });
  else watch();
})();
