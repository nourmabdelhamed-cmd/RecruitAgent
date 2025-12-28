# Product Overview

Tata is GlobalConnect's Talent Acquisition Team Assistant - a conversational AI that supports recruiters through the entire recruitment lifecycle.

## Core Concept

- Each chat session = one recruitment project
- The requirement profile is the backbone for all outputs
- Stateful: artifacts created in a session are reused automatically

## Key Modules

| Module | Purpose |
|--------|---------|
| A | Requirement Profile - foundation for all outputs |
| B | Job Ad creation |
| C | TA Screening Template |
| D | HM Screening Template |
| E | Headhunting Messages (LinkedIn outreach) |
| F | Candidate Report from interview transcripts |
| G | Funnel Report from ATS/LinkedIn data |
| H | Job Ad Review |
| I | D&I Review (bias-free language check) |
| J | Calendar Invitation text |

## Module Dependencies

- B, C, D, E require Module A (Requirement Profile)
- F requires A + C (Profile + Screening Template)
- G, H, I, J are standalone

## Language Support

English (default), Swedish, Danish, Norwegian, German (du/Sie variants)

## Key Constraints

- Never expose module letters (A, B, C) to users - use natural terms
- Never ask for recruiter's personal name
- Never invent requirements not provided by recruiter
- No emojis in any output
- No dash-style bullets in body text
- Enforce banned words list in candidate-facing text
