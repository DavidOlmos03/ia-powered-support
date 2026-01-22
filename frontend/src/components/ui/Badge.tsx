/**
 * Badge component for displaying categories and sentiments
 */

import { cn } from '@/lib/utils'

interface BadgeProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'outline'
}

export function Badge({ children, className, variant = 'default' }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',
        variant === 'default' && 'bg-gray-100 text-gray-800',
        variant === 'outline' && 'border border-gray-300 text-gray-700',
        className
      )}
    >
      {children}
    </span>
  )
}
