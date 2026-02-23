# NEXUS - Social + Dating Platform PRD

## Original Problem Statement
Build NEXUS - a unified social network and dating platform with squad-first group dating as the primary dating mode. Features include:
- Social: profiles, posts, feed, comments, reactions, stories, DMs
- Dating: squad creation, invites, swipe/vote/match system, group chats
- Age-gating: Dating features (Meet) locked for users under 18

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn UI
- **Backend**: FastAPI + MongoDB (async with Motor)
- **Auth**: JWT tokens with 7-day expiration
- **Database**: MongoDB collections for users, profiles, posts, squads, matches, messages, etc.

## User Personas
1. **Teens (13-17)**: Social-only users, cannot access Meet (dating)
2. **Adults (18+)**: Full access to social + dating after age verification
3. **Squad Owners**: Users who create and manage squads for group dating

## Core Requirements (Static)
- [x] DOB-based age band calculation (u13, teen, adult)
- [x] Meet (dating) locked for non-adults
- [x] Age assurance flow for adults to unlock Meet
- [x] Squad creation with owner designation
- [x] Squad invites with acceptance flow
- [x] Swipe and voting system with majority threshold
- [x] Match creation on mutual likes
- [x] Auto-creation of group chat on match
- [x] Posts with reactions and comments
- [x] User profiles with dating profile link

## What's Been Implemented (Feb 2026)

### Backend APIs
- ✅ Auth: signup, login, /me
- ✅ Profiles: create, update, get by ID/handle
- ✅ Follow system: follow, unfollow, followers/following lists
- ✅ Meet access: status check, age assurance
- ✅ Dating profiles: create, get
- ✅ Squads: create, list, invite, accept/decline
- ✅ Swipe/Vote: create swipe, cast vote, automatic match creation
- ✅ Matches: list user's matches
- ✅ Messaging: conversations, messages, DM creation
- ✅ Posts: create, feed, explore, react, comment
- ✅ Stories: create, feed (grouped by user), view tracking
- ✅ Notifications: list, mark read, unread count
- ✅ Search: users, posts

### Frontend Pages
- ✅ Landing page with feature cards
- ✅ Signup with DOB picker (2-step flow)
- ✅ Login page
- ✅ Home feed with posts, reactions, comments
- ✅ Explore page (trending content)
- ✅ Meet page with Discover/Squads/Matches tabs
- ✅ Squad creation and management
- ✅ Messages page with conversation list and chat view
- ✅ Profile page with Posts/Dating tabs
- ✅ Search page (users and posts)
- ✅ Notifications page

### Design System
- Electric Midnight dark theme
- Syne (headings) + Manrope (body) fonts
- Indigo (#6366F1) for social, Pink (#EC4899) for dating
- Glass-morphism effects
- Micro-animations and hover states

## P0/P1/P2 Features Remaining

### P0 (Critical)
- All core features implemented ✅

### P1 (Important)
- [ ] Stories viewer carousel
- [ ] Watch (short video) feed
- [ ] Real-time messaging with WebSocket
- [ ] Push notifications
- [ ] Photo upload to cloud storage

### P2 (Nice to have)
- [ ] Live streaming
- [ ] Remix tools (duet/stitch)
- [ ] Groups and Events
- [ ] Creator analytics dashboard
- [ ] ID verification badge
- [ ] Subscription billing (Premium tiers)

## Next Tasks
1. Implement Stories carousel viewer
2. Add Watch (TikTok-style) video feed
3. Set up WebSocket for real-time messaging
4. Integrate cloud storage for media uploads
5. Add push notification support

## Test Credentials
- Email: test@nexus.com
- Password: password123
- Status: Adult, age-assured, has squads
