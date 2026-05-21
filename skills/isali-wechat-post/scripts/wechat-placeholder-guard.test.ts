import { expect, test } from "bun:test";

import { assertNoUnresolvedImagePlaceholders } from "./wechat-placeholder-guard.ts";

test("throws when unresolved WeChat image placeholders remain in final HTML", () => {
  const html = '<p>body</p><img src="https://mmbiz.qpic.cn/ok.jpg">WECHATIMGPH_6';

  expect(() => assertNoUnresolvedImagePlaceholders(html)).toThrow(
    /Unresolved WeChat image placeholders remain: WECHATIMGPH_6/,
  );
});

test("ignores similar text that is not a full placeholder token", () => {
  const html = "<p>WECHATIMGPH_6_extra is ordinary text</p>";

  expect(() => assertNoUnresolvedImagePlaceholders(html)).not.toThrow();
});
