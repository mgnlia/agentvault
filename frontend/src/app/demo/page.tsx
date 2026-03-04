'use client'

import { useState } from 'react'
import { Shield, Zap, CheckCircle, ArrowRight, Github, Mail, MessageSquare, Lock } from 'lucide-react'
import Link from 'next/link'

const DEMO_COMMANDS = [
  {
    command: 'Summarize my unread emails and create GitHub issues for action items',
    plan: [
      { step: 1, service: 'google', action: 'list_emails', description: 'Fetch unread emails from Gmail', requires_step_up: false },
      { step: 2, service: 'google', action: 'read_email', description: 'Read email content', requires_step_up: false },
      { step: 3, service: 'github', action: 'create_issue', description: 'Create GitHub issue for each action item', requires_step_up: false },
    ],
    result: '3 emails read, 2 GitHub issues created',
  },
  {
    command: 'List my open PRs and post a summary to #engineering on Slack',
    plan: [
      { step: 1, service: 'github', action: 'list_prs', description: 'Fetch open pull requests', requires_step_up: false },
      { step: 2, service: 'slack', action: 'send_message', description: 'Post PR summary to #engineering', requires_step_up: true },
    ],
    result: '4 PRs found, Slack message sent (required step-up auth)',
  },
  {
    command: 'Delete the test-branch repository',
    plan: [
      { step: 1, service: 'github', action: 'delete_repo', description: 'Delete test-branch repository', requires_step_up: true },
    ],
    result: 'Blocked — step-up authentication required for destructive actions',
  },
]

const SERVICE_ICONS: Record<string, any> = {
  github: Github,
  google: Mail,
  slack: MessageSquare,
}

export default function DemoPage() {
  const [activeDemo, setActiveDemo] = useState(0)
  const [running, setRunning] = useState(false)
  const [phase, setPhase] = useState<'idle' | 'planning' | 'executing' | 'done'>('idle')
  const [currentStep, setCurrentStep] = useState(0)
  const [showStepUp, setShowStepUp] = useState(false)

  const demo = DEMO_COMMANDS[activeDemo]

  async function runDemo() {
    setRunning(true)
    setPhase('planning')
    setCurrentStep(0)
    setShowStepUp(false)

    await sleep(800)
    setPhase('executing')

    for (let i = 0; i < demo.plan.length; i++) {
      setCurrentStep(i)
      await sleep(700)
      if (demo.plan[i].requires_step_up) {
        setShowStepUp(true)
        await sleep(1200)
        setShowStepUp(false)
        await sleep(400)
      }
    }

    setPhase('done')
    setRunning(false)
  }

  function reset() {
    setPhase('idle')
    setCurrentStep(0)
    setShowStepUp(false)
    setRunning(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 text-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-white/10">
        <Link href="/" className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-blue-400" />
          <span className="font-bold">AgentVault</span>
        </Link>
        <Link href="/dashboard" className="btn-primary text-sm">
          Open Dashboard
        </Link>
      </nav>

      <div className="max-w-4xl mx-auto px-8 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Interactive Demo</h1>
          <p className="text-gray-400">See AgentVault execute multi-service commands with Auth0 Token Vault security</p>
        </div>

        {/* Command selector */}
        <div className="space-y-3 mb-8">
          {DEMO_COMMANDS.map((d, i) => (
            <button
              key={i}
              onClick={() => { setActiveDemo(i); reset() }}
              className={`w-full text-left px-5 py-4 rounded-xl border transition-all ${
                activeDemo === i
                  ? 'border-blue-500 bg-blue-500/10 text-white'
                  : 'border-white/10 bg-white/5 text-gray-300 hover:bg-white/10'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-blue-400">Command {i + 1}</span>
                {d.plan.some(s => s.requires_step_up) && (
                  <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full border border-amber-500/30">
                    requires step-up
                  </span>
                )}
              </div>
              <p className="mt-1 text-sm">"{d.command}"</p>
            </button>
          ))}
        </div>

        {/* Execution panel */}
        <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-medium">Execution Trace</span>
            </div>
            <div className="flex gap-2">
              <div className={`w-2 h-2 rounded-full ${phase === 'idle' ? 'bg-gray-500' : phase === 'done' ? 'bg-green-500' : 'bg-blue-500 animate-pulse'}`} />
              <span className="text-xs text-gray-400 capitalize">{phase}</span>
            </div>
          </div>

          <div className="p-6 space-y-3 min-h-48">
            {phase === 'idle' && (
              <div className="text-center py-8 text-gray-500">
                <p className="text-sm">Press Run to execute the demo</p>
              </div>
            )}

            {phase === 'planning' && (
              <div className="flex items-center gap-3 text-sm text-blue-300">
                <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                Parsing intent with Claude AI...
              </div>
            )}

            {(phase === 'executing' || phase === 'done') && demo.plan.map((step, i) => {
              const Icon = SERVICE_ICONS[step.service] || Shield
              const isDone = phase === 'done' || i < currentStep
              const isActive = i === currentStep && phase === 'executing'

              return (
                <div key={i} className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                  isActive ? 'bg-blue-500/10 border border-blue-500/30' :
                  isDone ? 'bg-green-500/5 border border-green-500/20' :
                  'opacity-40 border border-white/5'
                }`}>
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    step.service === 'github' ? 'bg-gray-700' :
                    step.service === 'google' ? 'bg-red-700' : 'bg-purple-700'
                  }`}>
                    <Icon className="w-3.5 h-3.5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-200">{step.description}</p>
                    <p className="text-xs text-gray-500">{step.service} / {step.action}</p>
                  </div>
                  {step.requires_step_up && (
                    <div className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${
                      showStepUp && isActive ? 'bg-amber-500/20 text-amber-400 animate-pulse' : 'bg-amber-500/10 text-amber-500/70'
                    }`}>
                      <Lock className="w-3 h-3" />
                      {showStepUp && isActive ? 'Re-auth required' : 'step-up'}
                    </div>
                  )}
                  {isDone && <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />}
                  {isActive && !showStepUp && <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin flex-shrink-0" />}
                </div>
              )
            })}

            {phase === 'done' && (
              <div className="flex items-center gap-3 mt-4 p-4 bg-green-500/10 border border-green-500/30 rounded-xl">
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                <p className="text-sm text-green-300">{demo.result}</p>
              </div>
            )}
          </div>

          <div className="px-6 pb-6 flex gap-3">
            {phase === 'idle' || phase === 'done' ? (
              <button
                onClick={runDemo}
                disabled={running}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 px-6 rounded-xl transition-colors"
              >
                <Zap className="w-4 h-4" />
                {phase === 'done' ? 'Run Again' : 'Run Demo'}
              </button>
            ) : null}
            {phase !== 'idle' && (
              <button onClick={reset} className="btn-secondary">Reset</button>
            )}
            <Link href="/dashboard" className="flex items-center gap-2 ml-auto text-sm text-blue-400 hover:text-blue-300">
              Try with real services <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

function sleep(ms: number) {
  return new Promise(r => setTimeout(r, ms))
}
