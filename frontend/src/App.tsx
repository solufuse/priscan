import { Routes, Route, Link } from 'react-router-dom';
import StockTracker from './pages/StockTracker';
import Dashboard from './pages/Dashboard';
import './App.css';
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarProvider,
  SidebarTrigger,
  SidebarInset,
} from './components/ui/sidebar';

function App() {
    return (
      <SidebarProvider>
        <div className="flex min-h-screen bg-background text-foreground">
            <Sidebar>
                <SidebarHeader>
                  <SidebarTrigger />
                </SidebarHeader>
                <SidebarContent>
                  <SidebarMenu>
                    <SidebarMenuItem>
                      <Link to="/">
                        <SidebarMenuButton>Stock Tracker</SidebarMenuButton>
                      </Link>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <Link to="/dashboard">
                        <SidebarMenuButton>S&P 500 Dashboard</SidebarMenuButton>
                      </Link>
                    </SidebarMenuItem>
                  </SidebarMenu>
                </SidebarContent>
            </Sidebar>

            <SidebarInset>
                <Routes>
                    <Route path="/" element={<StockTracker />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                </Routes>
            </SidebarInset>
        </div>
      </SidebarProvider>
    );
}

export default App;
