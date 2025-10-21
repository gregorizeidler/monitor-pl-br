import { AlertTriangle, XCircle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  variant?: 'error' | 'warning' | 'info';
}

export function ErrorMessage({ message, onRetry, variant = 'error' }: ErrorMessageProps) {
  const colors = {
    error: {
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      icon: 'text-red-400',
      text: 'text-red-300',
      button: 'bg-red-500/20 hover:bg-red-500/30 text-red-300'
    },
    warning: {
      bg: 'bg-yellow-500/10',
      border: 'border-yellow-500/30',
      icon: 'text-yellow-400',
      text: 'text-yellow-300',
      button: 'bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300'
    },
    info: {
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      icon: 'text-blue-400',
      text: 'text-blue-300',
      button: 'bg-blue-500/20 hover:bg-blue-500/30 text-blue-300'
    }
  };

  const style = colors[variant];
  const Icon = variant === 'error' ? XCircle : AlertTriangle;

  return (
    <div className={`${style.bg} border ${style.border} rounded-lg p-4 my-4`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-6 h-6 ${style.icon} flex-shrink-0 mt-0.5`} />
        <div className="flex-1">
          <p className={`${style.text} text-sm leading-relaxed`}>{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className={`mt-3 ${style.button} px-4 py-2 rounded text-sm font-medium transition-colors flex items-center gap-2`}
            >
              <RefreshCw className="w-4 h-4" />
              Tentar novamente
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function EmptyState({ 
  icon: Icon = AlertTriangle, 
  title, 
  description 
}: { 
  icon?: any; 
  title: string; 
  description: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <Icon className="w-16 h-16 text-gray-400 mb-4" />
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400 text-sm max-w-md">{description}</p>
    </div>
  );
}

