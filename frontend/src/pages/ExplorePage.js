import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MainLayout } from '../components/layout/MainLayout';
import { Card } from '../components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
    TrendingUp, 
    Flame, 
    Clock, 
    Heart, 
    MessageCircle, 
    Share2,
    Play
} from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';

export default function ExplorePage() {
    const { api, user } = useAuth();
    const [tab, setTab] = useState('trending');
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchPosts();
    }, [tab]);

    const fetchPosts = async () => {
        setLoading(true);
        try {
            const res = await api.get('/posts/explore?limit=30');
            setPosts(res.data);
        } catch (e) {
            toast.error('Failed to load content');
        } finally {
            setLoading(false);
        }
    };

    const handleReact = async (postId) => {
        try {
            await api.post(`/posts/${postId}/react`, { reaction_type: 'like' });
            setPosts(posts.map(p => {
                if (p.id === postId) {
                    const wasLiked = p.user_reaction === 'like';
                    return {
                        ...p,
                        user_reaction: wasLiked ? null : 'like',
                        reactions_count: p.reactions_count + (wasLiked ? -1 : 1)
                    };
                }
                return p;
            }));
        } catch (e) {
            toast.error('Failed to react');
        }
    };

    return (
        <MainLayout>
            <div className="max-w-4xl mx-auto px-4 py-6 space-y-6" data-testid="explore-page">
                {/* Header */}
                <div>
                    <h1 className="font-heading text-2xl font-bold">Explore</h1>
                    <p className="text-sm text-muted-foreground">Discover what's trending</p>
                </div>

                {/* Tabs */}
                <Tabs value={tab} onValueChange={setTab}>
                    <TabsList className="glass">
                        <TabsTrigger value="trending">
                            <TrendingUp className="w-4 h-4 mr-2" />
                            Trending
                        </TabsTrigger>
                        <TabsTrigger value="latest">
                            <Clock className="w-4 h-4 mr-2" />
                            Latest
                        </TabsTrigger>
                    </TabsList>
                </Tabs>

                {/* Content Grid */}
                {loading ? (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {[1, 2, 3, 4, 5, 6].map(i => (
                            <div key={i} className="aspect-square skeleton-shimmer rounded-xl" />
                        ))}
                    </div>
                ) : posts.length > 0 ? (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {posts.map((post, index) => (
                            <Card 
                                key={post.id} 
                                className={`glass-card overflow-hidden group cursor-pointer ${
                                    index === 0 ? 'md:col-span-2 md:row-span-2' : ''
                                }`}
                            >
                                <div className="relative aspect-square">
                                    {post.media_urls?.[0] ? (
                                        <img 
                                            src={post.media_urls[0]} 
                                            alt="" 
                                            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                                        />
                                    ) : (
                                        <div className="w-full h-full bg-gradient-to-br from-indigo-500/20 to-pink-500/20 flex items-center justify-center p-4">
                                            <p className="text-sm text-center line-clamp-6">{post.content}</p>
                                        </div>
                                    )}
                                    
                                    {/* Overlay on hover */}
                                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-6">
                                        <button 
                                            className="flex items-center gap-1 text-white"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleReact(post.id);
                                            }}
                                        >
                                            <Heart className={`w-5 h-5 ${post.user_reaction === 'like' ? 'fill-white' : ''}`} />
                                            <span>{post.reactions_count}</span>
                                        </button>
                                        <div className="flex items-center gap-1 text-white">
                                            <MessageCircle className="w-5 h-5" />
                                            <span>{post.comments_count}</span>
                                        </div>
                                    </div>
                                    
                                    {/* Video indicator */}
                                    {post.type === 'video' && (
                                        <div className="absolute top-2 right-2">
                                            <Play className="w-5 h-5 text-white drop-shadow-lg" />
                                        </div>
                                    )}
                                </div>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <Card className="glass-card p-12 text-center">
                        <TrendingUp className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                        <p className="text-muted-foreground">No content to explore yet</p>
                    </Card>
                )}
            </div>
        </MainLayout>
    );
}
