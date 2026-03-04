'use client'

import { Shield, AlertTriangle, X } from 'lucide-react'

interface Props {
  action: string
  onConfirm: () => void
  onCancel: () => void
}

export function StepUpModal({ action, onConfirm, onCancel }: Props) {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
              <Shield className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900">Step-up Authentication Required</h3>
              <p className="text-sm text-gray-500">Sensitive action detected</p>
            </div>
          </div>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-900">
                Action: <code className="bg-amber-100 px-1.5 py-0.5 rounded text-amber-800">{action}</code>
              </p>
              <p className="text-sm text-amber-700 mt-1">
                This action is marked as sensitive and requires your explicit confirmation.
                Auth0 Token Vault enforces step-up authentication to protect against
                unauthorized consequential actions.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-2 mb-6">
          <p className="text-sm font-medium text-gray-700">By confirming, you authorize AgentVault to:</p>
          <ul className="text-sm text-gray-600 space-y-1">
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
              Execute the "{action}" action on your behalf
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
              Use your stored OAuth token from Auth0 Token Vault
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
              Log this action in your audit trail
            </li>
          </ul>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="btn-secondary flex-1"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 bg-amber-600 hover:bg-amber-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            Confirm & Execute
          </button>
        </div>
      </div>
    </div>
  )
}
