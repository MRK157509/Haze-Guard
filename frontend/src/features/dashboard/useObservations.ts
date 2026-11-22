import { useCallback, useEffect, useState } from 'react'
import { getObservations } from '../../api/client'
import type { ObservationFilters, ObservationPage } from '../../types/observation'

const POLL_INTERVAL_MS = 5_000

export function useObservations(filters: ObservationFilters) {
  const [data, setData] = useState<ObservationPage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const loading = data === null && error === null
  const load = useCallback(async () => {
    try {
      const response = await getObservations(filters)
      setData(response)
      setError(null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to load observations.')
    }
  }, [filters])
  // The dashboard remains HTTP-only; polling reveals MQTT-ingested records without a browser refresh.
  useEffect(() => {
    void load()
    const interval = window.setInterval(() => { void load() }, POLL_INTERVAL_MS)
    return () => window.clearInterval(interval)
  }, [load])
  return { data, error, loading, reload: load }
}
