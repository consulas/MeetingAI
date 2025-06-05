type RequestOptions = Omit<RequestInit, "method" | "body">;

export async function get<T>(url: string, options?: RequestOptions): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`GET ${url} failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export async function post<T, U = unknown>(
  url: string,
  data: U,
  options?: RequestOptions
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
    ...options,
  });

  if (!response.ok) {
    throw new Error(`POST ${url} failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export async function del<T>(url: string, options?: RequestOptions): Promise<T> {
  const response = await fetch(url, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`DELETE ${url} failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}
