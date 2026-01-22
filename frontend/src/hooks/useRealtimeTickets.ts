/**
 * Hook for real-time ticket updates via Supabase channels
 */

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import type { Ticket, ConnectionStatus } from '@/types/database'
import type { RealtimeChannel } from '@supabase/supabase-js'

interface UseRealtimeTicketsOptions {
  onInsert?: (ticket: Ticket) => void
  onUpdate?: (ticket: Ticket) => void
  onDelete?: (ticketId: string) => void
}

interface UseRealtimeTicketsResult {
  connectionStatus: ConnectionStatus
  lastUpdate: Date | null
}

export function useRealtimeTickets({
  onInsert,
  onUpdate,
  onDelete,
}: UseRealtimeTicketsOptions): UseRealtimeTicketsResult {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting')
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  useEffect(() => {
    setConnectionStatus('connecting')

    const channel: RealtimeChannel = supabase
      .channel('tickets-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'tickets',
        },
        (payload) => {
          console.log('Real-time event:', payload)
          setLastUpdate(new Date())

          if (payload.eventType === 'INSERT' && onInsert) {
            onInsert(payload.new as Ticket)
          } else if (payload.eventType === 'UPDATE' && onUpdate) {
            onUpdate(payload.new as Ticket)
          } else if (payload.eventType === 'DELETE' && onDelete) {
            onDelete((payload.old as Ticket).id)
          }
        }
      )
      .subscribe((status) => {
        console.log('Subscription status:', status)

        if (status === 'SUBSCRIBED') {
          setConnectionStatus('connected')
        } else if (status === 'CHANNEL_ERROR') {
          setConnectionStatus('error')
        } else if (status === 'TIMED_OUT') {
          setConnectionStatus('disconnected')
        }
      })

    // Cleanup subscription on unmount
    return () => {
      console.log('Unsubscribing from tickets channel')
      supabase.removeChannel(channel)
    }
  }, [onInsert, onUpdate, onDelete])

  return {
    connectionStatus,
    lastUpdate,
  }
}
