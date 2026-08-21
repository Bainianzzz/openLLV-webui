export default {
  overrides: [
    {
      files: ["src/**/*.vue"],
      customSyntax: "postcss-html",
    },
  ],
  plugins: ["./tools/stylelint/no-component-style.mjs"],
  rules: {
    "local/no-component-style": true,
  },
};
