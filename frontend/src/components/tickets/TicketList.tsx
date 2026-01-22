/**
 * Ticket list component with real-time updates
 */

import { useState, useCallback, useEffect } from 'react'
import { useTickets } from '@/hooks/useTickets'
import { useRealtimeTickets } from '@/hooks/useRealtimeTickets'
import { TicketCard } from './TicketCard'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import type { Ticket } from '@/types/database'

export function TicketList() {
  const { tickets: initialTickets, loading, error, refetch } = useTickets()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [newTicketIds, setNewTicketIds] = useState<Set<string>>(new Set())

  // Update tickets when initialTickets changes
  useEffect(() => {
    setTickets(initialTickets)
  }, [initialTickets])

  // Handle real-time insert
  const handleInsert = useCallback((ticket: Ticket) => {
    console.log('New ticket inserted:', ticket)

    // Only add if processed (matches our filter)
    if (ticket.processed) {
      setTickets((prev) => [ticket, ...prev])
      setNewTicketIds((prev) => new Set(prev).add(ticket.id))

      // Remove "new" indicator after 3 seconds
      setTimeout(() => {
        setNewTicketIds((prev) => {
          const next = new Set(prev)
          next.delete(ticket.id)
          return next
        })
      }, 3000)
    }
  }, [])

  // Handle real-time update
  const handleUpdate = useCallback((ticket: Ticket) => {
    console.log('Ticket updated:', ticket)

    setTickets((prev) => {
      const index = prev.findIndex((t) => t.id === ticket.id)
      if (index !== -1) {
        // Update existing ticket
        const next = [...prev]
        next[index] = ticket
        return next
      } else if (ticket.processed) {
        // Add newly processed ticket
        return [ticket, ...prev]
      }
      return prev
    })
  }, [])

  // Handle real-time delete
  const handleDelete = useCallback((ticketId: string) => {
    console.log('Ticket deleted:', ticketId)
    setTickets((prev) => prev.filter((t) => t.id !== ticketId))
  }, [])

  // Subscribe to real-time updates
  const { connectionStatus, lastUpdate } = useRealtimeTickets({
    onInsert: handleInsert,
    onUpdate: handleUpdate,
    onDelete: handleDelete,
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-error bg-error/5 p-4">
        <div className="flex items-start">
          <svg
            className="h-5 w-5 text-error mr-3 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div>
            <h3 className="font-semibold text-error">Failed to load tickets</h3>
            <p className="text-sm text-gray-600 mt-1">{error.message}</p>
            <button
              onClick={refetch}
              className="mt-3 text-sm font-medium text-primary hover:text-primary-dark"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (tickets.length === 0) {
    return (
      <EmptyState
        title="No tickets yet"
        description="New tickets will appear here automatically"
        icon={
          <svg
            className="h-12 w-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        }
      />
    )
  }

  return (
    <div className="space-y-4">
      {/* Connection Status */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center gap-2">
          <div
            className={`h-2 w-2 rounded-full ${
              connectionStatus === 'connected'
                ? 'bg-success animate-pulse-subtle'
                : connectionStatus === 'connecting'
                ? 'bg-warning'
                : 'bg-error'
            }`}
          />
          <span>
            {connectionStatus === 'connected' && 'Live updates active'}
            {connectionStatus === 'connecting' && 'Connecting...'}
            {connectionStatus === 'disconnected' && 'Disconnected'}
            {connectionStatus === 'error' && 'Connection error'}
          </span>
        </div>
        {lastUpdate && (
          <span className="text-xs">
            Last update: {formatRelativeTime(lastUpdate)}
          </span>
        )}
      </div>

      {/* Ticket Cards */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {tickets.map((ticket) => (
          <TicketCard
            key={ticket.id}
            ticket={ticket}
            isNew={newTicketIds.has(ticket.id)}
          />
        ))}
      </div>
    </div>
  )
}

function formatRelativeTime(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  return `${hours}h ago`
}
