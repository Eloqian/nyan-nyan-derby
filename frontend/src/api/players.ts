import axios from 'axios'

const API_BASE = '/api/v1/players'

export interface CreatePlayerPayload {
    in_game_name: string
    qq_id: string
}

export const createPlayer = async (token: string, payload: CreatePlayerPayload) => {
    const res = await axios.post(API_BASE + '/', payload, {
        headers: { Authorization: `Bearer ${token}` }
    })
    return res.data
}
