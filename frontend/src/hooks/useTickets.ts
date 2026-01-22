/**
 * Hook for fetching tickets from Supabase
 */

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import type { Ticket } from '@/types/database'

interface UseTicketsResult {
  tickets: Ticket[]
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

export function useTickets(): UseTicketsResult {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchTickets = async () => {
    try {
      setLoading(true)
      setError(null)

      const { data, error: fetchError } = await supabase
        .from('tickets')
        .select('*')
        .eq('processed', true)
        .order('created_at', { ascending: false })
        .limit(100)

      if (fetchError) throw fetchError

      setTickets(data || [])
    } catch (err) {
      console.error('Error fetching tickets:', err)
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTickets()
  }, [])

  return {
    tickets,
    loading,
    error,
    refetch: fetchTickets,
  }
}
