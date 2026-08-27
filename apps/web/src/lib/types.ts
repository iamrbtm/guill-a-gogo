export interface Trip {
  id: string;
  title: string;
  origin?: string | null;
  destination?: string | null;
  status: string;
  applied_delay_minutes?: number;
}

export interface Profile {
  id: string;
  name: string;
  [key: string]: unknown;
}

export interface Stop {
  id: string;
  name: string | null;
  address: string | null;
  required: boolean;
  completed: boolean;
  stop_type: string;
  order_index: number;
  min_duration_minutes: number | null;
  notes: string | null;
}

export interface Today {
  trip_id: string;
  trip_title: string;
  day_number: number;
  next_stop: { id: string; name: string; required: boolean } | null;
  remaining_count: number;
  completed_count: number;
  actions: Record<string, boolean>;
  eta_note: string;
}
