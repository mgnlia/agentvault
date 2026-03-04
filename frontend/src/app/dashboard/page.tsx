'use client'

import { useState, useEffect } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { Shield, Zap, Settings, LogOut, Github, Mail, MessageSquare, Plus, AlertTriangle } from 'lucide-react'
import { CommandBar } from '@/components/CommandBar'
import { ServiceCard } from '@/components/ServiceCard'
import { ActivityFeed } from '@/components/ActivityFeed'
import { PermissionsPanel } from '@/components/PermissionsPanel'
import { StepUpModal } from '@/components/StepUpModal'
import { api } from '@/lib/api'

type Tab = 'agent' | 'permissions' | 'activity'

interface StepUpState {
  required: boolean
  action: string
  pendingCommand: string
}

export default function DashboardPage() {
  const { user, logout, getAccessTokenSilently, isLoading } = useAuth0()
  const [tab, setTab] = useState<Tab>('agent')
  const [connections, setConnections] = useState<any[]>([])
  const [results, setResults] = useState<any[]>([])
  const [stepUp, setStepUp] = useState<StepUpState>({ required: false, action: '', pendingCommand: '' })
  const [loadingConnections, setLoadingConnections] = useState(true)

  const userId = user?.sub || 'demo-user'

  useEffect(() => {
    loadConnections()
  }, [userId])

  async function loadConnections() {
    setLoadingConnections(true)
    try {
      const data = await api.get(`/api/vault/tokens/${encodeURIComponent(userId)}`)
      setConnections(data.connections || [])
    } catch {
      // Demo mode — show mock connections
      setConnections([])
    } finally {
      setLoadingConnections(false)
    }
  }

  async function handleCommand(command: string, confirmed = false) {
    try {
      const token = await getAccessTokenSilently().catch(() => 'demo-token')
      const result = await api.post('/api/agent/command', {
        command,
        user_id: userId,
        confirm_sensitive: confirmed,
      }, token)

      if (result.requires_step_up) {
        setStepUp({ required: true, action: result.step_up_action, pendingCommand: command })
        return
      }

      setResults(prev => [{
        id: Date.now(),
        command,
        timestamp: new Date().toISOString(),
        status: result.status,
        plan: result.plan,
        results: result.results,
        message: result.message,
      }, ...prev.slice(0, 19)])

      setTab('activity')
    } catch (err: any) {
      setResults(prev => [{
        id: Date.now(),
        command,
        timestamp: new Date().toISOString(),
        status: 'error',
        plan: [],
        results: [],
        message: err.message || 'Command failed',
      }, ...prev.slice(0, 19)])
    }
  }

  async function handleConnectService(service: string) {
    try {
      const token = await getAccessTokenSilently().catch(() => 'demo-token')
      const data = await api.post('/api/auth/connect-service', null, token, {
        service,
        user_id: userId,
      })
      if (data.auth_url) {
        window.location.href = data.auth_url
      }
    } catch {
      // Demo mode: add mock connection
      setConnections(prev => [...prev, {
        service,
        active: true,
        scopes: ['read'],
        connected_at: new Date().toISOString(),
        last_used: null,
      }])
    }
  }

  async function handleDisconnectService(service: string) {
    try {
      const token = await getAccessTokenSilently().catch(() => 'demo-token')
      await api.delete(`/api/vault/tokens/${encodeURIComponent(userId)}/${service}`, token)
      setConnections(prev => prev.filter(c => c.service !== service))
    } catch {
      setConnections(prev => prev.filter(c => c.service !== service))
    }
  }

  const services = [
    { id: 'github', name: 'GitHub', icon: Github, color: 'bg-gray-800', description: 'Repos, issues, PRs' },
    { id: 'google', name: 'Gmail', icon: Mail, color: 'bg-red-600', description: 'Email management' },
    { id: 'slack', name: 'Slack', icon: MessageSquare, color: 'bg-purple-600', description: 'Messaging & channels' },
  ]

  const connectedIds = connections.map(c => c.service)

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Shield className="w-12 h-12 text-blue-600 mx-auto mb-4 animate-pulse" />
          <p className="text-gray-600">Loading AgentVault...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-blue-600" />
            <span className="font-bold text-gray-900">AgentVault</span>
            <span className="badge bg-green-100 text-green-700 ml-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block" /> Live
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">{user?.email || 'Demo User'}</span>
            <button
              onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
              className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
            >
              <LogOut className="w-4 h-4" /> Sign out
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Command Bar */}
        <div className="mb-8">
          <CommandBar onCommand={handleCommand} connectedServices={connectedIds} />
        </div>

        {/* Services Grid */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {services.map(svc => (
            <ServiceCard
              key={svc.id}
              service={svc}
              connected={connectedIds.includes(svc.id)}
              connectionData={connections.find(c => c.service === svc.id)}
              onConnect={() => handleConnectService(svc.id)}
              onDisconnect={() => handleDisconnectService(svc.id)}
            />
          ))}
        </div>

        {/* Tabs */}
        <div className="card">
          <div className="flex border-b border-gray-200">
            {([
              { id: 'agent', label: 'Agent', icon: Zap },
              { id: 'permissions', label: 'Permissions', icon: Settings },
              { id: 'activity', label: 'Activity', icon: Shield },
            ] as const).map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  tab === id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon className="w-4 h-4" /> {label}
              </button>
            ))}
          </div>

          <div className="p-6">
            {tab === 'agent' && (
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900">Quick Commands</h3>
                <div className="grid grid-cols-1 gap-2">
                  {[
                    'Summarize my unread emails and create GitHub issues for action items',
                    'List my open GitHub PRs and post a summary to Slack',
                    'Search emails for invoices from last month',
                    'Find all GitHub issues assigned to me',
                  ].map(cmd => (
                    <button
                      key={cmd}
                      onClick={() => handleCommand(cmd)}
                      className="text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 text-sm text-gray-700 transition-colors"
                    >
                      "{cmd}"
                    </button>
                  ))}
                </div>
                {connectedIds.length === 0 && (
                  <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-lg p-4 mt-4">
                    <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-amber-800">No services connected</p>
                      <p className="text-sm text-amber-600 mt-1">Connect GitHub, Gmail, or Slack above to start executing commands.</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {tab === 'permissions' && (
              <PermissionsPanel userId={userId} connections={connections} />
            )}

            {tab === 'activity' && (
              <ActivityFeed results={results} />
            )}
          </div>
        </div>
      </div>

      {/* Step-up Modal */}
      {stepUp.required && (
        <StepUpModal
          action={stepUp.action}
          onConfirm={() => {
            setStepUp({ required: false, action: '', pendingCommand: '' })
            handleCommand(stepUp.pendingCommand, true)
          }}
          onCancel={() => setStepUp({ required: false, action: '', pendingCommand: '' })}
        />
      )}
    </div>
  )
}
