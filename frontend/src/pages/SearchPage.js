import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { MainLayout } from '../components/layout/MainLayout';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Search as SearchIcon, Users, FileText, Hash, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';

export default function SearchPage() {
    const { api, user } = useAuth();
    const [query, setQuery] = useState('');
    const [tab, setTab] = useState('users');
    const [users, setUsers] = useState([]);
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    const handleSearch = async (e) => {
        e?.preventDefault();
        if (!query.trim()) return;
        
        setLoading(true);
        setSearched(true);
        
        try {
            if (tab === 'users') {
                const res = await api.get(`/search/users?q=${encodeURIComponent(query)}`);
                setUsers(res.data);
            } else {
                const res = await api.get(`/search/posts?q=${encodeURIComponent(query)}`);
                setPosts(res.data);
            }
        } catch (e) {
            toast.error('Search failed');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (query && searched) {
            handleSearch();
        }
    }, [tab]);

    return (
        <MainLayout>
            <div className="max-w-2xl mx-auto px-4 py-6 space-y-6" data-testid="search-page">
                {/* Search Input */}
                <form onSubmit={handleSearch} className="relative">
                    <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <Input
                        placeholder="Search users, posts, hashtags..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="pl-12 h-12 rounded-full bg-muted border-0"
                        data-testid="search-input"
                    />
                </form>

                {/* Tabs */}
                <Tabs value={tab} onValueChange={setTab}>
                    <TabsList className="w-full glass">
                        <TabsTrigger value="users" className="flex-1">
                            <Users className="w-4 h-4 mr-2" />
                            Users
                        </TabsTrigger>
                        <TabsTrigger value="posts" className="flex-1">
                            <FileText className="w-4 h-4 mr-2" />
                            Posts
                        </TabsTrigger>
                    </TabsList>

                    {/* Users Results */}
                    <TabsContent value="users" className="mt-6 space-y-2">
                        {loading ? (
                            <div className="space-y-2">
                                {[1, 2, 3].map(i => (
                                    <Card key={i} className="glass-card p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-12 h-12 rounded-full skeleton-shimmer" />
                                            <div className="flex-1 space-y-2">
                                                <div className="h-4 w-32 skeleton-shimmer rounded" />
                                                <div className="h-3 w-24 skeleton-shimmer rounded" />
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        ) : users.length > 0 ? (
                            <div className="space-y-2">
                                {users.map(u => (
                                    <Link key={u.id} to={`/profile/${u.id}`}>
                                        <Card className="glass-card p-4 card-interactive">
                                            <div className="flex items-center gap-3">
                                                <Avatar className="w-12 h-12">
                                                    <AvatarImage src={u.avatar_url} />
                                                    <AvatarFallback className="bg-primary/20 text-primary">
                                                        {u.display_name?.[0]?.toUpperCase()}
                                                    </AvatarFallback>
                                                </Avatar>
                                                <div className="flex-1 min-w-0">
                                                    <p className="font-medium truncate">{u.display_name}</p>
                                                    <p className="text-sm text-muted-foreground truncate">@{u.handle}</p>
                                                    {u.bio && (
                                                        <p className="text-sm text-muted-foreground truncate mt-1">{u.bio}</p>
                                                    )}
                                                </div>
                                            </div>
                                        </Card>
                                    </Link>
                                ))}
                            </div>
                        ) : searched ? (
                            <Card className="glass-card p-8 text-center">
                                <p className="text-muted-foreground">No users found</p>
                            </Card>
                        ) : (
                            <Card className="glass-card p-8 text-center">
                                <SearchIcon className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                                <p className="text-muted-foreground">Search for users by name or handle</p>
                            </Card>
                        )}
                    </TabsContent>

                    {/* Posts Results */}
                    <TabsContent value="posts" className="mt-6 space-y-4">
                        {loading ? (
                            <div className="space-y-4">
                                {[1, 2, 3].map(i => (
                                    <Card key={i} className="glass-card p-4">
                                        <div className="flex gap-3">
                                            <div className="w-10 h-10 rounded-full skeleton-shimmer" />
                                            <div className="flex-1 space-y-2">
                                                <div className="h-4 w-32 skeleton-shimmer rounded" />
                                                <div className="h-3 w-full skeleton-shimmer rounded" />
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        ) : posts.length > 0 ? (
                            <div className="space-y-4">
                                {posts.map(post => (
                                    <Card key={post.id} className="glass-card p-4">
                                        <div className="flex items-start gap-3">
                                            <Avatar className="w-10 h-10">
                                                <AvatarImage src={post.user_avatar} />
                                                <AvatarFallback className="text-sm">
                                                    {post.user_name?.[0]}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div className="flex-1 min-w-0">
                                                <p className="font-medium">{post.user_name}</p>
                                                <p className="text-sm text-muted-foreground">@{post.user_handle}</p>
                                                <p className="mt-2">{post.content}</p>
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        ) : searched ? (
                            <Card className="glass-card p-8 text-center">
                                <p className="text-muted-foreground">No posts found</p>
                            </Card>
                        ) : (
                            <Card className="glass-card p-8 text-center">
                                <Hash className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                                <p className="text-muted-foreground">Search posts by content or hashtags</p>
                            </Card>
                        )}
                    </TabsContent>
                </Tabs>
            </div>
        </MainLayout>
    );
}
