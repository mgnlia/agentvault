'use client'

import { CheckCircle, XCircle, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

interface ActivityItem {
  id: number
  command: string
  timestamp: string
  status: string
  plan: any[]
  results: any[]
  message: string
}

interface Props {
  results: ActivityItem[]
}

export function ActivityFeed({ results }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null)

  if (results.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <Clock className="w-8 h-8 mx-auto mb-3 opacity-50" />
        <p className="text-sm">No activity yet. Run a command to get started.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-gray-900 mb-4">Command History</h3>
      {results.map(item => (
        <div key={item.id} className="border border-gray-200 rounded-xl overflow-hidden">
          <button
            onClick={() => setExpanded(expanded === item.id ? null : item.id)}
            className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors text-left"
          >
            {item.status === 'completed' || item.status === 'success' ? (
              <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
            ) : item.status === 'error' ? (
              <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
            ) : (
              <Clock className="w-4 h-4 text-amber-500 flex-shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900 truncate">"{item.command}"</p>
              <p className="text-xs text-gray-400 mt-0.5">{new Date(item.timestamp).toLocaleTimeString()}</p>
            </div>
            <span className={`badge flex-shrink-0 ${
              item.status === 'completed' ? 'bg-green-100 text-green-700' :
              item.status === 'error' ? 'bg-red-100 text-red-700' :
              'bg-amber-100 text-amber-700'
            }`}>
              {item.status}
            </span>
            {expanded === item.id ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
          </button>

          {expanded === item.id && (
            <div className="border-t border-gray-200 p-4 bg-gray-50 space-y-3">
              <p className="text-sm text-gray-600">{item.message}</p>

              {item.plan.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Execution Plan</p>
                  <div className="space-y-1.5">
                    {item.plan.map((step: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-xs">
                        <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-medium flex-shrink-0">
                          {step.step || i + 1}
                        </span>
                        <span className="text-gray-500 capitalize">{step.service}</span>
                        <span className="text-gray-400">→</span>
                        <span className="text-gray-700">{step.description || step.action}</span>
                        {step.requires_step_up && (
                          <span className="badge bg-amber-100 text-amber-700">step-up</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {item.results.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Results</p>
                  <div className="space-y-1.5">
                    {item.results.map((r: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-xs">
                        {r.status === 'success' ? (
                          <CheckCircle className="w-3.5 h-3.5 text-green-500" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 text-red-500" />
                        )}
                        <span className="text-gray-600">{r.service} / {r.action}: {r.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
