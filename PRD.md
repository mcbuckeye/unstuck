# Unstuckinator — Product Requirements Document

## Product Overview

**Unstuckinator** is a mobile-first web app that helps users reduce procrastination and develop focus by guiding them through short, psychologically-informed interventions when they feel blocked.

The core promise is simple: when a user is avoiding something, Unstuckinator helps them quickly identify why, reduce resistance, define the smallest next step, and start moving.

**Website:** [unstuckinator.com](https://unstuckinator.com)

## Problem

People often know what they should do but still fail to start. The gap is rarely lack of information, it is emotional resistance, overwhelm, perfectionism, ambiguity, or low energy. Most productivity apps help users plan tasks but do not help them restart in the moment of avoidance.

## Solution

Unstuckinator combines:
- quick daily planning
- guided “I’m stuck” interventions
- task breakdown tools
- focus sprint timers
- emotional check-ins
- pattern tracking and insights

The app is designed to be especially effective on mobile so users can use it the moment they notice resistance.

## Target User

Primary user:
- someone who struggles with procrastination despite being ambitious, capable, and self-aware
- often has multiple projects or responsibilities
- benefits from structured prompts, emotional clarity, and immediate next-step guidance

## Core Jobs To Be Done

- Help me start when I feel stuck
- Help me understand why I am avoiding something
- Help me shrink overwhelming tasks into tiny actions
- Help me build momentum through short focus sessions
- Help me see patterns in my procrastination triggers

## Product Principles

- Mobile first
- Fast to use in moments of resistance
- Emotionally intelligent, not shame-based
- Minimal typing and low friction
- Action-oriented over analytics-heavy
- Support one meaningful next step at a time

## Core Features

### 1. Today Screen
- Main focus for today
- Current task list
- Quick mood and energy state
- Large “I’m Stuck” button
- Start focus sprint button
- Recent wins and active streaks

### 2. I’m Stuck Flow
Guided micro-coaching flow:
- What are you avoiding?
- Why does it feel hard?
- What are you feeling?
- What is the smallest next step?
- Choose a 5, 10, or 25 minute sprint

### 3. Task Breakdown
- Convert vague projects into concrete next actions
- Define first ugly version
- Tag blockers like fear, confusion, perfectionism, boredom, overwhelm

### 4. Sprint Mode
- Single-task countdown timer
- Optional encouragement prompts
- End-of-sprint reflection
- Mark progress or continue

### 5. Check-ins
- Mood
- Energy
- Clarity
- Resistance
- Confidence

### 6. Insights
- Best focus times
- Most common avoidance triggers
- Which interventions work best
- Which tasks repeatedly stall

### 7. Wins
- Streak tracking
- Focus sessions completed
- Recovery moments after procrastination
- Daily and weekly momentum summaries

## MVP Scope

### Included
- Authentication
- Today dashboard
- Task creation
- I’m Stuck flow
- Sprint timer
- Check-ins
- Basic insights
- Mobile-first responsive UI

### Not Included Initially
- Calendar sync
- Team or social features
- Advanced AI coaching
- Voice features
- Push notifications
- Wearable integrations

## User Flow

1. User opens app
2. Lands on Today screen
3. Sees main focus and tasks
4. When blocked, taps “I’m Stuck”
5. Completes quick guided intervention
6. Gets one tiny next step
7. Starts sprint timer
8. Logs progress
9. Over time, app builds insights

## UX Requirements

- Excellent mobile layout
- Big touch targets
- One action per screen where possible
- Calm visual design
- Fast transitions
- Low typing burden
- PWA-friendly

## Tech Stack

- Frontend: React
- Backend: Python / FastAPI
- Database: PostgreSQL
- Auth: standard app auth flow
- Deployment: GitHub to Dokploy

## Success Metrics

- Users complete at least one focus start per day
- Users reduce time from “stuck” to “started”
- Repeat use of the I’m Stuck flow
- Increased completion of meaningful tasks
- Improvement in self-reported focus confidence

## Future Opportunities

- AI-generated coaching prompts
- Smarter intervention recommendations
- Notification nudges
- Voice capture
- Habit loops and adaptive routines
- Accountability partner features

## Product Positioning

Unstuckinator is not just a task manager.
It is an execution support system for people who need help getting moving when resistance shows up.
