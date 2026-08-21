const ruleName = "local/no-tailwind-arbitrary-values";
const message = "Prefer a Tailwind preset utility over this arbitrary value.";

export function arbitraryUtility(token) {
  return token.startsWith("[") || /-\[[^\]]+\]/.test(token);
}

export function tokensFromText(text) {
  return text.match(/[^\s"'`]+/g)?.filter(arbitraryUtility) ?? [];
}

function isClassAttribute(node) {
  if (!node.directive) {
    return node.key.name === "class";
  }

  return (
    node.key.name.name === "bind" &&
    node.key.argument?.type === "VIdentifier" &&
    node.key.argument.name === "class"
  );
}

function create(context) {
  function inspect(text, node) {
    for (const token of tokensFromText(text)) {
      context.report({
        node,
        message: `${message} Found \`${token}\`.`,
      });
    }
  }

  const templateVisitor = {
    VAttribute(node) {
      if (!isClassAttribute(node) || !node.value) {
        return;
      }

      const value = node.value.expression
        ? context.sourceCode.getText(node.value.expression)
        : node.value.value;
      inspect(value, node);
    },
  };

  const templateBodyVisitor =
    context.sourceCode.parserServices.defineTemplateBodyVisitor?.(
      templateVisitor,
      {},
    ) ?? {};

  return templateBodyVisitor;
}

export default {
  meta: {
    type: "suggestion",
    docs: {
      description: "Prefer Tailwind preset utilities over arbitrary values",
    },
    schema: [],
  },
  create,
  name: ruleName,
};
