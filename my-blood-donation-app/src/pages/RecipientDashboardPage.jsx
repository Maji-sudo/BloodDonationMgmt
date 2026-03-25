import { useState } from 'react';
import { AlertCircle, Clock, Calendar, Send } from 'lucide-react';

export default function RecipientDashboardPage() {
  const [formData, setFormData] = useState({
    bloodType: '',
    units: '',
    location: '',
    phone: '',
    email: '',
    urgency: '1' // 1: Low, 2: Medium, 3: High
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    alert(`Blood Request Submitted! (Urgency Level ${formData.urgency})`);
    // Mock save
    setFormData({
      bloodType: '', units: '', location: '', phone: '', email: '', urgency: '1'
    });
  };

  const isCritical = formData.urgency === '3';

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Request Blood</h1>
        <p className="text-gray-600">Please provide detailed information to help donors reach you quickly.</p>
      </div>

      <div className={`bg-white rounded-2xl shadow-lg border overflow-hidden transition-all duration-300 ${isCritical ? 'border-red-500 animate-pulse-border shadow-red-200' : 'border-gray-100'}`}>
        {isCritical && (
          <div className="bg-red-600 text-white px-6 py-3 flex items-center gap-3">
            <AlertCircle className="w-6 h-6 animate-pulse" />
            <span className="font-bold tracking-wide">CRITICAL EMERGENCY RESPONSE ACTIVATED</span>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="p-8 space-y-8">
          {/* Urgency Selection */}
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-4">Urgency Level</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <label className={`relative flex flex-col p-4 cursor-pointer rounded-xl border-2 transition-all ${formData.urgency === '1' ? 'border-primary bg-red-50' : 'border-gray-200 hover:border-primary-light'}`}>
                <input type="radio" name="urgency" value="1" checked={formData.urgency === '1'} onChange={handleChange} className="sr-only" />
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className={`w-5 h-5 ${formData.urgency === '1' ? 'text-primary' : 'text-gray-400'}`} />
                  <span className="font-bold text-gray-900">Level 1 (Low)</span>
                </div>
                <p className="text-sm text-gray-600">Surgery scheduled in 10 days.</p>
              </label>

              <label className={`relative flex flex-col p-4 cursor-pointer rounded-xl border-2 transition-all ${formData.urgency === '2' ? 'border-orange-500 bg-orange-50' : 'border-gray-200 hover:border-orange-300'}`}>
                <input type="radio" name="urgency" value="2" checked={formData.urgency === '2'} onChange={handleChange} className="sr-only" />
                <div className="flex items-center gap-2 mb-2">
                  <Clock className={`w-5 h-5 ${formData.urgency === '2' ? 'text-orange-500' : 'text-gray-400'}`} />
                  <span className="font-bold text-gray-900">Level 2 (Medium)</span>
                </div>
                <p className="text-sm text-gray-600">Blood required within 3 days.</p>
              </label>

              <label className={`relative flex flex-col p-4 cursor-pointer rounded-xl border-2 transition-all ${formData.urgency === '3' ? 'border-red-600 bg-red-50' : 'border-gray-200 hover:border-red-400'}`}>
                <input type="radio" name="urgency" value="3" checked={formData.urgency === '3'} onChange={handleChange} className="sr-only" />
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className={`w-5 h-5 ${formData.urgency === '3' ? 'text-red-600 animate-bounce' : 'text-gray-400'}`} />
                  <span className="font-bold text-red-600">Level 3 (High)</span>
                </div>
                <p className="text-sm text-gray-600 font-medium tracking-tight">CRITICAL: Sudden accident/trauma. Immediate requirement.</p>
              </label>
            </div>
          </div>

          <hr className="border-gray-100" />

          {/* Patient Details */}
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-4">Patient & Hospital Details</h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Required Blood Type</label>
                <select
                  name="bloodType"
                  required
                  value={formData.bloodType}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none bg-white"
                >
                  <option value="" disabled>Select Type</option>
                  {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Any'].map(bg => (
                    <option key={bg} value={bg}>{bg}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Units Needed</label>
                <input
                  type="number"
                  name="units"
                  required
                  min="1"
                  value={formData.units}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="e.g., 2"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Hospital Location / Address</label>
                <input
                  type="text"
                  name="location"
                  required
                  value={formData.location}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="Hospital Name, City"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contact Phone</label>
                <input
                  type="tel"
                  name="phone"
                  required
                  value={formData.phone}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="+1 (555) 000-0000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contact Email</label>
                <input
                  type="email"
                  name="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="contact@example.com"
                />
              </div>
            </div>
          </div>

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              className={`flex items-center gap-2 px-8 py-3 font-medium rounded-lg text-white shadow-md transition-all focus:ring-2 focus:ring-offset-2 ${
                isCritical 
                  ? 'bg-red-600 hover:bg-red-700 focus:ring-red-600 animate-pulse' 
                  : 'bg-primary hover:bg-primary-light focus:ring-primary'
              }`}
            >
              <Send className="w-5 h-5" />
              {isCritical ? 'BROADCAST EMERGENCY REQUEST' : 'Submit Request'}
            </button>
          </div>
        </form>
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes pulse-border {
          0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
          70% { box-shadow: 0 0 0 15px rgba(220, 38, 38, 0); }
          100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
        }
        .animate-pulse-border {
          animation: pulse-border 2s infinite;
        }
      `}} />
    </div>
  );
}
