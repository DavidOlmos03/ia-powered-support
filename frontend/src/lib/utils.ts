/**
 * Utility functions
 */

import { formatDistanceToNow } from 'date-fns'
import type { TicketCategory, TicketSentiment, TicketStats, Ticket } from '@/types/database'

/**
 * Format date to relative time (e.g., "2 minutes ago")
 */
export function formatRelativeTime(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true })
}

/**
 * Get badge color class for category
 */
export function getCategoryColor(category: TicketCategory): string {
  const colors: Record<TicketCategory, string> = {
    'Técnico': 'bg-tecnico text-white',
    'Facturación': 'bg-facturacion text-white',
    'Comercial': 'bg-comercial text-white',
  }
  return colors[category]
}

/**
 * Get badge color class for sentiment
 */
export function getSentimentColor(sentiment: TicketSentiment): string {
  const colors: Record<TicketSentiment, string> = {
    'Positivo': 'bg-success text-white',
    'Neutral': 'bg-gray-500 text-white',
    'Negativo': 'bg-error text-white',
  }
  return colors[sentiment]
}

/**
 * Get emoji for sentiment
 */
export function getSentimentEmoji(sentiment: TicketSentiment): string {
  const emojis: Record<TicketSentiment, string> = {
    'Positivo': '😊',
    'Neutral': '😐',
    'Negativo': '😞',
  }
  return emojis[sentiment]
}

/**
 * Calculate statistics from tickets
 */
export function calculateStats(tickets: Ticket[]): TicketStats {
  const stats: TicketStats = {
    total: tickets.length,
    byCategory: {
      'Técnico': 0,
      'Facturación': 0,
      'Comercial': 0,
    },
    bySentiment: {
      'Positivo': 0,
      'Neutral': 0,
      'Negativo': 0,
    },
    processed: 0,
    unprocessed: 0,
  }

  tickets.forEach((ticket) => {
    if (ticket.processed) {
      stats.processed++
    } else {
      stats.unprocessed++
    }

    if (ticket.category) {
      stats.byCategory[ticket.category]++
    }

    if (ticket.sentiment) {
      stats.bySentiment[ticket.sentiment]++
    }
  })

  return stats
}

/**
 * Truncate text to specified length
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

/**
 * Class name utility (simple version)
 */
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}
