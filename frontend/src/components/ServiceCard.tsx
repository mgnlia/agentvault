'use client'

import { LucideIcon, CheckCircle, Plus, Unlink } from 'lucide-react'

interface ServiceDef {
  id: string
  name: string
  icon: LucideIcon
  color: string
  description: string
}

interface Props {
  service: ServiceDef
  connected: boolean
  connectionData?: any
  onConnect: () => void
  onDisconnect: () => void
}

export function ServiceCard({ service, connected, connectionData, onConnect, onDisconnect }: Props) {
  const { icon: Icon, name, color, description } = service

  return (
    <div className={`card p-5 transition-all duration-200 ${connected ? 'ring-2 ring-green-200' : ''}`}>
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-xl ${color} flex items-center justify-center`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        {connected ? (
          <span className="badge bg-green-100 text-green-700">
            <CheckCircle className="w-3 h-3" /> Connected
          </span>
        ) : (
          <span className="badge bg-gray-100 text-gray-500">Not connected</span>
        )}
      </div>

      <h3 className="font-semibold text-gray-900 mb-1">{name}</h3>
      <p className="text-xs text-gray-500 mb-4">{description}</p>

      {connected && connectionData && (
        <div className="text-xs text-gray-400 mb-3 space-y-0.5">
          {connectionData.scopes?.length > 0 && (
            <p>Scopes: {connectionData.scopes.slice(0, 2).join(', ')}{connectionData.scopes.length > 2 ? '...' : ''}</p>
          )}
          {connectionData.last_used && (
            <p>Last used: {new Date(connectionData.last_used).toLocaleDateString()}</p>
          )}
        </div>
      )}

      {connected ? (
        <button
          onClick={onDisconnect}
          className="w-full flex items-center justify-center gap-1.5 text-xs text-red-500 hover:text-red-600 py-2 rounded-lg border border-red-200 hover:bg-red-50 transition-colors"
        >
          <Unlink className="w-3.5 h-3.5" /> Disconnect
        </button>
      ) : (
        <button
          onClick={onConnect}
          className="w-full flex items-center justify-center gap-1.5 text-xs text-blue-600 font-medium py-2 rounded-lg border border-blue-200 hover:bg-blue-50 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" /> Connect via Auth0
        </button>
      )}
    </div>
  )
}
