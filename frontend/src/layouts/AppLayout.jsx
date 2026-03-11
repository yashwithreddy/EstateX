import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';

function AppLayout() {
  return (
    <div className="mx-auto flex min-h-screen max-w-7xl gap-4 p-4 md:flex-row">
      <Sidebar />
      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  );
}

export default AppLayout;
