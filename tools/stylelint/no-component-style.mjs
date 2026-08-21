import stylelint from "stylelint";

const ruleName = "local/no-component-style";
const messages = stylelint.utils.ruleMessages(ruleName, {
  rejected: "Prefer Tailwind utility classes over custom component CSS.",
});

export function isComponentVueFile(filePath) {
  return /[\\/]src[\\/](components|pages)[\\/].+\.vue$/.test(filePath);
}

export function firstStyleNode(root) {
  return root.nodes?.find((node) => node.type !== "comment");
}

const rule = (primaryOption) => {
  return (root, result) => {
    const node = firstStyleNode(root);
    if (
      !primaryOption ||
      !isComponentVueFile(root.source.input.file ?? "") ||
      !node
    ) {
      return;
    }

    stylelint.utils.report({
      message: messages.rejected,
      node,
      result,
      ruleName,
    });
  };
};

rule.ruleName = ruleName;
rule.messages = messages;

export default stylelint.createPlugin(ruleName, rule);
