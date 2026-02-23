# CliqUp - Product Requirements Document

## Overview
CliqUp is a unified social + dating platform with squad-first group matching. Users have a single account for both social networking and dating features, with age-gating for dating (18+ only).

## Original Problem Statement
Build a single unified platform called "CliqUp" that combines:
- Core features of modern social networks (like Facebook, Instagram, TikTok)
- Dating app features (like Tinder, Hinge)
- Squad-first dating: Users form groups to match with other groups

## Tech Stack
- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React 18 with ShadCN/UI components
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT tokens (7-day expiry)
- **State Management**: React Context API

## Architecture (v2.0.0 - Modular Domain-Driven)

### Backend Structure
```
/app/backend/
├── app.py                    # Main FastAPI application
├── server.py                 # Entry point (imports from app.py)
├── core/                     # Core functionality
│   ├── config.py            # Configuration with pydantic-settings
│   ├── database.py          # MongoDB connection & collections
│   ├── security.py          # JWT auth, password hashing
│   └── enums.py             # Shared enumerations
├── modules/                  # Domain modules
│   ├── identity/            # Authentication
│   │   ├── router.py        # /api/auth/* endpoints
│   │   ├── service.py       # Business logic
│   │   ├── repository.py    # Data access
│   │   └── schemas.py       # Pydantic models
│   ├── profiles/            # User profiles & follows
│   │   └── (same structure)
│   ├── social/              # Posts, stories, reactions
│   │   └── (same structure)
│   ├── meet/                # Dating features
│   │   └── (same structure)
│   └── messaging/           # Conversations & messages
│       └── (same structure)
└── utils/                    # Utilities
    ├── helpers.py           # Common helpers
    └── elo.py               # Elo rating algorithm
```

### Key Features Implemented

#### 1. Identity Module
- Email/phone signup with password
- JWT authentication
- Age band calculation (u13, teen, adult)
- Automatic profile & entitlement creation

#### 2. Profiles Module  
- User profiles with handle, bio, avatar
- Follow/unfollow system
- Followers/following counts
- Dating link mode (curated, full, none)

#### 3. Social Module
- Text/photo/video/carousel posts
- Reactions (like, love, laugh, wow, sad, angry)
- Comments with replies
- Stories (24-hour ephemeral posts)
- Personalized feed from followed users
- Explore/trending feed

#### 4. Meet (Dating) Module
- Age verification (18+ only, mocked)
- Dating profiles with intents & preferences
- Squad creation & management
- Squad invites (accept/decline)
- **Elo-based discovery algorithm**
- Swipe system with squad voting
- Match creation with group chat

#### 5. Messaging Module
- DM conversations
- Group conversations
- Match group chats (auto-created on match)
- Message history with pagination

#### 6. Notifications
- Follow notifications
- Squad invite notifications
- Match notifications
- Message notifications
- Read/unread status

### Elo Rating Algorithm
The Elo rating system (inspired by chess) ranks squads for discovery:
- Default rating: 1200
- K-factor: 32
- Squad rating = weighted average of member ratings
- Compatibility score based on rating difference
- Ratings update on successful matches

### Database Collections
- `users` - User accounts
- `profiles` - User profiles
- `entitlements` - Subscription tiers
- `meet_access` - Age verification status
- `dating_profiles` - Dating preferences
- `squads` - Squad groups
- `squad_members` - Squad membership
- `squad_invites` - Pending invites
- `squad_swipes` - Swipe records
- `squad_swipe_votes` - Member votes
- `squad_matches` - Successful matches
- `follows` - Follow relationships
- `posts` - Social posts
- `post_reactions` - Post reactions
- `post_comments` - Comments
- `stories` - Ephemeral stories
- `story_views` - Story view tracking
- `conversations` - Chat conversations
- `conversation_members` - Chat members
- `messages` - Chat messages
- `notifications` - User notifications

## UI/UX Design
- **Theme**: Dark mode with Pink (#C93483), Turquoise (#2DD4BF), Grey palette
- **Components**: ShadCN/UI library
- **Layout**: Mobile-first responsive design
- **Branding**: CliqUp logo with star icon

## What's Mocked
- **Age Verification**: `/api/meet/age-assure` simply flips a boolean. Real implementation would require third-party verification service (e.g., ID scanning, biometrics).

## API Endpoints Summary

### Auth
- `POST /api/auth/signup` - Register
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Current user
- `POST /api/auth/verify-token` - Validate token

### Profiles
- `GET /api/profiles/me` - My profile
- `PUT /api/profiles/me` - Update profile
- `GET /api/profiles/{id}` - Get profile
- `POST /api/profiles/{id}/follow` - Follow
- `DELETE /api/profiles/{id}/follow` - Unfollow

### Social
- `POST /api/posts` - Create post
- `GET /api/posts/feed` - Personalized feed
- `GET /api/posts/explore` - Trending
- `POST /api/posts/{id}/react` - React
- `POST /api/posts/{id}/comments` - Comment
- `POST /api/stories` - Create story
- `GET /api/stories/feed` - Stories feed
- `GET /api/search?q=` - Search users/posts

### Meet (Dating)
- `GET /api/meet/status` - Access status
- `POST /api/meet/age-assure` - Verify age
- `POST /api/meet/dating-profile` - Dating profile
- `POST /api/meet/squads` - Create squad
- `GET /api/meet/squads` - My squads
- `POST /api/meet/squads/{id}/invite` - Invite
- `GET /api/meet/invites` - My invites
- `GET /api/meet/discover` - Discover squads
- `POST /api/meet/squads/{id}/swipe` - Swipe
- `POST /api/meet/swipes/{id}/vote` - Vote
- `GET /api/meet/matches` - My matches

### Messaging
- `GET /api/conversations` - List conversations
- `POST /api/conversations/dm/{id}` - Start DM
- `POST /api/conversations/group` - Create group
- `GET /api/conversations/{id}/messages` - Get messages
- `POST /api/conversations/{id}/messages` - Send message

### Notifications
- `GET /api/notifications` - Get notifications
- `GET /api/notifications/unread-count` - Unread count
- `POST /api/notifications/{id}/read` - Mark read
- `POST /api/notifications/read-all` - Mark all read

## Test Status (Last Run: 2024-02-23)
- **Backend**: 100% (32/32 tests passed)
- **Frontend**: 95% (minor UX improvements suggested)
- **Test Report**: `/app/test_reports/iteration_2.json`

## Future Tasks (Backlog)

### P0 - High Priority
- Real age verification integration
- File upload for posts/stories/avatars
- WebSocket for real-time messaging

### P1 - Medium Priority
- Video posts & stories
- Live streaming (18+ only)
- Push notifications

### P2 - Lower Priority
- Remix tools (Duet, Stitch)
- Communities (Groups & Events)
- Creator analytics dashboard
- Premium subscriptions (Stripe)

---
*Last updated: February 23, 2026*
*Version: 2.0.0 - Modular Architecture Overhaul*
