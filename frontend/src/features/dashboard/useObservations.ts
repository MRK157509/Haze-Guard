import { useCallback, useEffect, useState } from 'react'
import { getObservations } from '../../api/client'
import type { ObservationFilters, ObservationPage } from '../../types/observation'

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
  // oxlint-disable-next-line react(set-state-in-effect) -- This effect starts the required API synchronization.
  useEffect(() => { void load() }, [load])
  return { data, error, loading, reload: load }
}
