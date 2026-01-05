const API_BASE_URL = '/api/v1'

export interface Tournament {
  id: string
  name: string
  status: 'setup' | 'active' | 'completed'
  created_at: string
  start_time?: string
  rules_config: Record<string, any>
  prize_pool_config?: Record<string, any>
  rules_content?: string
}

export interface TournamentParticipant {
  tournament_id: string
  player_id: string
  checked_in: boolean
  checked_in_at?: string
  player: {
    in_game_name: string
    qq_id?: string
  }
}

export const createTournament = async (token: string, data: any) => {
  const response = await fetch(`${API_BASE_URL}/tournaments/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to create tournament')
  return response.json()
}

export const listTournaments = async (): Promise<Tournament[]> => {
  const response = await fetch(`${API_BASE_URL}/tournaments/`)
  if (!response.ok) return []
  return response.json()
}

export const getCurrentTournament = async (): Promise<Tournament | null> => {
  const response = await fetch(`${API_BASE_URL}/tournaments/current`)
  if (!response.ok) return null
  const data = await response.json()
  return data || null
}

export const updateTournament = async (token: string, id: string, data: any) => {
  const response = await fetch(`${API_BASE_URL}/tournaments/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to update tournament')
  return response.json()
}

export const checkInTournament = async (token: string, tournamentId: string) => {
  const response = await fetch(`${API_BASE_URL}/tournaments/${tournamentId}/checkin`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  if (!response.ok) {
     const err = await response.json()
     throw new Error(err.detail || 'Check-in failed')
  }
  return response.json()
}

export const getTournamentParticipants = async (tournamentId: string): Promise<TournamentParticipant[]> => {
  const response = await fetch(`${API_BASE_URL}/tournaments/${tournamentId}/participants`)
  if (!response.ok) return []
  return response.json()
}

export const removeParticipant = async (token: string, tournamentId: string, playerId: string) => {
  const response = await fetch(`${API_BASE_URL}/tournaments/${tournamentId}/participants/${playerId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  if (!response.ok) throw new Error('Failed to remove participant')
}
