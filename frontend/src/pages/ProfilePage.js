import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MainLayout } from '../components/layout/MainLayout';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { 
    Settings, 
    Edit2, 
    Camera,
    MapPin,
    Link as LinkIcon,
    Calendar,
    Heart,
    Users,
    Grid3X3,
    Bookmark,
    Copy,
    Check,
    Shield,
    Sparkles
} from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

export default function ProfilePage() {
    const { userId } = useParams();
    const { api, user, isAdult, canAccessMeet } = useAuth();
    const [profile, setProfile] = useState(null);
    const [datingProfile, setDatingProfile] = useState(null);
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isOwnProfile, setIsOwnProfile] = useState(false);
    const [isFollowing, setIsFollowing] = useState(false);
    const [showEdit, setShowEdit] = useState(false);
    const [showDatingEdit, setShowDatingEdit] = useState(false);
    const [copied, setCopied] = useState(false);
    const [tab, setTab] = useState('posts');

    // Edit form state
    const [editForm, setEditForm] = useState({
        display_name: '',
        bio: '',
        handle: '',
    });

    const [datingForm, setDatingForm] = useState({
        intent: '',
        bio: '',
    });

    const targetUserId = userId || user?.id;

    useEffect(() => {
        if (targetUserId) {
            fetchProfile();
        }
    }, [targetUserId]);

    const fetchProfile = async () => {
        setLoading(true);
        try {
            const profileRes = await api.get(`/profiles/${targetUserId}`);
            setProfile(profileRes.data);
            setIsOwnProfile(targetUserId === user?.id);
            
            if (targetUserId === user?.id) {
                setEditForm({
                    display_name: profileRes.data.display_name || '',
                    bio: profileRes.data.bio || '',
                    handle: profileRes.data.handle || '',
                });
            } else {
                // Check if following
                try {
                    const followingRes = await api.get(`/profiles/${user?.id}/following`);
                    setIsFollowing(followingRes.data.some(p => p.user_id === targetUserId));
                } catch (e) {}
            }

            // Fetch dating profile if adult
            if (isAdult && canAccessMeet) {
                try {
                    const datingRes = await api.get(`/meet/dating-profile/${targetUserId}`);
                    setDatingProfile(datingRes.data);
                    if (targetUserId === user?.id) {
                        setDatingForm({
                            intent: datingRes.data.intent || '',
                            bio: datingRes.data.bio || '',
                        });
                    }
                } catch (e) {
                    // No dating profile
                }
            }

            // Fetch posts (would need endpoint for user posts)
            // For now, using explore as placeholder
            try {
                const postsRes = await api.get('/posts/explore?limit=9');
                setPosts(postsRes.data.filter(p => p.user_id === targetUserId));
            } catch (e) {}

        } catch (e) {
            toast.error('Failed to load profile');
        } finally {
            setLoading(false);
        }
    };

    const handleFollow = async () => {
        try {
            if (isFollowing) {
                await api.delete(`/profiles/${targetUserId}/follow`);
                setIsFollowing(false);
                setProfile(p => ({ ...p, followers_count: p.followers_count - 1 }));
            } else {
                await api.post(`/profiles/${targetUserId}/follow`);
                setIsFollowing(true);
                setProfile(p => ({ ...p, followers_count: p.followers_count + 1 }));
            }
        } catch (e) {
            toast.error('Failed to update follow');
        }
    };

    const handleSaveProfile = async () => {
        try {
            const res = await api.put('/profiles/me', editForm);
            setProfile(res.data);
            setShowEdit(false);
            toast.success('Profile updated!');
        } catch (e) {
            toast.error(e.response?.data?.detail || 'Failed to update');
        }
    };

    const handleSaveDatingProfile = async () => {
        try {
            const res = await api.post('/meet/dating-profile', datingForm);
            setDatingProfile(res.data);
            setShowDatingEdit(false);
            toast.success('Dating profile updated!');
        } catch (e) {
            toast.error(e.response?.data?.detail || 'Failed to update');
        }
    };

    const copyUserId = () => {
        navigator.clipboard.writeText(user?.id || '');
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
        toast.success('User ID copied!');
    };

    if (loading) {
        return (
            <MainLayout>
                <div className="max-w-2xl mx-auto px-4 py-6">
                    <div className="space-y-6">
                        <div className="h-32 skeleton-shimmer rounded-xl" />
                        <div className="flex gap-4">
                            <div className="w-24 h-24 rounded-full skeleton-shimmer" />
                            <div className="flex-1 space-y-2">
                                <div className="h-6 w-32 skeleton-shimmer rounded" />
                                <div className="h-4 w-24 skeleton-shimmer rounded" />
                            </div>
                        </div>
                    </div>
                </div>
            </MainLayout>
        );
    }

    return (
        <MainLayout>
            <div className="max-w-2xl mx-auto px-4 py-6 space-y-6" data-testid="profile-page">
                {/* Cover & Avatar */}
                <div className="relative">
                    {/* Cover */}
                    <div className="h-32 md:h-48 rounded-xl bg-gradient-to-br from-pink-600/30 via-gray-500/20 to-teal-600/30 overflow-hidden">
                        {profile?.cover_url && (
                            <img src={profile.cover_url} alt="" className="w-full h-full object-cover" />
                        )}
                    </div>
                    
                    {/* Avatar */}
                    <div className="absolute -bottom-12 left-4">
                        <Avatar className="w-24 h-24 border-4 border-background">
                            <AvatarImage src={profile?.avatar_url} />
                            <AvatarFallback className="bg-primary/20 text-primary text-2xl font-bold">
                                {profile?.display_name?.[0]?.toUpperCase()}
                            </AvatarFallback>
                        </Avatar>
                    </div>

                    {/* Actions */}
                    <div className="absolute -bottom-12 right-4 flex gap-2">
                        {isOwnProfile ? (
                            <>
                                <Dialog open={showEdit} onOpenChange={setShowEdit}>
                                    <DialogTrigger asChild>
                                        <Button variant="outline" className="rounded-full" data-testid="edit-profile-btn">
                                            <Edit2 className="w-4 h-4 mr-2" />
                                            Edit Profile
                                        </Button>
                                    </DialogTrigger>
                                    <DialogContent>
                                        <DialogHeader>
                                            <DialogTitle>Edit Profile</DialogTitle>
                                        </DialogHeader>
                                        <div className="space-y-4 py-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="displayName">Display Name</Label>
                                                <Input
                                                    id="displayName"
                                                    value={editForm.display_name}
                                                    onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="handle">Username</Label>
                                                <Input
                                                    id="handle"
                                                    value={editForm.handle}
                                                    onChange={(e) => setEditForm({ ...editForm, handle: e.target.value })}
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="bio">Bio</Label>
                                                <Textarea
                                                    id="bio"
                                                    value={editForm.bio}
                                                    onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                                                    rows={3}
                                                />
                                            </div>
                                        </div>
                                        <DialogFooter>
                                            <Button variant="outline" onClick={() => setShowEdit(false)}>Cancel</Button>
                                            <Button onClick={handleSaveProfile}>Save</Button>
                                        </DialogFooter>
                                    </DialogContent>
                                </Dialog>
                                <Link to="/settings">
                                    <Button variant="ghost" size="icon" className="rounded-full">
                                        <Settings className="w-5 h-5" />
                                    </Button>
                                </Link>
                            </>
                        ) : (
                            <>
                                <Button 
                                    className={`rounded-full ${isFollowing ? 'bg-gray-700 text-foreground' : 'bg-teal-600 hover:bg-teal-700'}`}
                                    onClick={handleFollow}
                                    data-testid="follow-btn"
                                >
                                    {isFollowing ? 'Following' : 'Follow'}
                                </Button>
                                <Link to={`/messages`}>
                                    <Button variant="outline" className="rounded-full border-pink-600 text-pink-400 hover:bg-pink-600/10">
                                        Message
                                    </Button>
                                </Link>
                            </>
                        )}
                    </div>
                </div>

                {/* Profile Info */}
                <div className="pt-14 space-y-4">
                    <div>
                        <h1 className="font-heading text-2xl font-bold">{profile?.display_name}</h1>
                        <p className="text-muted-foreground">@{profile?.handle}</p>
                    </div>

                    {profile?.bio && (
                        <p className="text-foreground">{profile.bio}</p>
                    )}

                    {/* Stats */}
                    <div className="flex gap-6">
                        <div className="text-center">
                            <p className="font-bold text-teal-400">{posts.length}</p>
                            <p className="text-sm text-muted-foreground">Posts</p>
                        </div>
                        <Link to={`/profile/${targetUserId}/followers`} className="text-center hover:text-pink-400 transition-colors">
                            <p className="font-bold text-pink-400">{profile?.followers_count || 0}</p>
                            <p className="text-sm text-muted-foreground">Followers</p>
                        </Link>
                        <Link to={`/profile/${targetUserId}/following`} className="text-center hover:text-teal-400 transition-colors">
                            <p className="font-bold text-teal-400">{profile?.following_count || 0}</p>
                            <p className="text-sm text-muted-foreground">Following</p>
                        </Link>
                    </div>

                    {/* User ID for invites (only show on own profile) */}
                    {isOwnProfile && (
                        <Card className="glass-card p-4 border-teal-600/20">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-teal-400">Your User ID (for squad invites)</p>
                                    <p className="font-mono text-sm truncate max-w-[200px]">{user?.id}</p>
                                </div>
                                <Button variant="outline" size="sm" className="rounded-full border-teal-600 text-teal-400 hover:bg-teal-600/10" onClick={copyUserId}>
                                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                </Button>
                            </div>
                        </Card>
                    )}
                </div>

                {/* Tabs */}
                <Tabs value={tab} onValueChange={setTab}>
                    <TabsList className="w-full glass">
                        <TabsTrigger value="posts" className="flex-1">
                            <Grid3X3 className="w-4 h-4 mr-2" />
                            Posts
                        </TabsTrigger>
                        {isAdult && canAccessMeet && (
                            <TabsTrigger value="dating" className="flex-1">
                                <Heart className="w-4 h-4 mr-2" />
                                Dating
                            </TabsTrigger>
                        )}
                    </TabsList>

                    <TabsContent value="posts" className="mt-6">
                        {posts.length > 0 ? (
                            <div className="grid grid-cols-3 gap-1">
                                {posts.map(post => (
                                    <div key={post.id} className="aspect-square bg-muted rounded-lg overflow-hidden">
                                        {post.media_urls?.[0] ? (
                                            <img src={post.media_urls[0]} alt="" className="w-full h-full object-cover" />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center p-2">
                                                <p className="text-xs text-center line-clamp-4">{post.content}</p>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <Card className="glass-card p-8 text-center">
                                <p className="text-muted-foreground">No posts yet</p>
                            </Card>
                        )}
                    </TabsContent>

                    {isAdult && canAccessMeet && (
                        <TabsContent value="dating" className="mt-6 space-y-4">
                            {datingProfile ? (
                                <Card className="glass-card p-6 space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h3 className="font-heading text-lg font-semibold">Dating Profile</h3>
                                        {isOwnProfile && (
                                            <Dialog open={showDatingEdit} onOpenChange={setShowDatingEdit}>
                                                <DialogTrigger asChild>
                                                    <Button variant="ghost" size="sm" className="rounded-full">
                                                        <Edit2 className="w-4 h-4" />
                                                    </Button>
                                                </DialogTrigger>
                                                <DialogContent>
                                                    <DialogHeader>
                                                        <DialogTitle>Edit Dating Profile</DialogTitle>
                                                    </DialogHeader>
                                                    <div className="space-y-4 py-4">
                                                        <div className="space-y-2">
                                                            <Label htmlFor="intent">Looking for</Label>
                                                            <Input
                                                                id="intent"
                                                                placeholder="e.g., Serious, Casual, Friends"
                                                                value={datingForm.intent}
                                                                onChange={(e) => setDatingForm({ ...datingForm, intent: e.target.value })}
                                                            />
                                                        </div>
                                                        <div className="space-y-2">
                                                            <Label htmlFor="datingBio">Dating Bio</Label>
                                                            <Textarea
                                                                id="datingBio"
                                                                value={datingForm.bio}
                                                                onChange={(e) => setDatingForm({ ...datingForm, bio: e.target.value })}
                                                                rows={3}
                                                            />
                                                        </div>
                                                    </div>
                                                    <DialogFooter>
                                                        <Button variant="outline" onClick={() => setShowDatingEdit(false)}>Cancel</Button>
                                                        <Button onClick={handleSaveDatingProfile}>Save</Button>
                                                    </DialogFooter>
                                                </DialogContent>
                                            </Dialog>
                                        )}
                                    </div>

                                    {datingProfile.intent && (
                                        <div className="flex items-center gap-2">
                                            <Badge className="bg-pink-500/20 text-pink-400 border-0">
                                                <Heart className="w-3 h-3 mr-1" />
                                                {datingProfile.intent}
                                            </Badge>
                                        </div>
                                    )}

                                    {datingProfile.bio && (
                                        <p>{datingProfile.bio}</p>
                                    )}

                                    <div className="flex gap-2">
                                        {datingProfile.photo_verified && (
                                            <Badge variant="outline" className="gap-1">
                                                <Camera className="w-3 h-3" />
                                                Photo Verified
                                            </Badge>
                                        )}
                                        {datingProfile.id_verified && (
                                            <Badge variant="outline" className="gap-1">
                                                <Shield className="w-3 h-3" />
                                                ID Verified
                                            </Badge>
                                        )}
                                    </div>
                                </Card>
                            ) : isOwnProfile ? (
                                <Card className="glass-card p-8 text-center space-y-4">
                                    <Sparkles className="w-12 h-12 mx-auto text-pink-400" />
                                    <h3 className="font-heading text-xl font-semibold">Create Dating Profile</h3>
                                    <p className="text-muted-foreground">Set up your dating profile to start matching with squads</p>
                                    <Button 
                                        className="rounded-full"
                                        onClick={() => setShowDatingEdit(true)}
                                    >
                                        Get Started
                                    </Button>
                                </Card>
                            ) : (
                                <Card className="glass-card p-8 text-center">
                                    <p className="text-muted-foreground">No dating profile</p>
                                </Card>
                            )}
                        </TabsContent>
                    )}
                </Tabs>
            </div>
        </MainLayout>
    );
}
