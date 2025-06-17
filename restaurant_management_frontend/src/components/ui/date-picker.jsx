import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Calendar } from 'lucide-react';
import debounce from 'lodash/debounce';

// Simple date picker component since react-day-picker has peer dependency issues
export const DatePickerWithRange = ({ date, setDate }) => {
  const [startDate, setStartDate] = useState(date?.from ? date.from.toISOString().split('T')[0] : '');
  const [endDate, setEndDate] = useState(date?.to ? date.to.toISOString().split('T')[0] : '');

  // Debounced date update function
  const debouncedSetDate = useCallback(
    debounce((newStartDate, newEndDate) => {
      setDate({
        from: newStartDate ? new Date(newStartDate) : null,
        to: newEndDate ? new Date(newEndDate) : null
      });
    }, 500),
    [setDate]
  );

  const handleStartDateChange = (e) => {
    const newStartDate = e.target.value;
    setStartDate(newStartDate);
    debouncedSetDate(newStartDate, endDate);
  };

  const handleEndDateChange = (e) => {
    const newEndDate = e.target.value;
    setEndDate(newEndDate);
    debouncedSetDate(startDate, newEndDate);
  };

  return (
    <div className="flex space-x-2">
      <div className="flex-1">
        <Label htmlFor="start-date">From</Label>
        <Input
          id="start-date"
          type="date"
          value={startDate}
          onChange={handleStartDateChange}
        />
      </div>
      <div className="flex-1">
        <Label htmlFor="end-date">To</Label>
        <Input
          id="end-date"
          type="date"
          value={endDate}
          onChange={handleEndDateChange}
        />
      </div>
    </div>
  );
};

