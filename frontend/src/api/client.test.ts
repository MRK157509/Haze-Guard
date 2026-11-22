import { describe, expect, it, vi } from 'vitest'
import { getObservations } from './client'

describe('getObservations', () => {
  it('uses the documented observation endpoint and query fields', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], limit: 50, offset: 0 }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    await expect(getObservations({ node_id: 'node-01', signal_type: 'spoofing', limit: 50 })).resolves.toMatchObject({ items: [] })
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/observations?node_id=node-01&signal_type=spoofing&limit=50', expect.any(Object))
  })
})
