const API_BASE_URL = '/api/v1'

export interface MatchResponse {
  id: string
  name: string
  status: string
  room_number: string | null
  stage_name: string
  group_name: string
  host_player_id: string | null
  is_host: boolean
  opponent_names: string[]
}

export const getMyMatches = async (token: string): Promise<MatchResponse[]> => {
  const response = await fetch(`${API_BASE_URL}/matches/my`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  if (!response.ok) {
    throw new Error('Failed to fetch matches')
  }
  return response.json()
}

export const updateRoomNumber = async (token: string, matchId: string, roomNumber: string) => {
  const response = await fetch(`${API_BASE_URL}/matches/${matchId}/room`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ room_number: roomNumber })
  })
  if (!response.ok) {
    throw new Error('Failed to update room number')
  }
  return response.json()
}
