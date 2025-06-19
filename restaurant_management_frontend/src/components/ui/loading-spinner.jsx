import React from 'react';
import { Loader2 } from 'lucide-react';

export const LoadingSpinner = ({ size = "default", text = "Loading..." }) => {
  const sizeClasses = {
    sm: "w-4 h-4",
    default: "w-6 h-6", 
    lg: "w-8 h-8",
    xl: "w-12 h-12"
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-4">
      <Loader2 className={`${sizeClasses[size]} animate-spin text-primary`} />
      {text && <p className="text-sm text-muted-foreground">{text}</p>}
    </div>
  );
};

export const LoadingCard = ({ title = "Loading...", description = "Please wait while we fetch your data" }) => {
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center space-x-2">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
        <h3 className="text-lg font-medium">{title}</h3>
      </div>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
};

export const SkeletonCard = () => {
  return (
    <div className="p-6 space-y-4">
      <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4"></div>
      <div className="h-3 bg-gray-200 rounded animate-pulse w-1/2"></div>
      <div className="h-32 bg-gray-200 rounded animate-pulse"></div>
    </div>
  );
}; 