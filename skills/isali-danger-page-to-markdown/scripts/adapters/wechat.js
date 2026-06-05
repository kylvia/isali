// isali-danger-page-to-markdown — WeChat (mp.weixin.qq.com) adapter
//
// Contract: defines window.__isaliExtract() returning Promise<ExtractResult>.
// Extracts the public article body. Anti-scraping: WeChat sometimes shows
// a "环境异常" interstitial — we detect it and surface as warning.

window.__isaliExtract = async function __isaliExtract() {
  const warnings = [];
  const url = location.href;
  const adapter = "wechat";

  // Anti-scrape interstitial detection
  const interstitial = document.querySelector(".weui-msg, #js_verify, #js_pc_qr_code");
  if (interstitial) {
    return {
      adapter,
      kind: "unknown",
      url,
      title: null,
      author: null,
      publishedAt: null,
      bodyHtml: "",
      media: [],
      warnings: ["WeChat interstitial detected (verification or rate limit). Open the URL manually first."],
    };
  }

  const titleEl = document.querySelector("#activity-name, h1.rich_media_title");
  const title = titleEl ? titleEl.textContent.trim() : (document.title || "").replace(/_微信.*$/, "").trim();

  const authorEl =
    document.querySelector("#js_name, .rich_media_meta_nickname, .profile_nickname, #profileBt .rich_media_meta_nickname");
  const authorName = authorEl ? authorEl.textContent.trim() : null;

  const profileLink = document.querySelector('a[href*="biz="]');
  const author = authorName
    ? { name: authorName, handle: null, url: profileLink ? profileLink.href : null }
    : null;

  // Published date — WeChat uses #publish_time or em.rich_media_meta_text
  const dateEl = document.querySelector("#publish_time, em#publish_time, em.rich_media_meta_text");
  const publishedAt = dateEl ? dateEl.textContent.trim() : null;

  // Article body
  const bodyEl = document.querySelector("#js_content, .rich_media_content");
  if (!bodyEl) {
    return {
      adapter,
      kind: "unknown",
      url,
      title: title || null,
      author,
      publishedAt,
      bodyHtml: "",
      media: [],
      warnings: [...warnings, "could not locate #js_content; page structure changed?"],
    };
  }

  // Normalize lazy-loaded images: data-src → src
  const bodyClone = bodyEl.cloneNode(true);
  bodyClone.querySelectorAll("img").forEach((img) => {
    const dataSrc = img.getAttribute("data-src");
    if (dataSrc && !img.getAttribute("src")) img.setAttribute("src", dataSrc);
    img.removeAttribute("data-src");
    img.removeAttribute("data-w");
    img.removeAttribute("data-ratio");
    img.removeAttribute("data-type");
  });
  // Drop inline styles (WeChat hardcodes verbose styling)
  bodyClone.querySelectorAll("[style]").forEach((el) => el.removeAttribute("style"));
  // Drop empty sections
  bodyClone.querySelectorAll("section:empty, p:empty").forEach((el) => el.remove());

  // Cover image: og:image or first body img
  let cover = null;
  const og = document.querySelector('meta[property="og:image"]');
  if (og) cover = og.getAttribute("content");
  if (!cover) {
    const firstImg = bodyClone.querySelector("img[src]");
    if (firstImg) cover = firstImg.getAttribute("src");
  }
  const media = cover ? [{ type: "photo", url: cover, alt: "" }] : [];

  return {
    adapter,
    kind: "article",
    url,
    title: title || null,
    author,
    publishedAt,
    bodyHtml: bodyClone.innerHTML,
    media,
    warnings,
  };
};
