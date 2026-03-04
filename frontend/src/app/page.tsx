'use client'

import { useAuth0 } from '@auth0/auth0-react'
import { Shield, Zap, Lock, Eye, Github, Mail, MessageSquare, ArrowRight, CheckCircle } from 'lucide-react'
import Link from 'next/link'

export default function HomePage() {
  const { loginWithRedirect, isAuthenticated, isLoading } = useAuth0()

  if (isAuthenticated) {
    if (typeof window !== 'undefined') window.location.href = '/dashboard'
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 text-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-white/10">
        <div className="flex items-center gap-2">
          <Shield className="w-7 h-7 text-blue-400" />
          <span className="text-xl font-bold">AgentVault</span>
        </div>
        <div className="flex items-center gap-4">
          <a href="https://github.com/mgnlia/agentvault" target="_blank" rel="noopener noreferrer"
            className="text-sm text-gray-300 hover:text-white transition-colors flex items-center gap-1">
            <Github className="w-4 h-4" /> GitHub
          </a>
          <button
            onClick={() => loginWithRedirect()}
            disabled={isLoading}
            className="btn-primary text-sm"
          >
            Sign In
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-8 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 text-sm text-blue-300 mb-8">
          <Lock className="w-3.5 h-3.5" />
          Powered by Auth0 Token Vault
        </div>
        <h1 className="text-5xl md:text-6xl font-bold leading-tight mb-6">
          Your AI agent,{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
            secured by Auth0
          </span>
        </h1>
        <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-10">
          AgentVault executes tasks across GitHub, Gmail, and Slack using natural language —
          with granular permissions, step-up auth for sensitive actions, and zero credential exposure.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <button
            onClick={() => loginWithRedirect()}
            disabled={isLoading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-8 rounded-xl transition-all duration-200 text-lg shadow-lg shadow-blue-500/25"
          >
            Get Started Free <ArrowRight className="w-5 h-5" />
          </button>
          <Link href="/demo"
            className="flex items-center gap-2 bg-white/10 hover:bg-white/15 text-white font-semibold py-3 px-8 rounded-xl transition-all duration-200 text-lg border border-white/20">
            <Zap className="w-5 h-5" /> Try Demo
          </Link>
        </div>
      </section>

      {/* Services */}
      <section className="max-w-5xl mx-auto px-8 py-12">
        <p className="text-center text-gray-400 text-sm mb-8 uppercase tracking-wider">Integrates with your tools</p>
        <div className="grid grid-cols-3 gap-4">
          {[
            { icon: Github, name: 'GitHub', desc: 'Repos, issues, PRs, code search', color: 'from-gray-700 to-gray-600' },
            { icon: Mail, name: 'Gmail', desc: 'Read, search, send emails', color: 'from-red-700 to-red-600' },
            { icon: MessageSquare, name: 'Slack', desc: 'Channels, messages, notifications', color: 'from-purple-700 to-purple-600' },
          ].map(({ icon: Icon, name, desc, color }) => (
            <div key={name} className="bg-white/5 border border-white/10 rounded-2xl p-6 text-center hover:bg-white/10 transition-colors">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mx-auto mb-4`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-semibold mb-1">{name}</h3>
              <p className="text-sm text-gray-400">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-8 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">Security-first by design</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            {
              icon: Lock,
              title: 'Auth0 Token Vault',
              desc: 'OAuth tokens stored encrypted at rest in Auth0. Your credentials never touch our servers — retrieved securely per-request via Token Vault.',
            },
            {
              icon: Shield,
              title: 'Step-up Authentication',
              desc: 'Sensitive actions (delete repo, send email) require re-authentication. You stay in control of every consequential action.',
            },
            {
              icon: Eye,
              title: 'Permission Dashboard',
              desc: 'See exactly what the agent can access. Toggle permissions per-service, per-action. Revoke access instantly.',
            },
            {
              icon: Zap,
              title: 'Natural Language Commands',
              desc: 'Just describe what you want. Claude AI parses intent, plans steps, and executes across services — streaming results in real-time.',
            },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="bg-white/5 border border-white/10 rounded-2xl p-6 flex gap-4">
              <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                <Icon className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold mb-2">{title}</h3>
                <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Example commands */}
      <section className="max-w-5xl mx-auto px-8 py-12">
        <h2 className="text-3xl font-bold text-center mb-4">What can AgentVault do?</h2>
        <p className="text-center text-gray-400 mb-10">Just type what you need</p>
        <div className="space-y-3">
          {[
            'Summarize my unread emails and create GitHub issues for action items',
            'List my open PRs and post a status update to #engineering on Slack',
            'Search emails for invoices from last month and list them',
            'Find all GitHub issues assigned to me and send a Slack digest',
          ].map((cmd) => (
            <div key={cmd} className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-xl px-5 py-4">
              <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
              <span className="text-gray-200 text-sm">"{cmd}"</span>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-5xl mx-auto px-8 py-16 text-center">
        <div className="bg-gradient-to-r from-blue-600/20 to-cyan-600/20 border border-blue-500/30 rounded-3xl p-12">
          <h2 className="text-3xl font-bold mb-4">Ready to delegate securely?</h2>
          <p className="text-gray-300 mb-8">Connect your services in 60 seconds. No credentials stored on our end.</p>
          <button
            onClick={() => loginWithRedirect()}
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-10 rounded-xl text-lg transition-all duration-200 shadow-lg shadow-blue-500/25"
          >
            Start for Free
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 px-8 py-8 text-center text-gray-500 text-sm">
        <p>AgentVault — Built for the Auth0 "Authorized to Act" Hackathon 2026</p>
        <p className="mt-1">Powered by Auth0 Token Vault + Claude AI</p>
      </footer>
    </div>
  )
}
