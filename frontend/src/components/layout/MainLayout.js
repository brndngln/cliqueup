import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { 
    DropdownMenu, 
    DropdownMenuContent, 
    DropdownMenuItem, 
    DropdownMenuSeparator, 
    DropdownMenuTrigger 
} from '../ui/dropdown-menu';
import { Badge } from '../ui/badge';
import { 
    Home, 
    Search, 
    Heart, 
    MessageCircle, 
    Bell, 
    User, 
    Settings, 
    LogOut, 
    Sparkles,
    Plus,
    Users,
    Play,
    Compass
} from 'lucide-react';
import { cn } from '../../lib/utils';

const navItems = [
    { path: '/home', icon: Home, label: 'Home' },
    { path: '/explore', icon: Compass, label: 'Explore' },
    { path: '/meet', icon: Heart, label: 'Meet', requiresAdult: true },
    { path: '/messages', icon: MessageCircle, label: 'Messages' },
];

export const MainLayout = ({ children }) => {
    const { user, logout, isAdult, canAccessMeet, api } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const [unreadNotifications, setUnreadNotifications] = useState(0);
    const [profile, setProfile] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [notifRes, profileRes] = await Promise.all([
                    api.get('/notifications/unread-count'),
                    api.get('/profiles/me')
                ]);
                setUnreadNotifications(notifRes.data.count);
                setProfile(profileRes.data);
            } catch (e) {
                console.error('Failed to fetch data');
            }
        };
        fetchData();
    }, [api]);

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const getInitials = (name) => {
        return name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'U';
    };

    return (
        <div className="min-h-screen bg-background">
            {/* Top Navigation */}
            <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5">
                <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
                    {/* Logo */}
                    <Link to="/home" className="flex items-center gap-2">
                        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-pink-600 to-teal-600 flex items-center justify-center">
                            <Sparkles className="w-4 h-4 text-white" />
                        </div>
                        <span className="font-heading text-xl font-bold hidden sm:block">CliqUp</span>
                    </Link>

                    {/* Desktop Navigation */}
                    <nav className="hidden md:flex items-center gap-1">
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
                            const isDisabled = item.requiresAdult && !isAdult;
                            
                            if (isDisabled) return null;
                            
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={cn(
                                        "flex items-center gap-2 px-4 py-2 rounded-full transition-colors",
                                        isActive 
                                            ? "bg-primary/10 text-primary" 
                                            : "text-muted-foreground hover:text-foreground hover:bg-accent"
                                    )}
                                    data-testid={`nav-${item.label.toLowerCase()}`}
                                >
                                    <item.icon className="w-5 h-5" />
                                    <span className="text-sm font-medium">{item.label}</span>
                                </Link>
                            );
                        })}
                    </nav>

                    {/* Right side */}
                    <div className="flex items-center gap-3">
                        {/* Search */}
                        <Link to="/search">
                            <Button variant="ghost" size="icon" className="rounded-full" data-testid="search-btn">
                                <Search className="w-5 h-5" />
                            </Button>
                        </Link>

                        {/* Notifications */}
                        <Link to="/notifications" className="relative">
                            <Button variant="ghost" size="icon" className="rounded-full" data-testid="notifications-btn">
                                <Bell className="w-5 h-5" />
                            </Button>
                            {unreadNotifications > 0 && (
                                <span className="absolute -top-1 -right-1 w-5 h-5 bg-destructive text-destructive-foreground text-xs font-bold rounded-full flex items-center justify-center badge-pulse">
                                    {unreadNotifications > 9 ? '9+' : unreadNotifications}
                                </span>
                            )}
                        </Link>

                        {/* User Menu */}
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="rounded-full p-0" data-testid="user-menu-btn">
                                    <Avatar className="w-9 h-9">
                                        <AvatarImage src={profile?.avatar_url} alt={user?.display_name} />
                                        <AvatarFallback className="bg-primary/20 text-primary">
                                            {getInitials(user?.display_name)}
                                        </AvatarFallback>
                                    </Avatar>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-56">
                                <div className="px-3 py-2">
                                    <p className="font-medium">{user?.display_name}</p>
                                    <p className="text-sm text-muted-foreground">@{user?.handle}</p>
                                </div>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem asChild>
                                    <Link to="/profile" className="cursor-pointer">
                                        <User className="w-4 h-4 mr-2" />
                                        Profile
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem asChild>
                                    <Link to="/settings" className="cursor-pointer">
                                        <Settings className="w-4 h-4 mr-2" />
                                        Settings
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={handleLogout} className="text-destructive cursor-pointer" data-testid="logout-btn">
                                    <LogOut className="w-4 h-4 mr-2" />
                                    Log out
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="pt-16 pb-20 md:pb-0 min-h-screen">
                {children}
            </main>

            {/* Mobile Bottom Navigation */}
            <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 glass border-t border-white/5">
                <div className="flex items-center justify-around h-16">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
                        const isDisabled = item.requiresAdult && !isAdult;
                        
                        if (isDisabled) return null;
                        
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={cn(
                                    "flex flex-col items-center gap-1 p-2 rounded-lg transition-colors",
                                    isActive ? "text-primary" : "text-muted-foreground"
                                )}
                                data-testid={`mobile-nav-${item.label.toLowerCase()}`}
                            >
                                <item.icon className="w-5 h-5" />
                                <span className="text-xs">{item.label}</span>
                            </Link>
                        );
                    })}
                    <Link
                        to="/profile"
                        className={cn(
                            "flex flex-col items-center gap-1 p-2 rounded-lg transition-colors",
                            location.pathname === '/profile' ? "text-primary" : "text-muted-foreground"
                        )}
                        data-testid="mobile-nav-profile"
                    >
                        <User className="w-5 h-5" />
                        <span className="text-xs">Profile</span>
                    </Link>
                </div>
            </nav>
        </div>
    );
};

export default MainLayout;
