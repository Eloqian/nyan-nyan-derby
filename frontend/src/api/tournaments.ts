const API_BASE_URL = '/api/v1'

export interface Tournament {
  id: string
  name: string
  status: 'setup' | 'active' | 'completed'
  created_at: string
  rules_config: Record<string, any>
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
