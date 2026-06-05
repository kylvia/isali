// isali-danger-page-to-markdown — generic adapter (Readability-lite)
//
// Contract: defines window.__isaliExtract() returning Promise<ExtractResult>.
// Strategy:
//   1. Drop noise (script/style/nav/header/footer/aside/form/iframe).
//   2. Pick best candidate: <article role=main> > [itemprop=articleBody] > <article> > <main> > densest <p>-container.
//   3. Lift its innerHTML, lift OG meta as title/author/published.

window.__isaliExtract = async function __isaliExtract() {
  const warnings = [];
  const url = location.href;
  const adapter = "generic";

  function meta(name) {
    const el = document.querySelector(
      `meta[property="${name}"], meta[name="${name}"]`
    );
    return el ? (el.getAttribute("content") || "").trim() : null;
  }

  const title =
    meta("og:title") ||
    (document.querySelector("h1") ? document.querySelector("h1").textContent.trim() : null) ||
    (document.title || "").trim() ||
    null;

  const authorName =
    meta("article:author") ||
    meta("author") ||
    (document.querySelector('[rel="author"]')?.textContent.trim() || null);
  const author = authorName ? { name: authorName, handle: null, url: null } : null;

  const publishedAt =
    meta("article:published_time") ||
    meta("og:article:published_time") ||
    (document.querySelector("time[datetime]")?.getAttribute("datetime") || null);

  // Pick body candidate
  function score(el) {
    const ps = el.querySelectorAll("p");
    let textLen = 0;
    ps.forEach((p) => (textLen += (p.textContent || "").trim().length));
    return textLen + ps.length * 50;
  }

  const candidates = [];
  function add(el) {
    if (el && !candidates.includes(el)) candidates.push(el);
  }
  document.querySelectorAll('[itemprop="articleBody"]').forEach(add);
  document.querySelectorAll('article[role="main"], main article, article').forEach(add);
  document.querySelectorAll("main").forEach(add);
  add(document.body);

  let best = null;
  let bestScore = -1;
  for (const c of candidates) {
    const s = score(c);
    if (s > bestScore) {
      best = c;
      bestScore = s;
    }
  }
  if (!best) {
    return {
      adapter,
      kind: "unknown",
      url,
      title,
      author,
      publishedAt,
      bodyHtml: "",
      media: [],
      warnings: [...warnings, "no body candidate found"],
    };
  }

  // Clone & sanitize
  const clone = best.cloneNode(true);
  clone
    .querySelectorAll(
      "script, style, noscript, iframe, form, nav, aside, header, footer, button, .ad, .advertisement, [aria-hidden='true']"
    )
    .forEach((el) => el.remove());
  // Strip inline event handlers / styles
  clone.querySelectorAll("*").forEach((el) => {
    for (const attr of Array.from(el.attributes)) {
      if (
        attr.name.startsWith("on") ||
        attr.name === "style" ||
        attr.name === "class" ||
        attr.name.startsWith("data-")
      ) {
        el.removeAttribute(attr.name);
      }
    }
  });
  // Lazy-load image src
  clone.querySelectorAll("img").forEach((img) => {
    const lazy =
      img.getAttribute("data-src") ||
      img.getAttribute("data-original") ||
      img.getAttribute("data-lazy-src");
    if (lazy && !img.getAttribute("src")) img.setAttribute("src", lazy);
  });

  // Resolve relative URLs in <a> and <img> against location.origin
  const base = location.origin;
  clone.querySelectorAll("a[href]").forEach((a) => {
    const h = a.getAttribute("href");
    if (h && !/^(https?:|mailto:|tel:|#)/i.test(h)) {
      try {
        a.setAttribute("href", new URL(h, location.href).toString());
      } catch (e) {}
    }
  });
  clone.querySelectorAll("img[src]").forEach((img) => {
    const s = img.getAttribute("src");
    if (s && !/^(https?:|data:)/i.test(s)) {
      try {
        img.setAttribute("src", new URL(s, location.href).toString());
      } catch (e) {}
    }
  });

  // Cover
  let cover = meta("og:image") || meta("twitter:image");
  if (!cover) {
    const firstImg = clone.querySelector("img[src]");
    if (firstImg) cover = firstImg.getAttribute("src");
  }
  const media = cover ? [{ type: "photo", url: cover, alt: "" }] : [];

  return {
    adapter,
    kind: "article",
    url,
    title,
    author,
    publishedAt,
    bodyHtml: clone.innerHTML,
    media,
    warnings,
  };
};
