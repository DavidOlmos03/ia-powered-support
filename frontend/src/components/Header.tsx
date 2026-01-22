/**
 * Header component
 */

import { calculateStats } from '@/lib/utils'
import type { Ticket } from '@/types/database'

interface HeaderProps {
  tickets: Ticket[]
}

export function Header({ tickets }: HeaderProps) {
  const stats = calculateStats(tickets)

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              🤖 AI Support Co-Pilot
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Real-time ticket classification dashboard
            </p>
          </div>

          <div className="hidden md:flex items-center gap-6">
            <StatItem label="Total" value={stats.total} />
            <StatItem label="Processed" value={stats.processed} color="success" />
            <StatItem label="Pending" value={stats.unprocessed} color="warning" />
          </div>
        </div>

        {/* Mobile Stats */}
        <div className="mt-4 flex gap-4 md:hidden">
          <StatItem label="Total" value={stats.total} />
          <StatItem label="Processed" value={stats.processed} color="success" />
          <StatItem label="Pending" value={stats.unprocessed} color="warning" />
        </div>

        {/* Category & Sentiment Stats */}
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <MiniStat
            label="Técnico"
            value={stats.byCategory['Técnico']}
            color="bg-tecnico"
          />
          <MiniStat
            label="Facturación"
            value={stats.byCategory['Facturación']}
            color="bg-facturacion"
          />
          <MiniStat
            label="Comercial"
            value={stats.byCategory['Comercial']}
            color="bg-comercial"
          />
          <MiniStat
            label="Positivo"
            value={stats.bySentiment['Positivo']}
            color="bg-success"
          />
          <MiniStat
            label="Neutral"
            value={stats.bySentiment['Neutral']}
            color="bg-gray-500"
          />
          <MiniStat
            label="Negativo"
            value={stats.bySentiment['Negativo']}
            color="bg-error"
          />
        </div>
      </div>
    </header>
  )
}

function StatItem({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color?: string
}) {
  const colorClass =
    color === 'success'
      ? 'text-success'
      : color === 'warning'
      ? 'text-warning'
      : 'text-gray-900'

  return (
    <div className="text-center">
      <div className={`text-2xl font-bold ${colorClass}`}>{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  )
}

function MiniStat({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color: string
}) {
  return (
    <div className="rounded-lg bg-gray-50 p-3 text-center">
      <div className={`mx-auto mb-1 h-2 w-12 rounded-full ${color}`} />
      <div className="text-lg font-semibold text-gray-900">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  )
}
