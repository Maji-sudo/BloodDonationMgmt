import { useState, useEffect } from 'react';
import { recipientApi } from '../services/api';
import { AlertCircle, Clock, CheckCircle2, Search, MapPin, Calendar, ArrowRight, Loader2, Filter, Users, BellRing } from 'lucide-react';

export default function RequestsListPage() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all'); // 'all' | 'critical' | 'fulfilled' | 'pending'

  // Matches logic
  const [expandedRequestId, setExpandedRequestId] = useState(null);
  const [matchesMap, setMatchesMap] = useState({});
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [notifiedDonors, setNotifiedDonors] = useState({});

  useEffect(() => {
    fetchRequests();
  }, []);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const data = await recipientApi.getAll();
      setRequests(data.requests || data);
    } catch (err) {
      setError(err.message || 'Failed to load requests');
    } finally {
      setLoading(false);
    }
  };

  const toggleMatches = async (requestId) => {
    if (expandedRequestId === requestId) {
      setExpandedRequestId(null);
      return;
    }
    setExpandedRequestId(requestId);
    
    if (!matchesMap[requestId]) {
      setLoadingMatches(true);
      try {
        const data = await recipientApi.getMatches(requestId);
        setMatchesMap(prev => ({ ...prev, [requestId]: data.matches }));
      } catch (err) {
        console.error("Failed to load matches", err);
      } finally {
        setLoadingMatches(false);
      }
    }
  };

  const handleNotifyDonor = async (requestId, donorId) => {
    try {
      await recipientApi.notifyDonor(requestId, donorId);
      setNotifiedDonors(prev => ({ ...prev, [`${requestId}_${donorId}`]: true }));
    } catch (err) {
      alert("Failed to notify donor: " + (err.message || "Unknown error"));
    }
  };

  const filteredRequests = requests.filter(req => {
    if (filter === 'critical') return req.urgency === 3;
    if (filter === 'fulfilled') return req.is_fulfilled === true;
    if (filter === 'pending') return req.is_fulfilled === false;
    return true;
  });

  const getUrgencyBadge = (level) => {
    const styles = {
      1: "bg-blue-100 text-blue-800 border-blue-200",
      2: "bg-orange-100 text-orange-800 border-orange-200",
      3: "bg-red-100 text-red-800 border-red-200 animate-pulse",
    };
    const labels = { 1: "Low", 2: "Normal", 3: "CRITICAL" };
    return (
      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${styles[level]}`}>
        {labels[level]}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
        <p className="text-gray-500 font-medium tracking-wide">Fetching live blood requests...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My Blood Requests</h1>
          <p className="text-gray-600">Manage your active requests and find nearby donors to ping.</p>
        </div>

        <div className="flex items-center gap-2 bg-white p-1 rounded-xl shadow-sm border border-gray-200">
           {['all', 'pending', 'critical', 'fulfilled'].map((f) => (
             <button
               key={f}
               onClick={() => setFilter(f)}
               className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${filter === f ? 'bg-primary text-white shadow-md' : 'text-gray-600 hover:bg-gray-50'}`}
             >
               {f.charAt(0).toUpperCase() + f.slice(1)}
             </button>
           ))}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl mb-8 flex items-center gap-3">
          <AlertCircle className="w-5 h-5" />
          <p>{error}</p>
        </div>
      )}

      {filteredRequests.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-gray-300 p-16 text-center shadow-sm">
          <div className="bg-gray-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-2">No requests found</h3>
          <p className="text-gray-500 max-w-xs mx-auto mb-6">There are no requests matching your current filter. Check back later!</p>
          <button 
            onClick={fetchRequests}
            className="text-primary font-bold hover:underline"
          >
            Refresh List
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRequests.map((req) => {
            const reqId = req.id || req._id;
            return (
              <div 
                key={reqId} 
                className={`group bg-white rounded-2xl border-2 transition-all hover:shadow-xl hover:translate-y-[-4px] overflow-hidden ${req.urgency === 3 ? 'border-red-100 shadow-red-50' : 'border-gray-100 shadow-sm'}`}
              >
                {req.urgency === 3 && (
                  <div className="bg-red-600 text-white text-[10px] font-black tracking-widest uppercase py-1 px-4 text-center">
                    Immediate Requirement
                  </div>
                )}
                
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center font-bold text-primary text-xl shadow-inner">
                      {req.blood_type}
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      {getUrgencyBadge(req.urgency)}
                      <span className={`flex items-center gap-1 text-[11px] font-semibold ${req.is_fulfilled ? 'text-green-600' : 'text-gray-400'}`}>
                        {req.is_fulfilled ? <CheckCircle2 className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                        {req.is_fulfilled ? 'Fulfilled' : 'Pending'}
                      </span>
                    </div>
                  </div>

                  <h3 className="text-lg font-bold text-gray-900 mb-1 group-hover:text-primary transition-colors">
                    {req.patient_name}
                  </h3>
                  
                  <div className="space-y-3 mt-4 text-sm text-gray-600">
                    <div className="flex items-center gap-2.5">
                      <MapPin className="w-4 h-4 text-gray-400" />
                      <span className="truncate">{req.location}</span>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <span>{new Date(req.requested_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <div className="w-4 h-4 rounded-full bg-primary/5 flex items-center justify-center">
                         <span className="text-[10px] font-bold text-primary">{req.units_needed}</span>
                      </div>
                      <span>{req.units_needed} Unit(s) needed</span>
                    </div>
                  </div>

                  {req.notes && (
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg text-xs italic text-gray-500 line-clamp-2">
                      "{req.notes}"
                    </div>
                  )}

                  <div className="mt-6 pt-4 border-t border-gray-50 flex flex-col gap-3">
                    <button 
                      onClick={() => toggleMatches(reqId)}
                      disabled={req.is_fulfilled}
                      className="w-full text-sm font-bold text-primary bg-primary/5 px-4 py-2.5 rounded-lg hover:bg-primary hover:text-white transition-all shadow-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Users className="w-4 h-4" />
                      {expandedRequestId === reqId ? 'Hide Matches' : 'Find Donors Nearby'}
                    </button>
                    
                    {expandedRequestId === reqId && !req.is_fulfilled && (
                      <div className="mt-2 pt-3 border-t border-dashed border-gray-200">
                        <h4 className="text-xs font-bold text-gray-800 mb-2 flex items-center gap-1">
                           <MapPin className="w-3 h-3 text-primary" />
                           Eligible Donors
                        </h4>
                        {loadingMatches ? (
                          <div className="flex items-center justify-center p-2">
                            <Loader2 className="w-4 h-4 animate-spin text-primary" />
                          </div>
                        ) : matchesMap[reqId]?.length > 0 ? (
                          <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                            {matchesMap[reqId].map(donor => (
                               <div key={donor.id} className="flex items-center justify-between bg-gray-50 p-2.5 rounded-lg border border-gray-100 shadow-sm">
                                 <div>
                                   <p className="font-bold text-xs text-gray-900">{donor.name}</p>
                                   <p className="text-[10px] text-gray-500">{donor.distance_km} km away</p>
                                 </div>
                                 <button
                                   onClick={() => handleNotifyDonor(reqId, donor.id)}
                                   disabled={notifiedDonors[`${reqId}_${donor.id}`]}
                                   className={`flex items-center justify-center p-1.5 rounded transition-colors ${
                                     notifiedDonors[`${reqId}_${donor.id}`]
                                     ? 'bg-green-100 text-green-700'
                                     : 'bg-primary text-white hover:bg-primary-dark'
                                   }`}
                                   title="Ping Donor"
                                 >
                                   {notifiedDonors[`${reqId}_${donor.id}`] ? <CheckCircle2 className="w-3.5 h-3.5" /> : <BellRing className="w-3.5 h-3.5" />}
                                 </button>
                               </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-[10px] text-gray-500 text-center py-1">No donors found within 10km radius.</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
