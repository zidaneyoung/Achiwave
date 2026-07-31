const API_ENVIRONMENTS = new Set([
  "development",
  "test",
  "production",
]);

function resolvePublicEnvironment(source = process.env) {
  const apiEnvironment = source.EXPO_PUBLIC_API_ENV;
  if (!API_ENVIRONMENTS.has(apiEnvironment)) {
    throw new Error(
      "EXPO_PUBLIC_API_ENV must be development, test, or production.",
    );
  }

  const apiBaseUrl = source.EXPO_PUBLIC_API_BASE_URL?.trim();
  if (!apiBaseUrl) {
    throw new Error("EXPO_PUBLIC_API_BASE_URL is required.");
  }

  let parsedUrl;
  try {
    parsedUrl = new URL(apiBaseUrl);
  } catch {
    throw new Error(
      "EXPO_PUBLIC_API_BASE_URL must be a valid absolute URL.",
    );
  }
  if (parsedUrl.protocol !== "http:" && parsedUrl.protocol !== "https:") {
    throw new Error("EXPO_PUBLIC_API_BASE_URL must use HTTP or HTTPS.");
  }
  if (parsedUrl.username || parsedUrl.password) {
    throw new Error(
      "EXPO_PUBLIC_API_BASE_URL must not contain embedded credentials.",
    );
  }
  if (parsedUrl.search || parsedUrl.hash) {
    throw new Error(
      "EXPO_PUBLIC_API_BASE_URL must not contain a query or fragment.",
    );
  }
  if (
    apiEnvironment === "production" &&
    parsedUrl.protocol !== "https:"
  ) {
    throw new Error(
      "Production EXPO_PUBLIC_API_BASE_URL must use HTTPS.",
    );
  }

  return {
    apiEnvironment,
    apiBaseUrl: apiBaseUrl.replace(/\/+$/, ""),
  };
}

module.exports = {
  resolvePublicEnvironment,
};
