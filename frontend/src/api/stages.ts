
const API_BASE_URL = '/api/v1'

export const getDrawPreview = async (stageId: string) => {
  const response = await fetch(`${API_BASE_URL}/stages/${stageId}/draw_preview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  if (!response.ok) {
    throw new Error('Failed to fetch draw preview')
  }
  return response.json()
}

export const saveGroups = async (stageId: string, groupsData: any) => {
  const response = await fetch(`${API_BASE_URL}/stages/${stageId}/groups`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(groupsData)
  })
  if (!response.ok) {
    throw new Error('Failed to save groups')
  }
  return response.json()
}

export const getStages = async (tournamentId: string) => {
    const response = await fetch(`${API_BASE_URL}/stages/?tournament_id=${tournamentId}`)
    if (!response.ok) return []
    return response.json()
}

export const getStageMatchesView = async (stageId: string) => {
  const response = await fetch(`${API_BASE_URL}/stages/${stageId}/matches_view`)
  if (!response.ok) {
    throw new Error('Failed to fetch stage view')
  }
  return response.json()
}

export const submitMatchResult = async (token: string, matchId: string, rankings: any[]) => {
    // rankings: [{player_id: "...", rank: 1}, ...]
    const response = await fetch(`${API_BASE_URL}/matches/${matchId}/result`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            race_number: 1, // Defaulting to 1 race per match for now
            rankings: rankings
        })
    })
    if (!response.ok) {
        throw new Error('Failed to submit result')
    }
    return response.json()
}
