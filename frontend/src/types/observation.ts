export type SignalType = 'spoofing' | 'jamming'

export interface Coordinates { lat: number; lon: number }
export interface Observation { id: string; node_id: string; timestamp: string; signal_type: SignalType; confidence: number; coordinates: Coordinates; metadata: Record<string, unknown> }
export interface ObservationPage { items: Observation[]; limit: number; offset: number }
export interface ObservationFilters { node_id?: string; signal_type?: SignalType; start_time?: string; end_time?: string; limit?: number; offset?: number }
