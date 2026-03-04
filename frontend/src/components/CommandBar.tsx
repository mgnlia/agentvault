'use client'

import { useState, useRef } from 'react'
import { Send, Loader2, Zap } from 'lucide-react'

interface Props {
  onCommand: (command: string) => Promise<void>
  connectedServices: string[]
}

export function CommandBar({ onCommand, connectedServices }: Props) {
  const [command, setCommand] = useState('')
  const [loading, setLoading] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!command.trim() || loading) return
    const cmd = command.trim()
    setCommand('')
    setLoading(true)
    try {
      await onCommand(cmd)
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Zap className="w-4 h-4 text-blue-600" />
        <span className="text-sm font-medium text-gray-700">Agent Command</span>
        {connectedServices.length > 0 && (
          <span className="text-xs text-gray-400">
            — {connectedServices.join(', ')} connected
          </span>
        )}
      </div>
      <form onSubmit={handleSubmit} className="flex gap-3">
        <textarea
          ref={textareaRef}
          value={command}
          onChange={e => setCommand(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Tell AgentVault what to do... (e.g. 'Summarize my unread emails and create GitHub issues for action items')"
          rows={2}
          className="flex-1 resize-none rounded-lg border border-gray-200 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={!command.trim() || loading}
          className="btn-primary flex items-center gap-2 self-end px-5 py-3"
        >
          {loading ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Running</>
          ) : (
            <><Send className="w-4 h-4" /> Run</>
          )}
        </button>
      </form>
      <p className="text-xs text-gray-400 mt-2">Press Enter to run · Shift+Enter for new line</p>
    </div>
  )
}
