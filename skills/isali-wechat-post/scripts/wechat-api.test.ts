import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { expect, test } from "bun:test";

import { assertWechatCoverAspectRatio, loadUploadAsset, readImageDimensions } from "./wechat-api.ts";

test("loadUploadAsset materializes a local cover file when extension mismatches detected format", async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "wechat-api-mime-"));
  const declaredPng = path.join(dir, "cover.png");
  const jpegBytes = Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46, 0x00, 0xff, 0xd9]);
  fs.writeFileSync(declaredPng, jpegBytes);

  const asset = await loadUploadAsset(declaredPng);

  expect(asset.contentType).toBe("image/jpeg");
  expect(asset.fileExt).toBe(".jpg");
  expect(asset.filename).toBe("cover.jpg");
  expect(asset.localPath).toBe(path.join(dir, "cover.jpg"));
  expect(fs.existsSync(asset.localPath!)).toBe(true);
  expect(fs.readFileSync(asset.localPath!)).toEqual(jpegBytes);
});

test("importing wechat-api does not execute the CLI", () => {
  const repo = path.resolve(import.meta.dir, "../../..");
  const result = spawnSync(
    "bun",
    ["-e", "await import('./skills/isali-wechat-post/scripts/wechat-api.ts')"],
    { cwd: repo, encoding: "utf8" },
  );

  expect(result.status).toBe(0);
  expect(result.stdout).toBe("");
  expect(result.stderr).toBe("");
});

test("readImageDimensions reads PNG dimensions", () => {
  const png = Buffer.from([
    0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
    0x00, 0x00, 0x00, 0x0d,
    0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x04, 0x96,
    0x00, 0x00, 0x01, 0xf4,
    0x08, 0x02, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
  ]);

  expect(readImageDimensions(png)).toEqual({ width: 1174, height: 500 });
});

test("assertWechatCoverAspectRatio accepts near 2.35 to 1 covers", () => {
  expect(() => assertWechatCoverAspectRatio({ width: 1174, height: 500 }, "cover.png")).not.toThrow();
});

test("assertWechatCoverAspectRatio rejects square covers", () => {
  expect(() => assertWechatCoverAspectRatio({ width: 1024, height: 1024 }, "cover.png")).toThrow(
    /cover\.png.*1\.00:1.*2\.35:1/,
  );
});
