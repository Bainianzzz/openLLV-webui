import tsParser from "@typescript-eslint/parser";
import vueParser from "vue-eslint-parser";
import noTailwindArbitraryValues from "./tools/eslint/no-tailwind-arbitrary-values.mjs";

const localPlugin = {
  rules: {
    "no-tailwind-arbitrary-values": noTailwindArbitraryValues,
  },
};

export default [
  {
    ignores: ["dist/**", "node_modules/**"],
  },
  {
    files: ["src/**/*.ts"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
    plugins: { local: localPlugin },
    rules: {
      "local/no-tailwind-arbitrary-values": "warn",
    },
  },
  {
    files: ["src/**/*.vue"],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        ecmaVersion: "latest",
        parser: tsParser,
        sourceType: "module",
      },
    },
    plugins: { local: localPlugin },
    rules: {
      "local/no-tailwind-arbitrary-values": "warn",
    },
  },
];
