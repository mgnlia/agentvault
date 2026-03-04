'use client'

import { useState } from 'react'
import { Shield, AlertTriangle, CheckCircle, XCircle, Lock } from 'lucide-react'
import { api } from '@/lib/api'

interface Props {
  userId: string
  connections: any[]
}

const SERVICE_ACTIONS: Record<string, { read: string[]; write: string[]; sensitive: string[] }> = {
  github: {
    read: ['list_repos', 'list_issues', 'list_prs', 'read_file', 'search_code'],
    write: ['create_issue'],
    sensitive: ['delete_repo', 'delete_branch', 'merge_pr', 'force_push'],
  },
  google: {
    read: ['list_emails', 'read_email', 'search_emails', 'list_labels'],
    write: [],
    sensitive: ['send_email', 'delete_email'],
  },
  slack: {
    read: ['list_channels', 'read_messages', 'search_messages', 'list_users'],
    write: [],
    sensitive: ['send_message', 'delete_message'],
  },
}

const SERVICE_LABELS: Record<string, string> = {
  github: 'GitHub',
  google: 'Gmail',
  slack: 'Slack',
}

export function PermissionsPanel({ userId, connections }: Props) {
  const [stepUpActions, setStepUpActions] = useState<Record<string, boolean>>({})
  const [deniedActions, setDeniedActions] = useState<Record<string, boolean>>({})

  if (connections.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <Shield className="w-8 h-8 mx-auto mb-3 opacity-50" />
        <p className="text-sm">Connect services to manage permissions.</p>
      </div>
    )
  }

  function isStepUp(service: string, action: string) {
    const key = `${service}:${action}`
    if (key in stepUpActions) return stepUpActions[key]
    return SERVICE_ACTIONS[service]?.sensitive.includes(action) ?? false
  }

  function isDenied(service: string, action: string) {
    return deniedActions[`${service}:${action}`] ?? false
  }

  async function togglePermission(service: string, action: string, enabled: boolean) {
    const key = `${service}:${action}`
    setDeniedActions(prev => ({ ...prev, [key]: !enabled }))
    try {
      await api.put(`/api/permissions/${encodeURIComponent(userId)}/${service}`, {
        user_id: userId, service, permission: action, enabled,
      })
    } catch { /* demo mode */ }
  }

  async function toggleStepUp(service: string, action: string) {
    const key = `${service}:${action}`
    const newVal = !isStepUp(service, action)
    setStepUpActions(prev => ({ ...prev, [key]: newVal }))
    try {
      await api.post(`/api/permissions/${encodeURIComponent(userId)}/${service}/step-up?action=${action}&required=${newVal}`)
    } catch { /* demo mode */ }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-blue-900">Token Vault Security Model</p>
          <p className="text-sm text-blue-700 mt-1">
            OAuth tokens are encrypted at rest in Auth0 Token Vault. The agent retrieves them
            per-request — your credentials are never stored in AgentVault's database.
            Sensitive actions require step-up re-authentication.
          </p>
        </div>
      </div>

      {connections.map(conn => {
        const service = conn.service
        const actions = SERVICE_ACTIONS[service]
        if (!actions) return null

        return (
          <div key={service} className="border border-gray-200 rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 bg-gray-50 border-b border-gray-200">
              <h4 className="font-semibold text-gray-900">{SERVICE_LABELS[service] || service}</h4>
              <span className="badge bg-green-100 text-green-700">
                <CheckCircle className="w-3 h-3" /> Connected
              </span>
            </div>

            <div className="p-5 space-y-4">
              {/* Read actions */}
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Read Actions</p>
                <div className="grid grid-cols-2 gap-2">
                  {actions.read.map(action => (
                    <ActionRow
                      key={action}
                      action={action}
                      enabled={!isDenied(service, action)}
                      stepUp={false}
                      sensitive={false}
                      onToggle={(enabled) => togglePermission(service, action, enabled)}
                      onToggleStepUp={() => {}}
                    />
                  ))}
                </div>
              </div>

              {/* Write actions */}
              {actions.write.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Write Actions</p>
                  <div className="grid grid-cols-2 gap-2">
                    {actions.write.map(action => (
                      <ActionRow
                        key={action}
                        action={action}
                        enabled={!isDenied(service, action)}
                        stepUp={isStepUp(service, action)}
                        sensitive={false}
                        onToggle={(enabled) => togglePermission(service, action, enabled)}
                        onToggleStepUp={() => toggleStepUp(service, action)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Sensitive actions */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <p className="text-xs font-medium text-amber-600 uppercase tracking-wider">Sensitive Actions</p>
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {actions.sensitive.map(action => (
                    <ActionRow
                      key={action}
                      action={action}
                      enabled={!isDenied(service, action)}
                      stepUp={isStepUp(service, action)}
                      sensitive={true}
                      onToggle={(enabled) => togglePermission(service, action, enabled)}
                      onToggleStepUp={() => toggleStepUp(service, action)}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function ActionRow({
  action, enabled, stepUp, sensitive, onToggle, onToggleStepUp
}: {
  action: string; enabled: boolean; stepUp: boolean; sensitive: boolean
  onToggle: (e: boolean) => void; onToggleStepUp: () => void
}) {
  return (
    <div className={`flex items-center justify-between p-2.5 rounded-lg border text-xs ${
      sensitive ? 'border-amber-200 bg-amber-50' : 'border-gray-200 bg-white'
    }`}>
      <div className="flex items-center gap-1.5 min-w-0">
        {sensitive && <Lock className="w-3 h-3 text-amber-500 flex-shrink-0" />}
        <span className="text-gray-700 truncate">{action.replace(/_/g, ' ')}</span>
      </div>
      <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
        {sensitive && (
          <button
            onClick={onToggleStepUp}
            title={stepUp ? 'Step-up required' : 'Step-up not required'}
            className={`text-xs px-1.5 py-0.5 rounded ${stepUp ? 'bg-amber-200 text-amber-700' : 'bg-gray-100 text-gray-400'}`}
          >
            2FA
          </button>
        )}
        <button
          onClick={() => onToggle(!enabled)}
          className={`w-8 h-4 rounded-full transition-colors relative ${enabled ? 'bg-green-500' : 'bg-gray-300'}`}
        >
          <span className={`absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${enabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
        </button>
      </div>
    </div>
  )
}
