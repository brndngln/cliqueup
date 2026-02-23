import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { ScrollArea } from '../components/ui/scroll-area';
import { 
    Heart, 
    Users, 
    Plus, 
    Check, 
    X, 
    ChevronRight, 
    Sparkles,
    Shield,
    AlertCircle,
    Crown,
    ThumbsUp,
    ThumbsDown,
    Ban,
    MessageCircle,
    UserPlus
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

// Squad Card for Discovery
const SquadDiscoveryCard = ({ squad, onSwipe, onVote }) => {
    const [currentMember, setCurrentMember] = useState(0);
    
    const member = squad.members[currentMember];
    
    return (
        <Card className="glass-card overflow-hidden relative" data-testid={`discovery-squad-${squad.id}`}>
            {/* Member Image */}
            <div className="aspect-[3/4] relative">
                {member?.photos?.[0] ? (
                    <img 
                        src={member.photos[0]} 
                        alt={member.display_name}
                        className="w-full h-full object-cover"
                    />
                ) : member?.avatar_url ? (
                    <img 
                        src={member.avatar_url} 
                        alt={member.display_name}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-teal-600/20 to-pink-600/20 flex items-center justify-center">
                        <Users className="w-20 h-20 text-muted-foreground" />
                    </div>
                )}
                
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                
                {/* Squad indicator */}
                <div className="absolute top-4 left-4 flex items-center gap-2">
                    <Badge className="bg-teal-600/80 text-white border-0">
                        <Users className="w-3 h-3 mr-1" />
                        {squad.member_count} members
                    </Badge>
                </div>
                
                {/* Member dots */}
                <div className="absolute top-4 right-4 flex gap-1">
                    {squad.members.map((_, i) => (
                        <button
                            key={i}
                            onClick={() => setCurrentMember(i)}
                            className={cn(
                                "w-2 h-2 rounded-full transition-colors",
                                i === currentMember ? "bg-white" : "bg-white/40"
                            )}
                        />
                    ))}
                </div>
                
                {/* Member info */}
                <div className="absolute bottom-0 left-0 right-0 p-4">
                    <h3 className="font-heading text-xl font-bold text-white">{squad.name}</h3>
                    <p className="text-white/80 text-sm mt-1">
                        {member?.display_name} {member?.bio && `• ${member.bio.slice(0, 50)}...`}
                    </p>
                </div>
            </div>
            
            {/* Actions */}
            <div className="p-4 flex items-center justify-center gap-4">
                <Button 
                    size="lg" 
                    variant="outline" 
                    className="rounded-full w-14 h-14 p-0 border-gray-500 text-gray-400 hover:bg-gray-600 hover:text-white"
                    onClick={() => onSwipe(squad.id, 'pass')}
                    data-testid={`pass-btn-${squad.id}`}
                >
                    <X className="w-6 h-6" />
                </Button>
                <Button 
                    size="lg" 
                    className="rounded-full w-16 h-16 p-0 bg-gradient-to-r from-pink-600 to-pink-700 hover:from-pink-700 hover:to-pink-800 neon-glow-pink"
                    onClick={() => onSwipe(squad.id, 'like')}
                    data-testid={`like-btn-${squad.id}`}
                >
                    <Heart className="w-7 h-7" />
                </Button>
                <Button 
                    size="lg" 
                    variant="outline" 
                    className="rounded-full w-14 h-14 p-0 border-teal-600 text-teal-400 hover:bg-teal-600 hover:text-white"
                    onClick={() => onSwipe(squad.id, 'like')}
                >
                    <Sparkles className="w-6 h-6" />
                </Button>
            </div>
        </Card>
    );
};

// My Squad Card
const MySquadCard = ({ squad, onViewDetails }) => {
    return (
        <Card 
            className="glass-card p-4 cursor-pointer card-interactive"
            onClick={() => onViewDetails(squad)}
            data-testid={`my-squad-${squad.id}`}
        >
            <div className="flex items-center gap-4">
                {/* Squad avatars stacked */}
                <div className="avatar-stack">
                    {squad.members.slice(0, 3).map((member, i) => (
                        <Avatar key={i} className="w-10 h-10 border-2 border-background">
                            <AvatarImage src={member.avatar_url} />
                            <AvatarFallback className="bg-primary/20 text-primary text-xs">
                                {member.display_name?.[0]}
                            </AvatarFallback>
                        </Avatar>
                    ))}
                    {squad.member_count > 3 && (
                        <div className="w-10 h-10 rounded-full bg-muted border-2 border-background flex items-center justify-center text-xs font-medium">
                            +{squad.member_count - 3}
                        </div>
                    )}
                </div>
                
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <h3 className="font-semibold truncate">{squad.name}</h3>
                        {squad.owner_id === squad.members[0]?.user_id && (
                            <Crown className="w-4 h-4 text-amber-400 shrink-0" />
                        )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                        {squad.member_count} members
                    </p>
                </div>
                
                <ChevronRight className="w-5 h-5 text-muted-foreground" />
            </div>
        </Card>
    );
};

// Match Card
const MatchCard = ({ match, onClick }) => {
    return (
        <Card 
            className="glass-card p-4 cursor-pointer card-interactive"
            onClick={() => onClick(match)}
            data-testid={`match-${match.id}`}
        >
            <div className="flex items-center gap-4">
                <div className="avatar-stack">
                    {match.members.slice(0, 4).map((member, i) => (
                        <Avatar key={i} className="w-10 h-10 border-2 border-background">
                            <AvatarImage src={member.avatar_url} />
                            <AvatarFallback className="bg-teal-600/20 text-teal-400 text-xs">
                                {member.display_name?.[0]}
                            </AvatarFallback>
                        </Avatar>
                    ))}
                </div>
                
                <div className="flex-1 min-w-0">
                    <h3 className="font-semibold truncate">
                        {match.squad_a_name} & {match.squad_b_name}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                        Matched {new Date(match.matched_at).toLocaleDateString()}
                    </p>
                </div>
                
                <Button variant="ghost" size="icon" className="rounded-full shrink-0 text-teal-400 hover:text-teal-300">
                    <MessageCircle className="w-5 h-5" />
                </Button>
            </div>
        </Card>
    );
};

export default function MeetPage() {
    const { api, user, meetStatus, ageAssure, canAccessMeet, isAdult } = useAuth();
    const navigate = useNavigate();
    const [tab, setTab] = useState('discover');
    const [loading, setLoading] = useState(true);
    const [squads, setSquads] = useState([]);
    const [mySquads, setMySquads] = useState([]);
    const [matches, setMatches] = useState([]);
    const [invites, setInvites] = useState([]);
    const [discoverySquads, setDiscoverySquads] = useState([]);
    const [showCreateSquad, setShowCreateSquad] = useState(false);
    const [showInvite, setShowInvite] = useState(false);
    const [selectedSquad, setSelectedSquad] = useState(null);
    const [newSquadName, setNewSquadName] = useState('');
    const [inviteUserId, setInviteUserId] = useState('');
    const [verifying, setVerifying] = useState(false);

    useEffect(() => {
        if (canAccessMeet) {
            fetchData();
        }
    }, [canAccessMeet, tab]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [squadsRes, matchesRes, invitesRes, discoverRes] = await Promise.all([
                api.get('/meet/squads'),
                api.get('/meet/matches'),
                api.get('/meet/invites'),
                api.get('/meet/discover')
            ]);
            setMySquads(squadsRes.data);
            setMatches(matchesRes.data);
            setInvites(invitesRes.data);
            setDiscoverySquads(discoverRes.data);
        } catch (e) {
            console.error('Failed to fetch meet data', e);
        } finally {
            setLoading(false);
        }
    };

    const handleVerify = async () => {
        setVerifying(true);
        try {
            await ageAssure();
            toast.success('Age verified! Meet is now unlocked.');
            fetchData();
        } catch (e) {
            toast.error('Verification failed');
        } finally {
            setVerifying(false);
        }
    };

    const handleCreateSquad = async () => {
        if (!newSquadName.trim()) return;
        try {
            const res = await api.post('/meet/squads', { name: newSquadName });
            setMySquads([res.data, ...mySquads]);
            setShowCreateSquad(false);
            setNewSquadName('');
            toast.success('Squad created!');
        } catch (e) {
            toast.error('Failed to create squad');
        }
    };

    const handleInvite = async () => {
        if (!inviteUserId.trim() || !selectedSquad) return;
        try {
            await api.post(`/meet/squads/${selectedSquad.id}/invite`, { invitee_id: inviteUserId });
            toast.success('Invite sent!');
            setShowInvite(false);
            setInviteUserId('');
        } catch (e) {
            toast.error(e.response?.data?.detail || 'Failed to send invite');
        }
    };

    const handleAcceptInvite = async (invite) => {
        try {
            await api.post(`/meet/squads/${invite.squad_id}/invite/${invite.id}/accept`);
            setInvites(invites.filter(i => i.id !== invite.id));
            fetchData();
            toast.success('Joined squad!');
        } catch (e) {
            toast.error(e.response?.data?.detail || 'Failed to join');
        }
    };

    const handleDeclineInvite = async (invite) => {
        try {
            await api.post(`/meet/squads/${invite.squad_id}/invite/${invite.id}/decline`);
            setInvites(invites.filter(i => i.id !== invite.id));
            toast.success('Invite declined');
        } catch (e) {
            toast.error('Failed to decline');
        }
    };

    const handleSwipe = async (targetSquadId, direction) => {
        if (mySquads.length === 0) {
            toast.error('Create or join a squad first!');
            return;
        }
        
        const mySquad = mySquads[0]; // Use first squad for now
        
        try {
            // Create swipe
            const swipeRes = await api.post(`/meet/squads/${mySquad.id}/swipe`, {
                target_squad_id: targetSquadId,
                direction
            });
            
            // Cast vote
            const voteRes = await api.post(`/meet/swipes/${swipeRes.data.id}/vote`, {
                vote: direction === 'like' ? 'like' : 'pass'
            });
            
            // Remove from discovery
            setDiscoverySquads(discoverySquads.filter(s => s.id !== targetSquadId));
            
            if (voteRes.data.match_created) {
                toast.success("It's a match! 🎉");
                fetchData();
            } else if (direction === 'like') {
                toast.success('Vote cast! Waiting for squad members.');
            }
        } catch (e) {
            toast.error('Failed to swipe');
        }
    };

    const handleMatchClick = (match) => {
        navigate(`/messages/${match.conversation_id}`);
    };

    // Not adult - show blocked message
    if (!isAdult) {
        return (
            <MainLayout>
                <div className="max-w-md mx-auto px-4 py-12 text-center space-y-6">
                    <div className="w-20 h-20 mx-auto rounded-full bg-amber-500/20 flex items-center justify-center">
                        <AlertCircle className="w-10 h-10 text-amber-400" />
                    </div>
                    <h1 className="font-heading text-2xl font-bold">Meet is 18+ Only</h1>
                    <p className="text-muted-foreground">
                        The dating features on CliqUp are only available to users who are 18 years or older.
                    </p>
                </div>
            </MainLayout>
        );
    }

    // Need verification
    if (!canAccessMeet) {
        return (
            <MainLayout>
                <div className="max-w-md mx-auto px-4 py-12 text-center space-y-6" data-testid="meet-verification">
                    <div className="w-20 h-20 mx-auto rounded-full bg-teal-600/20 flex items-center justify-center">
                        <Shield className="w-10 h-10 text-teal-400" />
                    </div>
                    <h1 className="font-heading text-2xl font-bold">Verify Your Age</h1>
                    <p className="text-muted-foreground">
                        To access Meet and start dating with your squad, we need to verify you're 18 or older.
                    </p>
                    <Button 
                        size="lg" 
                        className="rounded-full bg-teal-600 hover:bg-teal-700"
                        onClick={handleVerify}
                        disabled={verifying}
                        data-testid="verify-btn"
                    >
                        {verifying ? 'Verifying...' : 'Verify Age'}
                    </Button>
                </div>
            </MainLayout>
        );
    }

    return (
        <MainLayout>
            <div className="max-w-2xl mx-auto px-4 py-6 space-y-6" data-testid="meet-page">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="font-heading text-2xl font-bold text-gradient-brand">Meet</h1>
                        <p className="text-sm text-muted-foreground">Squad-first dating</p>
                    </div>
                    <Dialog open={showCreateSquad} onOpenChange={setShowCreateSquad}>
                        <DialogTrigger asChild>
                            <Button className="rounded-full gap-2" data-testid="create-squad-btn">
                                <Plus className="w-4 h-4" />
                                New Squad
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Create a Squad</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2">
                                    <Label htmlFor="squadName">Squad Name</Label>
                                    <Input
                                        id="squadName"
                                        placeholder="e.g., Weekend Warriors"
                                        value={newSquadName}
                                        onChange={(e) => setNewSquadName(e.target.value)}
                                        data-testid="squad-name-input"
                                    />
                                </div>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setShowCreateSquad(false)}>
                                    Cancel
                                </Button>
                                <Button onClick={handleCreateSquad} disabled={!newSquadName.trim()} data-testid="create-squad-submit">
                                    Create Squad
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

                {/* Invites */}
                {invites.length > 0 && (
                    <Card className="glass-card p-4 border-teal-600/20 bg-teal-600/5">
                        <h3 className="font-semibold mb-3 flex items-center gap-2">
                            <UserPlus className="w-4 h-4 text-teal-400" />
                            Pending Invites ({invites.length})
                        </h3>
                        <div className="space-y-2">
                            {invites.map((invite) => (
                                <div key={invite.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                                    <div>
                                        <p className="font-medium">{invite.squad_name}</p>
                                        <p className="text-sm text-muted-foreground">from {invite.inviter_name}</p>
                                    </div>
                                    <div className="flex gap-2">
                                        <Button 
                                            size="sm" 
                                            variant="outline" 
                                            className="rounded-full border-gray-500"
                                            onClick={() => handleDeclineInvite(invite)}
                                        >
                                            <X className="w-4 h-4" />
                                        </Button>
                                        <Button 
                                            size="sm" 
                                            className="rounded-full bg-teal-600 hover:bg-teal-700"
                                            onClick={() => handleAcceptInvite(invite)}
                                            data-testid={`accept-invite-${invite.id}`}
                                        >
                                            <Check className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Card>
                )}

                {/* Tabs */}
                <Tabs value={tab} onValueChange={setTab}>
                    <TabsList className="w-full glass">
                        <TabsTrigger value="discover" className="flex-1" data-testid="discover-tab">
                            <Heart className="w-4 h-4 mr-2" />
                            Discover
                        </TabsTrigger>
                        <TabsTrigger value="squads" className="flex-1" data-testid="squads-tab">
                            <Users className="w-4 h-4 mr-2" />
                            My Squads
                        </TabsTrigger>
                        <TabsTrigger value="matches" className="flex-1" data-testid="matches-tab">
                            <Sparkles className="w-4 h-4 mr-2" />
                            Matches
                        </TabsTrigger>
                    </TabsList>

                    {/* Discover Tab */}
                    <TabsContent value="discover" className="mt-6">
                        {loading ? (
                            <Card className="glass-card aspect-[3/4] flex items-center justify-center">
                                <div className="text-muted-foreground">Loading...</div>
                            </Card>
                        ) : mySquads.length === 0 ? (
                            <Card className="glass-card p-8 text-center space-y-4">
                                <Users className="w-12 h-12 mx-auto text-muted-foreground" />
                                <h3 className="font-heading text-xl font-semibold">Create Your Squad First</h3>
                                <p className="text-muted-foreground">
                                    You need to be in a squad before you can discover and match with others.
                                </p>
                                <Button 
                                    className="rounded-full"
                                    onClick={() => setShowCreateSquad(true)}
                                >
                                    Create Squad
                                </Button>
                            </Card>
                        ) : discoverySquads.length > 0 ? (
                            <SquadDiscoveryCard 
                                squad={discoverySquads[0]} 
                                onSwipe={handleSwipe}
                            />
                        ) : (
                            <Card className="glass-card p-8 text-center space-y-4">
                                <Heart className="w-12 h-12 mx-auto text-muted-foreground" />
                                <h3 className="font-heading text-xl font-semibold">No More Squads</h3>
                                <p className="text-muted-foreground">
                                    You've seen all available squads. Check back later!
                                </p>
                            </Card>
                        )}
                    </TabsContent>

                    {/* My Squads Tab */}
                    <TabsContent value="squads" className="mt-6 space-y-4">
                        {loading ? (
                            <div className="space-y-4">
                                {[1, 2].map(i => (
                                    <Card key={i} className="glass-card p-4">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-full skeleton-shimmer" />
                                            <div className="flex-1 space-y-2">
                                                <div className="h-4 w-32 skeleton-shimmer rounded" />
                                                <div className="h-3 w-24 skeleton-shimmer rounded" />
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        ) : mySquads.length > 0 ? (
                            <div className="space-y-4">
                                {mySquads.map((squad) => (
                                    <MySquadCard 
                                        key={squad.id} 
                                        squad={squad}
                                        onViewDetails={(s) => {
                                            setSelectedSquad(s);
                                            setShowInvite(true);
                                        }}
                                    />
                                ))}
                            </div>
                        ) : (
                            <Card className="glass-card p-8 text-center space-y-4">
                                <Users className="w-12 h-12 mx-auto text-muted-foreground" />
                                <h3 className="font-heading text-xl font-semibold">No Squads Yet</h3>
                                <p className="text-muted-foreground">
                                    Create a squad and invite your friends to start matching!
                                </p>
                            </Card>
                        )}
                    </TabsContent>

                    {/* Matches Tab */}
                    <TabsContent value="matches" className="mt-6 space-y-4">
                        {loading ? (
                            <div className="space-y-4">
                                {[1, 2].map(i => (
                                    <Card key={i} className="glass-card p-4">
                                        <div className="flex items-center gap-4">
                                            <div className="avatar-stack">
                                                <div className="w-10 h-10 rounded-full skeleton-shimmer" />
                                                <div className="w-10 h-10 rounded-full skeleton-shimmer" />
                                            </div>
                                            <div className="flex-1 space-y-2">
                                                <div className="h-4 w-32 skeleton-shimmer rounded" />
                                                <div className="h-3 w-24 skeleton-shimmer rounded" />
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        ) : matches.length > 0 ? (
                            <div className="space-y-4">
                                {matches.map((match) => (
                                    <MatchCard 
                                        key={match.id} 
                                        match={match}
                                        onClick={handleMatchClick}
                                    />
                                ))}
                            </div>
                        ) : (
                            <Card className="glass-card p-8 text-center space-y-4">
                                <Sparkles className="w-12 h-12 mx-auto text-muted-foreground" />
                                <h3 className="font-heading text-xl font-semibold">No Matches Yet</h3>
                                <p className="text-muted-foreground">
                                    Keep swiping with your squad to find matches!
                                </p>
                            </Card>
                        )}
                    </TabsContent>
                </Tabs>

                {/* Invite Dialog */}
                <Dialog open={showInvite} onOpenChange={setShowInvite}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Invite to {selectedSquad?.name}</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label htmlFor="userId">User ID</Label>
                                <Input
                                    id="userId"
                                    placeholder="Enter user ID to invite"
                                    value={inviteUserId}
                                    onChange={(e) => setInviteUserId(e.target.value)}
                                    data-testid="invite-user-input"
                                />
                                <p className="text-xs text-muted-foreground">
                                    Ask your friend for their user ID from their profile
                                </p>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setShowInvite(false)}>
                                Cancel
                            </Button>
                            <Button onClick={handleInvite} disabled={!inviteUserId.trim()} data-testid="send-invite-btn">
                                Send Invite
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
        </MainLayout>
    );
}
