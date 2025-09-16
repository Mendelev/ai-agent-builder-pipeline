import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import clsx from 'clsx';

interface CopyButtonProps {
  text: string;
  className?: string;
  label?: string;
}

export const CopyButton: React.FC<CopyButtonProps> = ({
  text,
  className,
  label = 'Copy',
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={clsx(
        'inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium',
        copied
          ? 'bg-green-50 text-green-700 border-green-300'
          : 'bg-white text-gray-700 hover:bg-gray-50',
        className
      )}
    >
      {copied ? (
        <>
          <Check className="h-4 w-4 mr-1" />
          Copied!
        </>
      ) : (
        <>
          <Copy className="h-4 w-4 mr-1" />
          {label}
        </>
      )}
    </button>
  );
};