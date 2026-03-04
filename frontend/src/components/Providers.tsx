'use client'

import { Auth0Provider } from '@auth0/auth0-react'

const domain = process.env.NEXT_PUBLIC_AUTH0_DOMAIN || 'demo.auth0.com'
const clientId = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID || 'demo_client_id'
const redirectUri = typeof window !== 'undefined' ? window.location.origin + '/dashboard' : 'http://localhost:3000/dashboard'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: redirectUri,
        audience: process.env.NEXT_PUBLIC_AUTH0_AUDIENCE || 'https://agentvault-api',
        scope: 'openid profile email offline_access',
      }}
    >
      {children}
    </Auth0Provider>
  )
}
