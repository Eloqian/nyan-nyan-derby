import axios from 'axios'

const API_BASE = '/api/v1/players'

export interface CreatePlayerPayload {
    in_game_name: string
    qq_id: string
}

export interface Player {
    id: string
    in_game_name: string
    qq_id: string
    user_id?: string | null
    checked_in?: boolean
    joined_tournament?: boolean
}

export const createPlayer = async (token: string, payload: CreatePlayerPayload, tournamentId?: string) => {
    const params = new URLSearchParams()
    if (tournamentId) params.append('tournament_id', tournamentId)

    const res = await axios.post(API_BASE + '/', payload, {
        headers: { Authorization: `Bearer ${token}` },
        params
    })
    return res.data
}

export const listPlayers = async (token: string, q?: string, tournamentId?: string) => {
    const params = new URLSearchParams()
    if (q) params.append('q', q)
    if (tournamentId) params.append('tournament_id', tournamentId)
    
    const res = await axios.get(API_BASE + '/', {
        headers: { Authorization: `Bearer ${token}` },
        params
    })
    return res.data as Player[]
}

export const updatePlayer = async (token: string, playerId: string, payload: Partial<CreatePlayerPayload>) => {
    const res = await axios.patch(`${API_BASE}/${playerId}`, payload, {
        headers: { Authorization: `Bearer ${token}` }
    })
    return res.data
}

export const deletePlayer = async (token: string, playerId: string) => {
    await axios.delete(`${API_BASE}/${playerId}`, {
        headers: { Authorization: `Bearer ${token}` }
    })
}