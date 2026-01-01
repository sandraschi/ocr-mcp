import React, { useState } from 'react'
import { User, LogOut, LogIn } from 'lucide-react'
import { Button } from '../../ui/Button'
import { useAuthStore } from '../../../stores/authStore'

export function AuthControls() {
  const { user, isAuthenticated, login, logout } = useAuthStore()
  const [showLogin, setShowLogin] = useState(false)
  const [credentials, setCredentials] = useState({ email: '', password: '' })
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      await login(credentials)
      setShowLogin(false)
      setCredentials({ email: '', password: '' })
    } catch (error) {
      console.error('Login failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <>
        <Button size="sm" onClick={() => setShowLogin(true)} className="gap-2">
          <LogIn className="w-4 h-4" />
          Sign In
        </Button>

        {/* Login Modal */}
        {showLogin && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="glass rounded-lg p-6 w-full max-w-md">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold">Sign In</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowLogin(false)}
                  className="w-8 h-8 p-0"
                >
                  ×
                </Button>
              </div>

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Email</label>
                  <input
                    type="email"
                    value={credentials.email}
                    onChange={(e) => setCredentials(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md"
                    placeholder="your@email.com"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Password</label>
                  <input
                    type="password"
                    value={credentials.password}
                    onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md"
                    placeholder="••••••••"
                    required
                  />
                </div>

                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? 'Signing In...' : 'Sign In'}
                </Button>
              </form>

              <div className="mt-4 text-center text-sm text-muted-foreground">
                Demo: Use any email/password to sign in
              </div>
            </div>
          </div>
        )}
      </>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-2 text-sm">
        <User className="w-4 h-4" />
        <span>{user?.name || 'User'}</span>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={logout}
        className="w-9 px-0"
        aria-label="Sign out"
      >
        <LogOut className="w-4 h-4" />
      </Button>
    </div>
  )
}