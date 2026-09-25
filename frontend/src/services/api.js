const API = import.meta.env.VITE_BACKEND_URL || "";

export async function api(path, { method = "GET", body, token, form } = {}) {
  const headers = {};
  if (!form) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, {
    method,
    headers,
    body: form ? form : body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!res.ok) {
    const err = new Error(typeof data?.detail === "string" ? data.detail : JSON.stringify(data?.detail || data || "Request failed"));
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}
