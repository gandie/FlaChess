export class ApiError extends Error {
  constructor(message, { status = 0, kind = "unavailable", detail = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.kind = kind;
    this.detail = detail;
  }
}

function messageForStatus(status) {
  if (status === 404) {
    return "The requested resource was not found.";
  }
  if (status === 409) {
    return "The request conflicts with the current server state.";
  }
  if (status === 422) {
    return "The request contains invalid or incomplete data.";
  }
  if (status >= 500) {
    return "The server could not complete the request.";
  }
  return "The server rejected the request.";
}

async function readJson(response) {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.toLowerCase().includes("application/json")) {
    throw new ApiError("The server returned an unexpected response.", {
      status: response.status,
      kind: "unexpected-response",
    });
  }

  return response.json();
}

export async function apiRequest(
  path,
  { method = "GET", body, headers = {}, signal } = {},
) {
  const requestHeaders = new Headers(headers);
  const options = { method, headers: requestHeaders, signal };

  if (body !== undefined) {
    requestHeaders.set("content-type", "application/json");
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(path, options);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError("The application server is unavailable.", {
      kind: "network",
      detail: error,
    });
  }

  if (!response.ok) {
    let payload = null;
    try {
      payload = await readJson(response);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
    }

    const detail = payload?.detail ?? null;
    throw new ApiError(messageForStatus(response.status), {
      status: response.status,
      kind: response.status === 422 ? "validation" : "http",
      detail,
    });
  }

  if (response.status === 204) {
    return null;
  }
  return readJson(response);
}

export const api = {
  get: (path, options = {}) => apiRequest(path, options),
  post: (path, body, options = {}) =>
    apiRequest(path, { ...options, method: "POST", body }),
  put: (path, body, options = {}) =>
    apiRequest(path, { ...options, method: "PUT", body }),
  delete: (path, options = {}) =>
    apiRequest(path, { ...options, method: "DELETE" }),
};
