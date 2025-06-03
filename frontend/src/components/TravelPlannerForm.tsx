'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CalendarIcon, MapPinIcon, PlaneIcon } from 'lucide-react';
import { TravelRequest } from '@/types';

interface TravelPlannerFormProps {
  onSubmit: (request: TravelRequest) => void;
  isLoading: boolean;
}

export function TravelPlannerForm({ onSubmit, isLoading }: TravelPlannerFormProps) {
  const [formData, setFormData] = useState<TravelRequest>({
    destination_city: 'Tokyo',
    destination_country: 'Japan',
    depart_date: '2025-10-10',
    return_date: '2025-10-17',
    priority: 'food',
    budget_level: 'flexible',
    departure_airport: 'LHR',
    destination_airport: '',
    additional_preferences: 'interested in temples and authentic experiences',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      destination_airport: formData.destination_airport || undefined,
      additional_preferences: formData.additional_preferences || undefined,
    });
  };

  const handleInputChange = (field: keyof TravelRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PlaneIcon className="h-5 w-5" />
          Plan Your Perfect Trip
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="destination_city" className="flex items-center gap-1">
                <MapPinIcon className="h-4 w-4" />
                Destination City
              </Label>
              <Input
                id="destination_city"
                value={formData.destination_city}
                onChange={(e) => handleInputChange('destination_city', e.target.value)}
                placeholder="e.g., Tokyo"
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="destination_country">Country</Label>
              <Input
                id="destination_country"
                value={formData.destination_country}
                onChange={(e) => handleInputChange('destination_country', e.target.value)}
                placeholder="e.g., Japan"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="depart_date" className="flex items-center gap-1">
                <CalendarIcon className="h-4 w-4" />
                Departure Date
              </Label>
              <Input
                id="depart_date"
                type="date"
                value={formData.depart_date}
                onChange={(e) => handleInputChange('depart_date', e.target.value)}
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="return_date">Return Date</Label>
              <Input
                id="return_date"
                type="date"
                value={formData.return_date}
                onChange={(e) => handleInputChange('return_date', e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="departure_airport">Departure Airport</Label>
              <Input
                id="departure_airport"
                value={formData.departure_airport}
                onChange={(e) => handleInputChange('departure_airport', e.target.value)}
                placeholder="e.g., LHR, JFK, LAX"
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="destination_airport">Destination Airport (Optional)</Label>
              <Input
                id="destination_airport"
                value={formData.destination_airport}
                onChange={(e) => handleInputChange('destination_airport', e.target.value)}
                placeholder="e.g., NRT, HND"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="priority">Travel Priority</Label>
              <Select value={formData.priority} onValueChange={(value: any) => handleInputChange('priority', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="food">Food & Dining</SelectItem>
                  <SelectItem value="culture">Culture & Arts</SelectItem>
                  <SelectItem value="history">History & Heritage</SelectItem>
                  <SelectItem value="adventure">Adventure & Sports</SelectItem>
                  <SelectItem value="relaxation">Relaxation & Wellness</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="budget_level">Budget Level</Label>
              <Select value={formData.budget_level} onValueChange={(value: any) => handleInputChange('budget_level', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select budget" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="budget">Budget-Friendly</SelectItem>
                  <SelectItem value="moderate">Moderate</SelectItem>
                  <SelectItem value="flexible">Flexible</SelectItem>
                  <SelectItem value="luxury">Luxury</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="additional_preferences">Additional Preferences</Label>
            <Textarea
              id="additional_preferences"
              value={formData.additional_preferences}
              onChange={(e) => handleInputChange('additional_preferences', e.target.value)}
              placeholder="Tell us about your interests, dietary restrictions, accessibility needs, etc."
              rows={3}
            />
          </div>

          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? 'Generating Your Travel Plan...' : 'Create Travel Plan'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}