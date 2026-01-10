import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiService } from '../services/api'

interface User {
  id: string
  name: string
  email: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  token: string | null
  login: (credentials: { email: string; password: string }) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      token: null,
      login: async (credentials) => {
        try {
          const { token, user } = await apiService.login(credentials)
          set({
            user,
            isAuthenticated: true,
            token,
          })
        } catch (error) {
          console.error('Login failed:', error)
          throw error
        }
      },
      logout: () => {
        set({
          user: null,
          isAuthenticated: false,
          token: null,
        })
      },
      refreshToken: async () => {
        // TODO: Implement token refresh
        console.log('Token refresh')
      },
    }),
    {
      name: 'ocr-mcp-auth',
      // Don't persist token for security
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)