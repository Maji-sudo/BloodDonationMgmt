import { useNavigate } from 'react-router-dom';
import { Heart, Activity } from 'lucide-react';

export default function RoleSelectionPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] py-12">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Choose Your Role</h1>
        <p className="text-gray-600 max-w-lg mx-auto">
          Please select whether you want to donate blood to save lives, or if you are in need of blood for medical purposes.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8 w-full max-w-4xl px-4">
        {/* Donor Card */}
        <button
          onClick={() => navigate('/donor')}
          className="group flex flex-col items-center p-10 bg-white border-2 border-gray-100 rounded-2xl shadow-sm hover:shadow-xl hover:border-primary transition-all duration-300 transform hover:-translate-y-1"
        >
          <div className="w-20 h-20 bg-red-50 text-primary rounded-full flex items-center justify-center mb-6 group-hover:bg-primary group-hover:text-white transition-colors duration-300">
            <Heart className="w-10 h-10" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">I want to Donate</h2>
          <p className="text-gray-500 max-w-xs group-hover:text-gray-700 transition-colors">
            Register as a donor and help save lives by donating blood.
          </p>
        </button>

        {/* Recipient Card */}
        <button
          onClick={() => navigate('/recipient')}
          className="group flex flex-col items-center p-10 bg-white border-2 border-gray-100 rounded-2xl shadow-sm hover:shadow-xl hover:border-blue-600 transition-all duration-300 transform hover:-translate-y-1"
        >
          <div className="w-20 h-20 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mb-6 group-hover:bg-blue-600 group-hover:text-white transition-colors duration-300">
            <Activity className="w-10 h-10" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">I need Blood</h2>
          <p className="text-gray-500 max-w-xs group-hover:text-gray-700 transition-colors">
            Post an urgent request to find blood donors near your location.
          </p>
        </button>
      </div>
    </div>
  );
}
