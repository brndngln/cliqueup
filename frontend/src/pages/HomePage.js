import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { MainLayout } from '../components/layout/MainLayout';
import { Button } from '../components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Textarea } from '../components/ui/textarea';
import { Card } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
    Heart, 
    MessageCircle, 
    Share2, 
    Bookmark, 
    MoreHorizontal, 
    Image as ImageIcon,
    Video,
    Smile,
    Send,
    ThumbsUp,
    Laugh,
    Angry,
    Frown
} from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';

const REACTIONS = [
    { type: 'like', icon: ThumbsUp, label: 'Like', color: 'text-blue-400' },
    { type: 'love', icon: Heart, label: 'Love', color: 'text-red-400' },
    { type: 'laugh', icon: Laugh, label: 'Haha', color: 'text-yellow-400' },
    { type: 'wow', icon: Smile, label: 'Wow', color: 'text-yellow-400' },
    { type: 'sad', icon: Frown, label: 'Sad', color: 'text-yellow-400' },
    { type: 'angry', icon: Angry, label: 'Angry', color: 'text-orange-400' },
];

const PostCard = ({ post, onReact }) => {
    const [showReactions, setShowReactions] = useState(false);
    const [showComments, setShowComments] = useState(false);
    const [comment, setComment] = useState('');
    const [comments, setComments] = useState([]);
    const [loadingComments, setLoadingComments] = useState(false);
    const { api } = useAuth();

    const fetchComments = async () => {
        if (showComments && comments.length === 0) {
            setLoadingComments(true);
            try {
                const res = await api.get(`/posts/${post.id}/comments`);
                setComments(res.data);
            } catch (e) {
                console.error('Failed to load comments');
            } finally {
                setLoadingComments(false);
            }
        }
    };

    useEffect(() => {
        if (showComments) fetchComments();
    }, [showComments]);

    const handleComment = async () => {
        if (!comment.trim()) return;
        try {
            const res = await api.post(`/posts/${post.id}/comments`, { content: comment });
            setComments([...comments, res.data]);
            setComment('');
            toast.success('Comment added');
        } catch (e) {
            toast.error('Failed to add comment');
        }
    };

    const getReactionIcon = () => {
        if (!post.user_reaction) return Heart;
        const reaction = REACTIONS.find(r => r.type === post.user_reaction);
        return reaction?.icon || Heart;
    };

    const ReactionIcon = getReactionIcon();

    return (
        <Card className="glass-card p-4 space-y-4 feed-post" data-testid={`post-${post.id}`}>
            {/* Post Header */}
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                    <Avatar className="w-10 h-10">
                        <AvatarImage src={post.user_avatar} alt={post.user_name} />
                        <AvatarFallback className="bg-primary/20 text-primary text-sm">
                            {post.user_name?.[0]?.toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                    <div>
                        <p className="font-medium">{post.user_name}</p>
                        <p className="text-sm text-muted-foreground">
                            @{post.user_handle} · {formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}
                        </p>
                    </div>
                </div>
                <Button variant="ghost" size="icon" className="rounded-full">
                    <MoreHorizontal className="w-5 h-5" />
                </Button>
            </div>

            {/* Post Content */}
            <div className="space-y-3">
                <p className="whitespace-pre-wrap">{post.content}</p>
                {post.media_urls?.length > 0 && (
                    <div className={`grid gap-2 ${post.media_urls.length > 1 ? 'grid-cols-2' : ''}`}>
                        {post.media_urls.map((url, i) => (
                            <img 
                                key={i} 
                                src={url} 
                                alt="" 
                                className="rounded-xl w-full object-cover max-h-96"
                            />
                        ))}
                    </div>
                )}
                {post.tags?.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {post.tags.map((tag, i) => (
                            <span key={i} className="text-primary text-sm">#{tag}</span>
                        ))}
                    </div>
                )}
            </div>

            {/* Post Stats */}
            {(post.reactions_count > 0 || post.comments_count > 0) && (
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    {post.reactions_count > 0 && (
                        <span>{post.reactions_count} reactions</span>
                    )}
                    {post.comments_count > 0 && (
                        <span>{post.comments_count} comments</span>
                    )}
                </div>
            )}

            {/* Post Actions */}
            <div className="flex items-center justify-between pt-2 border-t border-border/50">
                <div className="relative">
                    <Button 
                        variant="ghost" 
                        size="sm" 
                        className={`rounded-full gap-2 ${post.user_reaction ? 'text-primary' : ''}`}
                        onClick={() => setShowReactions(!showReactions)}
                        onMouseEnter={() => setShowReactions(true)}
                        onMouseLeave={() => setTimeout(() => setShowReactions(false), 300)}
                        data-testid={`react-btn-${post.id}`}
                    >
                        <ReactionIcon className={`w-4 h-4 ${post.user_reaction ? 'fill-current' : ''}`} />
                        <span>{post.user_reaction || 'React'}</span>
                    </Button>
                    
                    {showReactions && (
                        <div 
                            className="absolute bottom-full left-0 mb-2 glass rounded-full p-1 flex gap-1 animate-in"
                            onMouseEnter={() => setShowReactions(true)}
                            onMouseLeave={() => setShowReactions(false)}
                        >
                            {REACTIONS.map((reaction) => (
                                <button
                                    key={reaction.type}
                                    onClick={() => {
                                        onReact(post.id, reaction.type);
                                        setShowReactions(false);
                                    }}
                                    className={`p-2 rounded-full hover:bg-accent transition-transform hover:scale-125 ${reaction.color}`}
                                    title={reaction.label}
                                >
                                    <reaction.icon className="w-5 h-5" />
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                <Button 
                    variant="ghost" 
                    size="sm" 
                    className="rounded-full gap-2"
                    onClick={() => setShowComments(!showComments)}
                    data-testid={`comment-btn-${post.id}`}
                >
                    <MessageCircle className="w-4 h-4" />
                    <span>Comment</span>
                </Button>

                <Button variant="ghost" size="sm" className="rounded-full gap-2">
                    <Share2 className="w-4 h-4" />
                    <span className="hidden sm:inline">Share</span>
                </Button>

                <Button variant="ghost" size="sm" className="rounded-full">
                    <Bookmark className="w-4 h-4" />
                </Button>
            </div>

            {/* Comments Section */}
            {showComments && (
                <div className="space-y-3 pt-2 border-t border-border/50 animate-in">
                    {/* Comment Input */}
                    <div className="flex gap-2">
                        <Textarea
                            placeholder="Write a comment..."
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            className="min-h-[60px] resize-none"
                            data-testid={`comment-input-${post.id}`}
                        />
                        <Button 
                            size="icon" 
                            className="rounded-full shrink-0"
                            onClick={handleComment}
                            disabled={!comment.trim()}
                        >
                            <Send className="w-4 h-4" />
                        </Button>
                    </div>

                    {/* Comments List */}
                    {loadingComments ? (
                        <div className="text-center py-4 text-muted-foreground">Loading comments...</div>
                    ) : comments.length > 0 ? (
                        <div className="space-y-3">
                            {comments.map((c) => (
                                <div key={c.id} className="flex gap-2">
                                    <Avatar className="w-8 h-8">
                                        <AvatarImage src={c.user_avatar} />
                                        <AvatarFallback className="text-xs">{c.user_name?.[0]}</AvatarFallback>
                                    </Avatar>
                                    <div className="flex-1 bg-muted rounded-xl px-3 py-2">
                                        <p className="text-sm font-medium">{c.user_name}</p>
                                        <p className="text-sm">{c.content}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-center text-sm text-muted-foreground py-2">No comments yet</p>
                    )}
                </div>
            )}
        </Card>
    );
};

export default function HomePage() {
    const { api, user } = useAuth();
    const [posts, setPosts] = useState([]);
    const [newPost, setNewPost] = useState('');
    const [loading, setLoading] = useState(true);
    const [posting, setPosting] = useState(false);
    const [tab, setTab] = useState('feed');
    const [profile, setProfile] = useState(null);

    useEffect(() => {
        fetchData();
    }, [tab]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const endpoint = tab === 'feed' ? '/posts/feed' : '/posts/explore';
            const [postsRes, profileRes] = await Promise.all([
                api.get(endpoint),
                api.get('/profiles/me')
            ]);
            setPosts(postsRes.data);
            setProfile(profileRes.data);
        } catch (e) {
            toast.error('Failed to load feed');
        } finally {
            setLoading(false);
        }
    };

    const handlePost = async () => {
        if (!newPost.trim()) return;
        setPosting(true);
        try {
            const res = await api.post('/posts', { 
                type: 'text',
                content: newPost 
            });
            setPosts([res.data, ...posts]);
            setNewPost('');
            toast.success('Posted!');
        } catch (e) {
            toast.error('Failed to post');
        } finally {
            setPosting(false);
        }
    };

    const handleReact = async (postId, reactionType) => {
        try {
            await api.post(`/posts/${postId}/react`, { reaction_type: reactionType });
            setPosts(posts.map(p => {
                if (p.id === postId) {
                    const wasReacted = p.user_reaction === reactionType;
                    return {
                        ...p,
                        user_reaction: wasReacted ? null : reactionType,
                        reactions_count: p.reactions_count + (wasReacted ? -1 : (p.user_reaction ? 0 : 1))
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
            <div className="max-w-2xl mx-auto px-4 py-6 space-y-6" data-testid="home-page">
                {/* Create Post */}
                <Card className="glass-card p-4 space-y-4">
                    <div className="flex gap-3">
                        <Avatar className="w-10 h-10">
                            <AvatarImage src={profile?.avatar_url} />
                            <AvatarFallback className="bg-primary/20 text-primary">
                                {user?.display_name?.[0]?.toUpperCase()}
                            </AvatarFallback>
                        </Avatar>
                        <Textarea
                            placeholder="What's on your mind?"
                            value={newPost}
                            onChange={(e) => setNewPost(e.target.value)}
                            className="flex-1 min-h-[80px] resize-none bg-muted border-0"
                            data-testid="create-post-input"
                        />
                    </div>
                    <div className="flex items-center justify-between">
                        <div className="flex gap-2">
                            <Button variant="ghost" size="sm" className="rounded-full text-muted-foreground">
                                <ImageIcon className="w-4 h-4 mr-2" />
                                Photo
                            </Button>
                            <Button variant="ghost" size="sm" className="rounded-full text-muted-foreground">
                                <Video className="w-4 h-4 mr-2" />
                                Video
                            </Button>
                        </div>
                        <Button 
                            className="rounded-full"
                            onClick={handlePost}
                            disabled={!newPost.trim() || posting}
                            data-testid="post-btn"
                        >
                            {posting ? 'Posting...' : 'Post'}
                        </Button>
                    </div>
                </Card>

                {/* Feed Tabs */}
                <Tabs value={tab} onValueChange={setTab} className="w-full">
                    <TabsList className="w-full glass">
                        <TabsTrigger value="feed" className="flex-1" data-testid="feed-tab">
                            Following
                        </TabsTrigger>
                        <TabsTrigger value="explore" className="flex-1" data-testid="explore-tab">
                            Explore
                        </TabsTrigger>
                    </TabsList>
                </Tabs>

                {/* Posts */}
                {loading ? (
                    <div className="space-y-4">
                        {[1, 2, 3].map((i) => (
                            <Card key={i} className="glass-card p-4 space-y-4">
                                <div className="flex gap-3">
                                    <div className="w-10 h-10 rounded-full skeleton-shimmer" />
                                    <div className="flex-1 space-y-2">
                                        <div className="h-4 w-32 skeleton-shimmer rounded" />
                                        <div className="h-3 w-24 skeleton-shimmer rounded" />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <div className="h-4 w-full skeleton-shimmer rounded" />
                                    <div className="h-4 w-3/4 skeleton-shimmer rounded" />
                                </div>
                            </Card>
                        ))}
                    </div>
                ) : posts.length > 0 ? (
                    <div className="space-y-4">
                        {posts.map((post) => (
                            <PostCard key={post.id} post={post} onReact={handleReact} />
                        ))}
                    </div>
                ) : (
                    <Card className="glass-card p-8 text-center">
                        <p className="text-muted-foreground">
                            {tab === 'feed' 
                                ? "No posts yet. Follow some people to see their posts!" 
                                : "No posts to explore yet. Be the first to post!"}
                        </p>
                    </Card>
                )}
            </div>
        </MainLayout>
    );
}
