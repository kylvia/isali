// isali-danger-page-to-markdown — X (Twitter) adapter injected via browser-relay /api/eval
//
// Contract: defines window.__isaliExtract() returning Promise<ExtractResult>.
// Pure browser-native APIs only. See ../../references/adapters.md for schema.

window.__isaliExtract = async function __isaliExtract() {
  const warnings = [];
  const url = location.href;
  const adapter = "x";

  function warn(msg) {
    warnings.push(msg);
  }

  function parseTweetIdFromUrl(u) {
    try {
      const parsed = new URL(u);
      const m = parsed.pathname.match(/\/status(?:es)?\/(\d+)/);
      return m ? m[1] : null;
    } catch (e) {
      return null;
    }
  }

  function parseArticleIdFromUrl(u) {
    try {
      const parsed = new URL(u);
      const m = parsed.pathname.match(/\/(?:i\/)?article\/(\d+)/);
      return m ? m[1] : null;
    } catch (e) {
      return null;
    }
  }

  function tweetIdFromArticle(articleEl) {
    // status link inside the article
    const links = articleEl.querySelectorAll('a[href*="/status/"]');
    for (const a of links) {
      const m = a.getAttribute("href").match(/\/status\/(\d+)/);
      if (m) return m[1];
    }
    return null;
  }

  function extractAuthor(articleEl) {
    const userBlock = articleEl.querySelector('[data-testid="User-Name"]');
    if (!userBlock) return null;
    const links = userBlock.querySelectorAll('a[href^="/"]');
    let handle = null;
    let name = null;
    for (const a of links) {
      const href = a.getAttribute("href") || "";
      const m = href.match(/^\/([^\/]+)$/);
      if (m && !handle) {
        handle = m[1];
        // name is usually the first link's first text node
        const txt = a.textContent.trim();
        if (txt && !txt.startsWith("@")) name = txt;
      }
    }
    if (!handle) {
      const span = userBlock.querySelector("span");
      if (span) name = span.textContent.trim();
    }
    const avatarImg = articleEl.querySelector(
      '[data-testid^="UserAvatar-Container"] img, [data-testid="Tweet-User-Avatar"] img'
    );
    const avatarUrl = avatarImg ? avatarImg.src : null;
    return { name: name || handle || "", handle: handle || "", avatarUrl };
  }

  function extractText(articleEl) {
    const node = articleEl.querySelector('[data-testid="tweetText"]');
    if (!node) return { text: "", htmlText: "" };
    // Walk children: <span>, <a>, <img alt=":emoji:">, <br>
    let text = "";
    let html = "";
    for (const child of node.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) {
        text += child.textContent;
        html += child.textContent;
      } else if (child.nodeType === Node.ELEMENT_NODE) {
        const el = child;
        if (el.tagName === "BR") {
          text += "\n";
          html += "<br>";
        } else if (el.tagName === "IMG") {
          const alt = el.getAttribute("alt") || "";
          text += alt;
          html += alt;
        } else if (el.tagName === "A") {
          const href = el.getAttribute("href") || "";
          const inner = el.textContent;
          text += inner;
          html += `<a href="${href}">${inner}</a>`;
        } else {
          text += el.textContent;
          html += el.innerHTML;
        }
      }
    }
    return { text: text.trim(), htmlText: html.trim() };
  }

  function extractMedia(articleEl) {
    const out = [];
    const seen = new Set();

    // Photos
    const photoNodes = articleEl.querySelectorAll('[data-testid="tweetPhoto"] img');
    for (const img of photoNodes) {
      let src = img.src || "";
      // Upgrade to large: replace ?name=small with ?name=large
      src = src.replace(/&?name=(small|medium|360x360|240x240|900x900|thumb)/, "&name=large");
      if (!src) continue;
      if (seen.has(src)) continue;
      seen.add(src);
      out.push({ type: "photo", url: src, alt: img.alt || "" });
    }

    // Videos / GIFs (poster only — best mp4 needs network sniffing, not done in v0)
    const videoNodes = articleEl.querySelectorAll(
      '[data-testid="videoPlayer"] video, [data-testid="videoComponent"] video'
    );
    for (const v of videoNodes) {
      const poster = v.getAttribute("poster") || "";
      const src = v.getAttribute("src") || ""; // usually blob: URL, not directly downloadable
      out.push({
        type: v.getAttribute("aria-label")?.toLowerCase().includes("gif") ? "gif" : "video",
        posterUrl: poster,
        bestUrl: src && !src.startsWith("blob:") ? src : null,
      });
    }
    if (out.some((m) => m.type !== "photo" && !m.bestUrl)) {
      warn("video/gif uses HLS/blob; only poster captured");
    }
    return out;
  }

  function extractQuoted(articleEl) {
    const wrap = articleEl.querySelector('div[role="link"][tabindex="0"][aria-labelledby]');
    if (!wrap) return null;
    const author = extractAuthor(wrap);
    const { text, htmlText } = extractText(wrap);
    const media = extractMedia(wrap);
    const link = wrap.querySelector('a[href*="/status/"]');
    const href = link ? link.getAttribute("href") : null;
    const idMatch = href ? href.match(/\/status\/(\d+)/) : null;
    return {
      id: idMatch ? idMatch[1] : null,
      url: href ? new URL(href, location.origin).toString() : null,
      text,
      htmlText,
      createdAt: null,
      isRoot: false,
      media,
      quotedTweet: null,
      cardLink: null,
      author,
    };
  }

  function extractCardLink(articleEl) {
    const card = articleEl.querySelector('[data-testid="card.wrapper"]');
    if (!card) return null;
    const a = card.querySelector("a[href]");
    if (!a) return null;
    const titleEl = card.querySelector('[data-testid="card.layoutSmall.detail"] span, [data-testid="card.layoutLarge.detail"] span');
    return {
      url: a.getAttribute("href") || "",
      title: titleEl ? titleEl.textContent.trim() : "",
    };
  }

  function extractTimestamp(articleEl) {
    const t = articleEl.querySelector("time[datetime]");
    return t ? t.getAttribute("datetime") : null;
  }

  async function expandShowMoreInside(articleEl) {
    const btn = articleEl.querySelector('[data-testid="tweet-text-show-more-link"]');
    if (btn) {
      btn.click();
      await new Promise((r) => setTimeout(r, 250));
    }
  }

  async function buildTweetNode(articleEl, isRoot) {
    await expandShowMoreInside(articleEl);
    const id = tweetIdFromArticle(articleEl);
    const author = extractAuthor(articleEl);
    const { text, htmlText } = extractText(articleEl);
    const media = extractMedia(articleEl);
    const quoted = extractQuoted(articleEl);
    const cardLink = extractCardLink(articleEl);
    const createdAt = extractTimestamp(articleEl);
    const u = id && author?.handle
      ? `https://x.com/${author.handle}/status/${id}`
      : null;
    return {
      id,
      url: u,
      text,
      htmlText,
      createdAt,
      isRoot,
      media,
      quotedTweet: quoted,
      cardLink,
      author,
    };
  }

  // ---- Article (X long-form) ----
  const articleId = parseArticleIdFromUrl(url);
  if (articleId) {
    const articleBody = document.querySelector('[data-testid="article-body"]');
    if (!articleBody) {
      warn("article id detected but no article-body element found");
      return {
        adapter,
        kind: "unknown",
        tweetId: null,
        url,
        author: null,
        thread: [],
        article: null,
        warnings,
      };
    }
    const titleEl = document.querySelector('[data-testid="article-title"], h1');
    const title = titleEl ? titleEl.textContent.trim() : "";
    const html = articleBody.innerHTML;
    return {
      adapter,
      kind: "article",
      tweetId: null,
      url,
      author: null,
      thread: [],
      article: { title, html },
      warnings,
    };
  }

  // ---- Tweet thread ----
  const rootId = parseTweetIdFromUrl(url);
  if (!rootId) {
    return {
      adapter,
      kind: "unknown",
      tweetId: null,
      url,
      author: null,
      thread: [],
      article: null,
      warnings: [...warnings, "could not parse tweet id from URL"],
    };
  }

  const allArticles = Array.from(document.querySelectorAll('article[data-testid="tweet"]'));
  if (allArticles.length === 0) {
    return {
      adapter,
      kind: "tweet",
      tweetId: rootId,
      url,
      author: null,
      thread: [],
      article: null,
      warnings: [...warnings, "no tweet articles in DOM yet"],
    };
  }

  // Find root by id; fall back to tabindex="-1"
  let rootEl = allArticles.find((el) => tweetIdFromArticle(el) === rootId);
  if (!rootEl) {
    rootEl = allArticles.find((el) => el.getAttribute("tabindex") === "-1") || allArticles[0];
  }
  const rootIdx = allArticles.indexOf(rootEl);
  const rootAuthor = extractAuthor(rootEl);
  const rootHandle = rootAuthor?.handle || null;

  // Build thread: walk before & after root, include consecutive same-author tweets
  const beforeChain = [];
  for (let i = rootIdx - 1; i >= 0; i--) {
    const a = extractAuthor(allArticles[i]);
    if (!rootHandle || !a || a.handle !== rootHandle) break;
    beforeChain.unshift(allArticles[i]);
  }
  const afterChain = [];
  for (let i = rootIdx + 1; i < allArticles.length; i++) {
    const a = extractAuthor(allArticles[i]);
    if (!rootHandle || !a || a.handle !== rootHandle) break;
    afterChain.push(allArticles[i]);
  }

  const ordered = [...beforeChain, rootEl, ...afterChain];
  const thread = [];
  for (const el of ordered) {
    const node = await buildTweetNode(el, el === rootEl);
    thread.push(node);
  }

  // Dedupe by id (DOM occasionally renders the same tweet twice in different sections)
  const seenIds = new Set();
  const dedup = [];
  for (const t of thread) {
    const key = t.id || `idx:${dedup.length}`;
    if (seenIds.has(key)) continue;
    seenIds.add(key);
    dedup.push(t);
  }

  return {
    adapter,
    kind: "tweet",
    tweetId: rootId,
    url,
    author: rootAuthor,
    thread: dedup,
    article: null,
    warnings,
  };
};
