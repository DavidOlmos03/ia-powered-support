/**
 * Supabase database type definitions
 * Generated based on database schema
 */

export type TicketCategory = 'Técnico' | 'Facturación' | 'Comercial'
export type TicketSentiment = 'Positivo' | 'Neutral' | 'Negativo'

export interface Database {
  public: {
    Tables: {
      tickets: {
        Row: {
          id: string
          created_at: string
          updated_at: string
          description: string
          category: TicketCategory | null
          sentiment: TicketSentiment | null
          processed: boolean
          processing_started_at: string | null
          processing_completed_at: string | null
          processing_error: string | null
          retry_count: number
        }
        Insert: {
          id?: string
          description: string
          category?: TicketCategory | null
          sentiment?: TicketSentiment | null
          processed?: boolean
        }
        Update: {
          category?: TicketCategory | null
          sentiment?: TicketSentiment | null
          processed?: boolean
          processing_error?: string | null
        }
      }
    }
  }
}

export type Ticket = Database['public']['Tables']['tickets']['Row']

export interface TicketWithMetadata extends Ticket {
  isNew?: boolean
  isUpdated?: boolean
}

export interface TicketStats {
  total: number
  byCategory: Record<TicketCategory, number>
  bySentiment: Record<TicketSentiment, number>
  processed: number
  unprocessed: number
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'
