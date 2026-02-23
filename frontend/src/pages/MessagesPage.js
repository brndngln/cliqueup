import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MainLayout } from '../components/layout/MainLayout';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Input } from '../components/ui/input';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
    ArrowLeft, 
    Send, 
    MoreVertical,
    Phone,
    Video,
    Info,
    Image as ImageIcon
} from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '../lib/utils';

// Conversation List Item
const ConversationItem = ({ conversation, isActive, onClick }) => {
    const { user } = useAuth();
    
    // Get the other user(s) for display
    const otherMembers = conversation.members.filter(m => m.user_id !== user?.id);
    const displayName = conversation.name || otherMembers.map(m => m.display_name).join(', ') || 'Unknown';
    const displayAvatar = otherMembers[0]?.avatar_url;
    
    return (
        <div 
            className={cn(
                "flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors",
                isActive ? "bg-primary/10" : "hover:bg-accent"
            )}
            onClick={onClick}
            data-testid={`conversation-${conversation.id}`}
        >
            <Avatar className="w-12 h-12">
                <AvatarImage src={displayAvatar} />
                <AvatarFallback className="bg-primary/20 text-primary">
                    {displayName?.[0]?.toUpperCase()}
                </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                    <p className="font-medium truncate">{displayName}</p>
                    {conversation.last_message && (
                        <span className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(conversation.last_message.created_at), { addSuffix: false })}
                        </span>
                    )}
                </div>
                {conversation.last_message && (
                    <p className="text-sm text-muted-foreground truncate">
                        {conversation.last_message.body}
                    </p>
                )}
            </div>
        </div>
    );
};

// Message Bubble
const MessageBubble = ({ message, isOwn }) => {
    return (
        <div className={cn(
            "flex gap-2 max-w-[80%]",
            isOwn ? "ml-auto flex-row-reverse" : ""
        )}>
            {!isOwn && (
                <Avatar className="w-8 h-8 shrink-0">
                    <AvatarImage src={message.sender_avatar} />
                    <AvatarFallback className="text-xs">{message.sender_name?.[0]}</AvatarFallback>
                </Avatar>
            )}
            <div className={cn(
                "rounded-2xl px-4 py-2",
                isOwn ? "message-bubble-own text-white" : "message-bubble-other"
            )}>
                {!isOwn && (
                    <p className="text-xs font-medium mb-1 opacity-70">{message.sender_name}</p>
                )}
                <p className="text-sm">{message.body}</p>
                <p className={cn(
                    "text-xs mt-1",
                    isOwn ? "text-white/60" : "text-muted-foreground"
                )}>
                    {formatDistanceToNow(new Date(message.created_at), { addSuffix: true })}
                </p>
            </div>
        </div>
    );
};

