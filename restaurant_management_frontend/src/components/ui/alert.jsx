import React from 'react';

export const Alert = ({ children, variant = 'default', className = '' }) => {
  const baseClasses = 'relative w-full rounded-lg border p-4';
  const variantClasses = {
    default: 'bg-background text-foreground',
    destructive: 'border-red-500/50 text-red-900 bg-red-50'
  };

  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      {children}
    </div>
  );
};

export const AlertDescription = ({ children, className = '' }) => {
  return (
    <div className={`text-sm [&_p]:leading-relaxed ${className}`}>
      {children}
    </div>
  );
};

