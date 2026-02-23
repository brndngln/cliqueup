import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { MainLayout } from '../components/layout/MainLayout';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
    Bell, 
    Heart, 
    MessageCircle, 
    Users, 
    UserPlus, 
    Sparkles,
    Check,
    CheckCheck
} from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { Link } from 'react-router-dom';
import { cn } from '../lib/utils';

const getNotificationIcon = (type) => {
    switch (type) {
        case 'follow': return UserPlus;
        case 'like': return Heart;
        case 'comment': return MessageCircle;
        case 'squad_invite': return Users;
        case 'match': return Sparkles;
        default: return Bell;
    }
};

const getNotificationColor = (type) => {
    switch (type) {
        case 'follow': return 'text-blue-400 bg-blue-400/20';
        case 'like': return 'text-red-400 bg-red-400/20';
        case 'comment': return 'text-green-400 bg-green-400/20';
        case 'squad_invite': return 'text-amber-400 bg-amber-400/20';
        case 'match': return 'text-pink-400 bg-pink-400/20';
        default: return 'text-muted-foreground bg-muted';
    }
};

const NotificationItem = ({ notification, onMarkRead }) => {
    const Icon = getNotificationIcon(notification.type);
    const colorClass = getNotificationColor(notification.type);

    return (
        <div 
            className={cn(
                "flex items-start gap-3 p-4 rounded-xl transition-colors cursor-pointer",
                notification.read ? "bg-transparent" : "bg-primary/5"
            )}
            onClick={() => !notification.read && onMarkRead(notification.id)}
            data-testid={`notification-${notification.id}`}
        >
            <div className={cn("w-10 h-10 rounded-full flex items-center justify-center shrink-0", colorClass)}>
                <Icon className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
                <p className="font-medium">{notification.title}</p>
                <p className="text-sm text-muted-foreground">{notification.body}</p>
                <p className="text-xs text-muted-foreground mt-1">
                    {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                </p>
            </div>
            {!notification.read && (
                <div className="w-2 h-2 rounded-full bg-primary shrink-0 mt-2" />
            )}
        </div>
    );
};

export default function NotificationsPage() {
    const { api } = useAuth();
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchNotifications();
    }, []);

    const fetchNotifications = async () => {
        try {
            const res = await api.get('/notifications');
            setNotifications(res.data);
        } catch (e) {
            toast.error('Failed to load notifications');
        } finally {
            setLoading(false);
        }
    };

    const handleMarkRead = async (id) => {
        try {
            await api.post(`/notifications/${id}/read`);
            setNotifications(notifications.map(n => 
                n.id === id ? { ...n, read: true } : n
            ));
        } catch (e) {
            console.error('Failed to mark as read');
        }
    };

    const handleMarkAllRead = async () => {
        try {
            await api.post('/notifications/read-all');
            setNotifications(notifications.map(n => ({ ...n, read: true })));
            toast.success('All notifications marked as read');
        } catch (e) {
            toast.error('Failed to mark all as read');
        }
    };

    const unreadCount = notifications.filter(n => !n.read).length;

    return (
        <MainLayout>
            <div className="max-w-2xl mx-auto px-4 py-6 space-y-6" data-testid="notifications-page">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="font-heading text-2xl font-bold">Notifications</h1>
                        {unreadCount > 0 && (
                            <p className="text-sm text-muted-foreground">{unreadCount} unread</p>
                        )}
                    </div>
                    {unreadCount > 0 && (
                        <Button 
                            variant="outline" 
                            size="sm" 
                            className="rounded-full"
                            onClick={handleMarkAllRead}
                            data-testid="mark-all-read-btn"
                        >
                            <CheckCheck className="w-4 h-4 mr-2" />
                            Mark all read
                        </Button>
                    )}
                </div>

                {/* Notifications List */}
                <Card className="glass-card overflow-hidden">
                    {loading ? (
                        <div className="p-4 space-y-4">
                            {[1, 2, 3, 4].map(i => (
                                <div key={i} className="flex items-start gap-3">
                                    <div className="w-10 h-10 rounded-full skeleton-shimmer" />
                                    <div className="flex-1 space-y-2">
                                        <div className="h-4 w-32 skeleton-shimmer rounded" />
                                        <div className="h-3 w-full skeleton-shimmer rounded" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : notifications.length > 0 ? (
                        <ScrollArea className="max-h-[calc(100vh-200px)]">
                            <div className="divide-y divide-border/50">
                                {notifications.map(notification => (
                                    <NotificationItem
                                        key={notification.id}
                                        notification={notification}
                                        onMarkRead={handleMarkRead}
                                    />
                                ))}
                            </div>
                        </ScrollArea>
                    ) : (
                        <div className="p-12 text-center">
                            <Bell className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                            <p className="text-muted-foreground">No notifications yet</p>
                        </div>
                    )}
                </Card>
            </div>
        </MainLayout>
    );
}
