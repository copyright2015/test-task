async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  })
  const body = response.status === 204 ? '' : await response.text()
  let data = null
  if (body) {
    try {
      data = JSON.parse(body)
    } catch {
      data = body
    }
  }
  if (!response.ok) {
    const detail = typeof data === 'string' ? data : data?.detail
    throw new Error(detail || `HTTP ${response.status}`)
  }
  return data
}

export const api = {
  campaigns: (refresh = false) => request(`/api/campaigns?refresh=${refresh}`),
  catalog: () => request('/api/catalog'),
  createCampaign: (body) => request('/api/campaigns', { method: 'POST', body: JSON.stringify(body) }),
  deleteCampaign: (id) => request(`/api/campaigns/${id}`, { method: 'DELETE' }),
  setCampaignState: (id, action) => request(`/api/campaigns/${id}/${action}`, { method: 'POST' }),
  campaignEditor: (id) => request(`/api/campaigns/${id}/editor`),
  updateCampaignEditor: (id, streams) =>
    request(`/api/campaigns/${id}/editor`, { method: 'PUT', body: JSON.stringify({ streams }) }),
}
