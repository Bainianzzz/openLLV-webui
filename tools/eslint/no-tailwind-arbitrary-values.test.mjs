import { describe, expect, it } from "vitest";
import { arbitraryUtility, tokensFromText } from "./no-tailwind-arbitrary-values.mjs";

describe("no-tailwind-arbitrary-values rule", () => {
  it("detects arbitrary Tailwind utilities in class text", () => {
    expect(tokensFromText("grid min-h-[calc(100dvh-4rem)] lg:w-1/2")).toEqual([
      "min-h-[calc(100dvh-4rem)]",
    ]);
    expect(arbitraryUtility("hover:bg-[color:var(--accent)]")).toBe(true);
  });

  it("does not treat ordinary text as an arbitrary utility", () => {
    expect(tokensFromText("/api/tasks queued plain text")).toEqual([]);
    expect(arbitraryUtility("queued")).toBe(false);
  });

  it("allows arbitrary variants used by shadcn primitives", () => {
    expect(
      tokensFromText(
        "data-[state=checked]:bg-primary [&_svg]:size-4 group-[.active]:text-primary",
      ),
    ).toEqual([]);
  });
});
