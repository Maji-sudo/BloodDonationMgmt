import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, MapPin, CheckSquare, Save } from 'lucide-react';

export default function DonorRegistrationPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    bloodGroup: '',
    phone: '',
    email: '',
    age: '',
    weight: '',
    gpsAccess: false,
    termsAccepted: false,
  });

  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    const ageNum = parseInt(formData.age, 10);
    const weightNum = parseInt(formData.weight, 10);

    if ((ageNum && ageNum < 18) || (weightNum && weightNum < 50)) {
      setShowWarning(true);
    } else {
      setShowWarning(false);
    }
  }, [formData.age, formData.weight]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.termsAccepted) {
      alert("Please accept the Terms & Conditions.");
      return;
    }

    // Update local storage to mock profile update
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
    const updatedUser = { ...currentUser, ...formData, role: 'donor' };
    localStorage.setItem('currentUser', JSON.stringify(updatedUser));

    alert("Donor Profile successfully updated!");
    navigate('/role'); // or somewhere else
  };

  return (
    <div className="max-w-3xl mx-auto py-8">
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="bg-primary px-8 py-6 text-white">
          <h1 className="text-2xl font-bold">Donor Registration</h1>
          <p className="opacity-90 mt-1">Join our network of life-savers today.</p>
        </div>

        <div className="p-8">
          {showWarning && (
            <div className="mb-8 p-4 bg-orange-50 border-l-4 border-orange-500 rounded-r text-orange-800 flex items-start gap-4 shadow-sm animate-pulse-slow">
              <AlertTriangle className="w-6 h-6 text-orange-500 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-bold">⚠️ Warning</h3>
                <p className="text-sm mt-1">You may not be eligible to donate based on current health criteria (Age must be 18+ and Weight 50kg+).</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  type="text"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Blood Group</label>
                <select
                  name="bloodGroup"
                  required
                  value={formData.bloodGroup}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none bg-white"
                >
                  <option value="" disabled>Select Group</option>
                  {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(bg => (
                    <option key={bg} value={bg}>{bg}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                <input
                  type="email"
                  name="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="john@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Age (Years)</label>
                <input
                  type="number"
                  name="age"
                  required
                  min="1"
                  value={formData.age}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="e.g., 25"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Weight (kg)</label>
                <input
                  type="number"
                  name="weight"
                  required
                  min="1"
                  value={formData.weight}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none"
                  placeholder="e.g., 65"
                />
              </div>
            </div>

            <div className="border-t border-gray-100 pt-6 mt-8 space-y-4">
              <label className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  name="gpsAccess"
                  checked={formData.gpsAccess}
                  onChange={handleChange}
                  className="w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary"
                />
                <div className="flex items-center gap-2 group-hover:text-primary transition-colors">
                  <MapPin className="w-5 h-5 text-gray-400 group-hover:text-primary" />
                  <span className="text-gray-700">Allow GPS Location Access (to find nearby needs)</span>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  name="termsAccepted"
                  checked={formData.termsAccepted}
                  onChange={handleChange}
                  className="w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary"
                />
                <div className="flex items-center gap-2 group-hover:text-primary transition-colors">
                  <CheckSquare className="w-5 h-5 text-gray-400 group-hover:text-primary" />
                  <span className="text-gray-700">I agree to the Terms & Conditions and declare my health status is accurate</span>
                </div>
              </label>
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                className="flex items-center gap-2 px-8 py-3 bg-primary text-white font-medium rounded-lg hover:bg-primary-light transition-colors shadow-md focus:ring-2 focus:ring-offset-2 focus:ring-primary"
              >
                <Save className="w-5 h-5" />
                Submit Registration
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
