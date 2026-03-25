import { useState } from 'react';
import { AlertCircle, Clock, Calendar, Send, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { recipientApi } from '../services/api';

export default function RecipientDashboardPage() {
  const [formData, setFormData] = useState({
    patient_name: '',
    email: '',
    phone: '',
    blood_type: '',
    units_needed: '',
    location: '',
    urgency: 1,
    notes: '',
  });

  const [status, setStatus] = useState('idle'); // 'idle' | 'loading' | 'success' | 'error'
  const [apiError, setApiError] = useState('');
  const [submittedRequest, setSubmittedRequest] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' || name === 'urgency' ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError('');
    setStatus('loading');

    try {
      const payload = {
        ...formData,
        units_needed: parseInt(formData.units_needed, 10),
      };

      const result = await recipientApi.submitRequest(payload);
      setSubmittedRequest(result.request);
      setStatus('success');
    } catch (err) {
      setStatus('error');
      setApiError(err.message);
    }
  };

  const resetForm = () => {
    setFormData({
      patient_name: '', email: '', phone: '',
      blood_type: '', units_needed: '', location: '',
      urgency: 1, notes: '',
    });
    setStatus('idle');
    setApiError('');
    setSubmittedRequest(null);
  };

  const isCritical = formData.urgency === 3;

  const urgencyConfig = {
    1: { label: 'Level 1 (Low)', desc: 'Surgery scheduled in 10 days.', icon: Calendar, color: 'primary', border: 'border-primary', bg: 'bg-red-50' },
    2: { label: 'Level 2 (Medium)', desc: 'Blood required within 3 days.', icon: Clock, color: 'orange-500', border: 'border-orange-500', bg: 'bg-orange-50' },
    3: { label: 'Level 3 (High)', desc: 'CRITICAL: Sudden accident/trauma. Immediate requirement.', icon: AlertCircle, color: 'red-600', border: 'border-red-600', bg: 'bg-red-50' },
  };

  // ── Success Screen ───────────────────────────
  if (status === 'success' && submittedRequest) {
    const urgencyLabels = { 1: 'Low', 2: 'Medium', 3: 'Critical' };
    const urgencyColors = { 1: 'text-primary', 2: 'text-orange-500', 3: 'text-red-600' };
    return (
      <div className="max-w-4xl mx-auto py-8 flex items-center justify-center min-h-[60vh]">
        <div className="text-center bg-white rounded-2xl shadow-lg border border-gray-100 p-12 w-full max-w-lg">
          <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-12 h-12 text-green-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Request Submitted!</h2>
          <p className="text-gray-500 mb-6">Your blood request has been broadcast to available donors.</p>

          <div className="text-left bg-gray-50 rounded-xl p-5 space-y-2 text-sm mb-6">
            <div className="flex justify-between"><span className="text-gray-500">Patient</span><span className="font-medium">{submittedRequest.patient_name}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Blood Type</span><span className="font-bold text-primary">{submittedRequest.blood_type}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Units Needed</span><span className="font-medium">{submittedRequest.units_needed}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Urgency</span><span className={`font-bold ${urgencyColors[submittedRequest.urgency]}`}>{urgencyLabels[submittedRequest.urgency]}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Location</span><span className="font-medium text-right max-w-[180px]">{submittedRequest.location}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Request ID</span><span className="font-mono text-xs text-gray-400">{submittedRequest.id}</span></div>
          </div>

          <div className="flex flex-col gap-3">
            <button
              onClick={resetForm}
              className="w-full py-3 px-6 bg-primary text-white font-medium rounded-lg hover:bg-primary-light transition-colors"
            >
              Submit Another Request
            </button>
            <button
              onClick={() => navigate('/requests')}
              className="w-full py-3 px-6 bg-white text-primary border border-primary font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              View Live Requests Feed
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Request Blood</h1>
        <p className="text-gray-600">Please provide detailed information to help donors reach you quickly.</p>
      </div>

      <div className={`bg-white rounded-2xl shadow-lg border overflow-hidden transition-all duration-300 ${isCritical ? 'border-red-500 shadow-red-200' : 'border-gray-100'}`}
        style={isCritical ? { animation: 'pulse-border 2s infinite' } : {}}>

        {isCritical && (
          <div className="bg-red-600 text-white px-6 py-3 flex items-center gap-3">
            <AlertCircle className="w-6 h-6 animate-pulse" />
            <span className="font-bold tracking-wide">CRITICAL EMERGENCY RESPONSE ACTIVATED</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-8 space-y-8">

          {/* API error */}
          {apiError && status === 'error' && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3 text-red-700 text-sm">
              <XCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <p>{apiError}</p>
            </div>
          )}

          {/* Urgency Selection */}
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-4">Urgency Level</h3>
            <div className="grid md:grid-cols-3 gap-4">
              {[1, 2, 3].map((level) => {
                const cfg = urgencyConfig[level];
                const Icon = cfg.icon;
                const isSelected = formData.urgency === level;
                return (
                  <label
                    key={level}
                    className={`relative flex flex-col p-4 cursor-pointer rounded-xl border-2 transition-all ${isSelected ? `${cfg.border} ${cfg.bg}` : 'border-gray-200 hover:border-gray-300'}`}
                  >
                    <input type="radio" name="urgency" value={level} checked={isSelected} onChange={handleChange} className="sr-only" />
                    <div className="flex items-center gap-2 mb-2">
                      <Icon className={`w-5 h-5 ${isSelected ? `text-${cfg.color}` : 'text-gray-400'} ${isSelected && level === 3 ? 'animate-bounce' : ''}`} />
                      <span className={`font-bold ${level === 3 ? 'text-red-600' : 'text-gray-900'}`}>{cfg.label}</span>
                    </div>
                    <p className="text-sm text-gray-600">{cfg.desc}</p>
                  </label>
                );
              })}
            </div>
          </div>

          <hr className="border-gray-100" />

          {/* Patient Details */}
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-4">Patient & Hospital Details</h3>
            <div className="grid md:grid-cols-2 gap-6">

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Patient Name</label>
                <input
                  type="text" name="patient_name" required
                  value={formData.patient_name} onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="Patient's full name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Required Blood Type</label>
                <select
                  name="blood_type" required
                  value={formData.blood_type} onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none bg-white"
                >
                  <option value="" disabled>Select Type</option>
                  {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(bg => (
                    <option key={bg} value={bg}>{bg}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Units Needed</label>
                <input
                  type="number" name="units_needed" required min="1"
                  value={formData.units_needed} onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="e.g., 2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contact Phone</label>
                <input
                  type="tel" name="phone" required
                  value={formData.phone} onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="+91 9876543210"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contact Email</label>
                <input
                  type="email" name="email" required
                  value={formData.email} onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="contact@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Hospital Location / Address</label>
                <input
                  type="text" name="location" required
                  value={formData.location} onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="Hospital Name, City"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Additional Notes <span className="text-gray-400">(optional)</span></label>
                <textarea
                  name="notes" rows={2}
                  value={formData.notes} onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none resize-none"
                  placeholder="Any additional information for donors…"
                />
              </div>
            </div>
          </div>

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              disabled={status === 'loading'}
              className={`flex items-center gap-2 px-8 py-3 font-medium rounded-lg text-white shadow-md transition-all focus:ring-2 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed ${
                isCritical
                  ? 'bg-red-600 hover:bg-red-700 focus:ring-red-600'
                  : 'bg-primary hover:bg-primary-light focus:ring-primary'
              }`}
            >
              {status === 'loading' ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Submitting…
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  {isCritical ? 'BROADCAST EMERGENCY REQUEST' : 'Submit Request'}
                </>
              )}
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
      `}} />
    </div>
  );
}
