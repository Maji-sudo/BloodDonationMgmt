import { Droplet } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="bg-primary text-white shadow-md">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold tracking-tight">
          <Droplet className="w-6 h-6 fill-white" />
          <span>LifeBlood</span>
        </Link>
        <div className="text-sm font-medium opacity-90">Smart Blood Bank</div>
      </div>
    </nav>
  );
}