export default function MessagesPage() {
    const { conversationId } = useParams();
    const { api, user } = useAuth();
    const navigate = useNavigate();
    const messagesEndRef = useRef(null);
    
    const [conversations, setConversations] = useState([]);
    const [activeConversation, setActiveConversation] = useState(null);
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);

    useEffect(() => {
        fetchConversations();
    }, []);

    useEffect(() => {
        if (conversationId) {
            fetchConversation(conversationId);
            fetchMessages(conversationId);
        }
    }, [conversationId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Polling for new messages
    useEffect(() => {
        if (!conversationId) return;
        
        const interval = setInterval(() => {
            fetchMessages(conversationId, true);
        }, 5000);
        
        return () => clearInterval(interval);
    }, [conversationId]);

    const fetchConversations = async () => {
        try {
            const res = await api.get('/conversations');
            setConversations(res.data);
        } catch (e) {
            console.error('Failed to fetch conversations');
        } finally {
            setLoading(false);
        }
    };

    const fetchConversation = async (id) => {
        try {
            const res = await api.get(`/conversations/${id}`);
            setActiveConversation(res.data);
        } catch (e) {
            toast.error('Failed to load conversation');
        }
    };

    const fetchMessages = async (id, silent = false) => {
        try {
            const res = await api.get(`/conversations/${id}/messages`);
            setMessages(res.data);
        } catch (e) {
            if (!silent) toast.error('Failed to load messages');
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSend = async (e) => {
        e.preventDefault();
        if (!newMessage.trim() || !conversationId) return;
        
        setSending(true);
        try {
            const res = await api.post(`/conversations/${conversationId}/messages`, {
                body: newMessage
            });
            setMessages([...messages, res.data]);
            setNewMessage('');
        } catch (e) {
            toast.error('Failed to send message');
        } finally {
            setSending(false);
        }
    };

    const selectConversation = (conv) => {
        navigate(`/messages/${conv.id}`);
    };

    const otherMembers = activeConversation?.members.filter(m => m.user_id !== user?.id) || [];
    const chatName = activeConversation?.name || otherMembers.map(m => m.display_name).join(', ') || 'Chat';

    return (
        <MainLayout>
            <div className="h-[calc(100vh-64px)] md:h-[calc(100vh-64px)] flex" data-testid="messages-page">
                {/* Conversations List - Hidden on mobile when viewing a chat */}
                <div className={cn(
                    "w-full md:w-80 border-r border-border/50 flex flex-col",
                    conversationId ? "hidden md:flex" : "flex"
                )}>
                    <div className="p-4 border-b border-border/50">
                        <h1 className="font-heading text-xl font-bold">Messages</h1>
                    </div>
                    
                    <ScrollArea className="flex-1">
                        <div className="p-2 space-y-1">
                            {loading ? (
                                <div className="space-y-2 p-2">
                                    {[1, 2, 3].map(i => (
                                        <div key={i} className="flex items-center gap-3 p-3">
                                            <div className="w-12 h-12 rounded-full skeleton-shimmer" />
                                            <div className="flex-1 space-y-2">
                                                <div className="h-4 w-24 skeleton-shimmer rounded" />
                                                <div className="h-3 w-32 skeleton-shimmer rounded" />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : conversations.length > 0 ? (
                                conversations.map(conv => (
                                    <ConversationItem
                                        key={conv.id}
                                        conversation={conv}
                                        isActive={conv.id === conversationId}
                                        onClick={() => selectConversation(conv)}
                                    />
                                ))
                            ) : (
                                <div className="p-8 text-center text-muted-foreground">
                                    <p>No conversations yet</p>
                                </div>
                            )}
                        </div>
                    </ScrollArea>
                </div>

                {/* Chat View */}
                <div className={cn(
                    "flex-1 flex flex-col",
                    !conversationId ? "hidden md:flex" : "flex"
                )}>
                    {conversationId && activeConversation ? (
                        <>
                            {/* Chat Header */}
                            <div className="h-16 px-4 border-b border-border/50 flex items-center justify-between glass">
                                <div className="flex items-center gap-3">
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="md:hidden rounded-full"
                                        onClick={() => navigate('/messages')}
                                    >
                                        <ArrowLeft className="w-5 h-5" />
                                    </Button>
                                    <div className="avatar-stack">
                                        {otherMembers.slice(0, 3).map((m, i) => (
                                            <Avatar key={i} className="w-9 h-9 border-2 border-background">
                                                <AvatarImage src={m.avatar_url} />
                                                <AvatarFallback className="text-xs">{m.display_name?.[0]}</AvatarFallback>
                                            </Avatar>
                                        ))}
                                    </div>
                                    <div>
                                        <p className="font-medium">{chatName}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {otherMembers.length} {otherMembers.length === 1 ? 'member' : 'members'}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1">
                                    <Button variant="ghost" size="icon" className="rounded-full">
                                        <Phone className="w-5 h-5" />
                                    </Button>
                                    <Button variant="ghost" size="icon" className="rounded-full">
                                        <Video className="w-5 h-5" />
                                    </Button>
                                    <Button variant="ghost" size="icon" className="rounded-full">
                                        <Info className="w-5 h-5" />
                                    </Button>
                                </div>
                            </div>

                            {/* Messages */}
                            <ScrollArea className="flex-1 p-4">
                                <div className="space-y-4">
                                    {messages.map(msg => (
                                        <MessageBubble
                                            key={msg.id}
                                            message={msg}
                                            isOwn={msg.sender_id === user?.id}
                                        />
                                    ))}
                                    <div ref={messagesEndRef} />
                                </div>
                            </ScrollArea>

                            {/* Message Input */}
                            <form onSubmit={handleSend} className="p-4 border-t border-border/50">
                                <div className="flex items-center gap-2">
                                    <Button type="button" variant="ghost" size="icon" className="rounded-full shrink-0">
                                        <ImageIcon className="w-5 h-5" />
                                    </Button>
                                    <Input
                                        placeholder="Type a message..."
                                        value={newMessage}
                                        onChange={(e) => setNewMessage(e.target.value)}
                                        className="flex-1 rounded-full bg-muted border-0"
                                        data-testid="message-input"
                                    />
                                    <Button 
                                        type="submit" 
                                        size="icon" 
                                        className="rounded-full shrink-0"
                                        disabled={!newMessage.trim() || sending}
                                        data-testid="send-message-btn"
                                    >
                                        <Send className="w-5 h-5" />
                                    </Button>
                                </div>
                            </form>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-muted-foreground">
                            <p>Select a conversation to start messaging</p>
                        </div>
                    )}
                </div>
            </div>
        </MainLayout>
    );
}
