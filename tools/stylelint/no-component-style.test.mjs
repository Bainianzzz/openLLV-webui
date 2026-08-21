import { describe, expect, it } from "vitest";
import { firstStyleNode, isComponentVueFile } from "./no-component-style.mjs";

describe("no-component-style rule", () => {
  it("only targets component and page Vue files", () => {
    expect(isComponentVueFile("/repo/src/components/Button.vue")).toBe(true);
    expect(isComponentVueFile("/repo/src/pages/Home.vue")).toBe(true);
    expect(isComponentVueFile("/repo/src/styles/app.css")).toBe(false);
  });

  it("returns one report node for a style block", () => {
    const declaration = { type: "decl" };
    expect(firstStyleNode({ nodes: [{ type: "comment" }, declaration] })).toBe(declaration);
    expect(firstStyleNode({ nodes: [{ type: "comment" }] })).toBeUndefined();
  });
});
