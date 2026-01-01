import { create } from 'zustand'
import { persist } from 'zustand/middleware'

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
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      token: null,
      login: async (credentials) => {
        // TODO: Implement actual login API call
        console.log('Login attempt:', credentials)

        // Mock login for now
        const mockUser: User = {
          id: '1',
          name: 'Demo User',
          email: credentials.email,
        }

        set({
          user: mockUser,
          isAuthenticated: true,
          token: 'mock-token',
        })
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