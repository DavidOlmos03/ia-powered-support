/**
 * Individual ticket card component
 */

import { Badge } from '@/components/ui/Badge'
import { getCategoryColor, getSentimentColor, getSentimentEmoji, formatRelativeTime, truncateText } from '@/lib/utils'
import type { Ticket } from '@/types/database'

interface TicketCardProps {
  ticket: Ticket
  isNew?: boolean
}

export function TicketCard({ ticket, isNew }: TicketCardProps) {
  return (
    <div
      className={`rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-all hover:shadow-md ${
        isNew ? 'animate-slide-in' : ''
      }`}
    >
      {/* Header */}
      <div className="mb-3 flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-gray-500">
              #{ticket.id.substring(0, 8)}
            </span>
            {isNew && (
              <span className="text-xs font-semibold text-primary">NEW</span>
            )}
          </div>
        </div>
        {ticket.processed && (
          <div className="flex items-center gap-1 text-xs text-success">
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span>Processed</span>
          </div>
        )}
      </div>

      {/* Description */}
      <p className="mb-3 text-sm text-gray-700 leading-relaxed">
        {truncateText(ticket.description, 150)}
      </p>

      {/* Badges */}
      <div className="mb-3 flex flex-wrap gap-2">
        {ticket.category && (
          <Badge className={getCategoryColor(ticket.category)}>
            {ticket.category}
          </Badge>
        )}
        {ticket.sentiment && (
          <Badge className={getSentimentColor(ticket.sentiment)}>
            <span className="mr-1">{getSentimentEmoji(ticket.sentiment)}</span>
            {ticket.sentiment}
          </Badge>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{formatRelativeTime(ticket.created_at)}</span>
        {ticket.processing_completed_at && (
          <span>
            Processed in{' '}
            {Math.round(
              (new Date(ticket.processing_completed_at).getTime() -
                new Date(ticket.processing_started_at || ticket.created_at).getTime()) /
                1000
            )}
            s
          </span>
        )}
      </div>
    </div>
  )
}
