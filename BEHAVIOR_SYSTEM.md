# Unstuck — Behavior System Spec

## Purpose

This document defines the psychological model and intervention logic that powers Unstuck.

The goal is to help a user move from avoidance to action as quickly and reliably as possible.

## Core Model

Procrastination is treated as a regulation problem, not a character flaw.

Users usually do not fail because they lack desire. They fail because of one or more of these states:
- overwhelm
- ambiguity
- perfectionism
- fear of failure
- fear of success
- boredom
- low energy
- emotional discomfort

Unstuck should identify the state, reduce friction, and guide the user into immediate action.

## Main Intervention Loop

1. Notice resistance
2. Name the avoided task
3. Identify the blocker
4. Reduce scope
5. Start tiny action
6. Reinforce progress
7. Log what helped

## Blocker Types

### Overwhelm
Signals:
- “I don’t know where to start”
- “This is too big”

Interventions:
- Break into sub-steps
- Define the smallest visible next action
- Ask: what would count as progress in 5 minutes?

### Ambiguity
Signals:
- “I’m not clear what this actually means”
- “I need to think more before starting”

Interventions:
- Clarify outcome
- Convert fuzzy task into action statement
- Ask: what is the first observable move?

### Perfectionism
Signals:
- “I need to do this right”
- “I’m not ready yet”

Interventions:
- First ugly version
- Permission to be messy
- Time-box imperfect attempt

### Fear / Emotional Resistance
Signals:
- “If I do this badly, it means something about me”
- “I don’t want to face this”

Interventions:
- Name the fear
- Separate task from identity
- Reduce task to exposure-sized step

### Boredom / Low Reward
Signals:
- “This is tedious”
- “I just don’t want to”

Interventions:
- Short sprint
- Pair with reward
- Start with easiest meaningful fragment

### Low Energy
Signals:
- “I’m too tired”
- “My brain is mush”

Interventions:
- Scale down expectation
- Choose lighter step
- Encourage reset, movement, hydration, breath, then 5-minute attempt

## Core Flows

## I’m Stuck Flow

### Step 1: Capture
Prompt:
- What are you avoiding?

### Step 2: Identify blocker
Prompt:
- What feels hardest right now?
Options:
- Too big
- Not clear
- Want to do it perfectly
- Afraid / anxious
- Boring
- Low energy
- Other

### Step 3: Emotional state
Prompt:
- What are you feeling?
Options:
- overwhelmed
- anxious
- guilty
- frustrated
- tired
- numb
- resistant

### Step 4: Reframe
Prompt varies by blocker.
Examples:
- Overwhelm: “You do not need to finish it. You only need the next visible step.”
- Perfectionism: “A rough version counts. Done imperfectly is still motion.”
- Fear: “This task is not your identity. We are only doing the smallest safe move.”

### Step 5: Action shrink
Prompt:
- What is the smallest action you can do in 2 to 5 minutes?

### Step 6: Sprint selection
Prompt:
- Want to do this for 5, 10, or 25 minutes?

### Step 7: Reflection
After timer:
- Did you start?
- Did the step help?
- Do you want one more small step?

## Daily Planning Flow

Morning prompts:
- What matters most today?
- What are you most likely to avoid?
- What is the smallest meaningful step on that task?

Evening prompts:
- What moved forward today?
- Where did you get stuck?
- What helped you restart?
- What should tomorrow begin with?

## Intervention Library

### Start Tiny
- Commit to 2 to 5 minutes only

### First Ugly Version
- Produce a bad first pass on purpose

### Clarify the Win
- Define what “good enough” means for this step

### Reduce the Scope
- Cut task until it feels almost too easy

### Friction Removal
- Remove one obstacle before starting
- Example: open file, close tabs, place document in front of you

### Identity Separation
- Remind user: struggling to start does not mean they are lazy or incapable

### Focus Sprint
- Use timer to lower activation cost

### Restart Prompt
- “You do not need to feel ready. You only need to begin.”

## Data to Track

Per intervention:
- avoided task
- blocker type
- emotional state
- tiny next action
- sprint length
- completed or not
- self-rated helpfulness

Per day:
- focus starts
- recovered procrastination moments
- completed sprints
- main avoided categories

## Insight Logic

Unstuck should identify patterns such as:
- specific times of day with highest resistance
- blocker types that occur most often
- interventions that most reliably lead to action
- projects with repeated avoidance

## Tone Requirements

The system voice should be:
- calm
- direct
- non-shaming
- warm
- practical
- brief on mobile

Avoid:
- guilt
- hype
- fake cheerleading
- rigid productivity language

## Outcome

A successful intervention means the user does not just feel understood.
It means the user actually starts.
