
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
