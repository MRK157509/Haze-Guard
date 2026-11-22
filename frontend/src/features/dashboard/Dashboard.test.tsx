import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Dashboard } from './Dashboard'

afterEach(() => vi.unstubAllGlobals())

describe('Dashboard states', () => {
  it('shows a loading state while observations are being requested', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    render(<Dashboard />)
    expect(screen.getByText('Loading observations')).toBeInTheDocument()
  })

  it('shows an empty state when the API has no observations', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], limit: 50, offset: 0 }))))
    render(<Dashboard />)
    expect(await screen.findByText('No observations found')).toBeInTheDocument()
  })

  it('shows an API error without fabricating observations', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: { message: 'Service offline' } }), { status: 503 })))
    render(<Dashboard />)
    expect(await screen.findByText('Data unavailable')).toBeInTheDocument()
    expect(screen.getByText('Service offline')).toBeInTheDocument()
  })
})
