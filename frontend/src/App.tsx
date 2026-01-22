/**
 * Main App component
 */

import { Header } from '@/components/Header'
import { TicketList } from '@/components/tickets/TicketList'
import { useTickets } from '@/hooks/useTickets'

function App() {
  const { tickets } = useTickets()

  return (
    <div className="min-h-screen bg-gray-50">
      <Header tickets={tickets} />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <TicketList />
      </main>

      <footer className="mt-auto border-t border-gray-200 bg-white py-6">
        <div className="mx-auto max-w-7xl px-4 text-center text-sm text-gray-500">
          <p>
            AI-Powered Support Co-Pilot &copy; 2026
          </p>
          <p className="mt-1">
            Built with React, TypeScript, Vite, Tailwind CSS & Supabase
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
