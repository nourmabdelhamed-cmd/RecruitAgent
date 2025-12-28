# Implementation Plan: Tata Recruitment Assistant

## Overview

This implementation plan breaks down the Tata Recruitment Assistant into discrete coding tasks. The approach is to build core infrastructure first (session management, memory, dependencies), then implement each module incrementally, with property tests validating correctness at each step.

## Tasks

- [-] 1. Set up project structure and core infrastructure
  - [x] 1.1 Initialize Python project with uv and testing framework
    - Run `uv init` to create Python project
    - Configure `pyproject.toml` with dependencies: `hypothesis` for property-based testing, `pytest` for unit tests
    - Set up project structure: `src/tata/`, `tests/`
    - Run `uv sync` to install dependencies
    - _Requirements: Testing Strategy_

  - [x] 1.2 Implement Session Manager
    - Create `src/tata/session/session.py` with Session dataclass
    - Implement SessionManager protocol with create_session, get_session, set_position_name, set_language methods
    - Store sessions in dict with threading.Lock for thread safety
    - _Requirements: 1.1, 12.2_

  - [ ]* 1.3 Write property test for Session Manager
    - **Property 1: Memory Persistence Invariant**
    - **Validates: Requirements 1.1, 1.5**

  - [x] 1.4 Implement Memory Manager
    - Create `src/tata/memory/memory.py` with ArtifactType enum
    - Define Artifact protocol and implement store, retrieve, has_artifact, get_all_artifacts methods
    - Link to session by session_id
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 1.5 Write property test for Memory Manager
    - **Property 2: Artifact Reuse in Dependencies**
    - **Validates: Requirements 1.2, 1.3, 1.4, 3.1**

  - [x] 1.6 Implement Dependency Manager
    - Create `src/tata/dependency/dependency.py` with MODULE_DEPENDENCIES dict
    - Implement can_execute, get_required_modules, is_standalone methods
    - Return DependencyCheck with missing dependencies
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 1.7 Write property test for Dependency Manager
    - **Property 8: Dependency Enforcement**
    - **Validates: Requirements 3.2, 5.1**

- [x] 2. Checkpoint - Core infrastructure complete
  - Run `uv run pytest` to ensure all tests pass
  - Ask the user if questions arise.

- [x] 3. Implement Language Guide Processor
  - [x] 3.1 Create banned words lists for all languages
    - Create `src/tata/language/banned_words.py`
    - Define banned words lists for EN, SV, DA, NO, DE
    - Include hype words and exclusionary terms
    - _Requirements: 2.7, 7.5_

  - [x] 3.2 Implement banned word checker
    - Create check_banned_words function in `src/tata/language/checker.py`
    - Return BannedWordCheck with violations (word, suggestion, position)
    - _Requirements: 2.7, 13.5_

  - [ ]* 3.3 Write property test for banned words
    - **Property 7: No Banned Words**
    - **Validates: Requirements 2.7, 7.5, 13.5**

  - [x] 3.4 Implement emoji and dash bullet validators
    - Create has_emojis function with Unicode range checks
    - Create has_dash_bullets function
    - _Requirements: 2.5, 2.6_

  - [ ]* 3.5 Write property tests for format validators
    - **Property 5: No Emojis**
    - **Property 6: No Dash Bullets**
    - **Validates: Requirements 2.5, 2.6**

  - [x] 3.6 Implement German formality selector
    - Create get_german_formality function
    - Determine du/Sie based on context
    - _Requirements: 2.8_

  - [ ]* 3.7 Write property test for language consistency
    - **Property 3: Language Consistency**
    - **Validates: Requirements 2.2, 2.8**

- [x] 4. Checkpoint - Language processing complete
  - Run `uv run pytest` to ensure all tests pass
  - Ask the user if questions arise.

- [x] 5. Implement Module A: Requirement Profile
  - [x] 5.1 Create RequirementProfile types and processor
    - Create `src/tata/modules/profile/profile.py`
    - Define RequirementProfileInput and RequirementProfile dataclasses
    - Implement validate method for input
    - _Requirements: 4.1, 4.2_

  - [x] 5.2 Implement skill extraction logic
    - Extract exactly 4 must-have skills from input
    - Extract responsibilities and good-to-haves
    - _Requirements: 4.1, 4.2, 4.6_

  - [ ]* 5.3 Write property test for must-haves extraction
    - **Property 10: Four Must-Haves Invariant**
    - **Validates: Requirements 4.1, 6.1, 13.3**

  - [x] 5.4 Implement content traceability
    - Track source of each extracted item
    - Ensure no invented content
    - _Requirements: 4.6, 13.2_

  - [ ]* 5.5 Write property test for no invented content
    - **Property 11: No Invented Content**
    - **Validates: Requirements 4.6, 13.2**

- [ ] 6. Implement Module B: Job Ad
  - [ ] 6.1 Create JobAd types and processor
    - Create `src/tata/modules/jobad/jobad.py`
    - Define JobAdInput and JobAd dataclasses with all sections
    - Implement dependency check for requirement profile
    - _Requirements: 5.1, 5.2_

  - [ ] 6.2 Implement job ad section generators
    - Generate headline, intro, role description, responsibilities
    - Generate requirements section with 4 must-haves visible
    - Generate team/why GC, process, ending sections
    - _Requirements: 5.2, 5.3, 13.3_

  - [ ]* 6.3 Write property test for output structure
    - **Property 12: Output Structure Validation**
    - **Validates: Requirements 5.2, 6.5, 8.5, 10.5, 11.6**

  - [ ] 6.4 Implement module naming filter
    - Ensure no "Module A/B/C" references in output
    - Use natural terms only
    - _Requirements: 3.5_

  - [ ]* 6.5 Write property test for no module naming
    - **Property 9: No Module Naming Exposure**
    - **Validates: Requirements 3.5**

- [ ] 7. Checkpoint - Profile and Job Ad complete
  - Run `uv run pytest` to ensure all tests pass
  - Ask the user if questions arise.

- [ ] 8. Implement Module C & D: Screening Templates
  - [ ] 8.1 Create ScreeningTemplate types
    - Create `src/tata/modules/screening/screening.py`
    - Define ScreeningTemplateInput, ScreeningTemplate, SkillQuestionSet dataclasses
    - Support both TA and HM template variants
    - _Requirements: 6.1, 6.5_

  - [ ] 8.2 Implement question generation by skill type
    - Create question templates for technical, leadership, functional, good-to-have
    - Generate 1 main + 2-3 follow-ups per skill
    - _Requirements: 6.3, 6.4_

  - [ ]* 8.3 Write property test for question structure
    - **Property 13: Question Generation Structure**
    - **Validates: Requirements 6.3, 6.4**

  - [ ] 8.4 Implement HM template notes space
    - Add notes placeholder after each question for HM templates
    - _Requirements: 6.7_

  - [ ]* 8.5 Write property test for HM notes space
    - **Property 14: HM Template Notes Space**
    - **Validates: Requirements 6.7**

- [ ] 9. Implement Module E: Headhunting Messages
  - [ ] 9.1 Create HeadhuntingMessages types
    - Create `src/tata/modules/headhunting/headhunting.py`
    - Define HeadhuntingInput, HeadhuntingMessages, MultiLanguageMessage dataclasses
    - _Requirements: 7.1, 7.2_

  - [ ] 9.2 Implement three message version generators
    - Generate short & direct, value-proposition, call-to-action versions
    - _Requirements: 7.1, 7.6_

  - [ ]* 9.3 Write property test for three versions
    - **Property 15: Three Headhunting Versions**
    - **Validates: Requirements 7.1**

  - [ ] 9.4 Implement multi-language generation
    - Generate all versions in EN, SV, DA, NO, DE (du and Sie)
    - _Requirements: 7.2_

  - [ ]* 9.5 Write property test for multi-language
    - **Property 16: Multi-Language Availability**
    - **Validates: Requirements 7.2**

  - [ ] 9.6 Implement message length constraint
    - Ensure all messages under 100 words
    - _Requirements: 7.3_

  - [ ]* 9.7 Write property test for message length
    - **Property 17: Message Length Constraint**
    - **Validates: Requirements 7.3**

  - [ ] 9.8 Implement personalization logic
    - Extract detail from candidate profile when provided
    - Include in personalized message
    - _Requirements: 7.4_

  - [ ]* 9.9 Write property test for personalization
    - **Property 18: Personalization When Profile Provided**
    - **Validates: Requirements 7.4**

  - [ ] 9.10 Implement message structure validation
    - Ensure role hook, value prop, CTA in each message
    - _Requirements: 7.6_

  - [ ]* 9.11 Write property test for message structure
    - **Property 19: Message Structure Completeness**
    - **Validates: Requirements 7.6**

- [ ] 10. Checkpoint - Templates and Headhunting complete
  - Run `uv run pytest` to ensure all tests pass
  - Ask the user if questions arise.

- [ ] 11. Implement Module F: Candidate Report
  - [ ] 11.1 Create CandidateReport types
    - Create `src/tata/modules/report/candidate.py`
    - Define CandidateReportInput, CandidateReport, SkillAssessment dataclasses
    - _Requirements: 8.1, 8.5_

  - [ ] 11.2 Implement transcript processing
    - Parse Microsoft Teams transcript format
    - Map content to motivation, skills, practical sections
    - _Requirements: 8.1, 8.3_

  - [ ] 11.3 Implement rating system
    - Create Rating enum with values 1-5
    - Validate rating in range with non-empty explanation
    - _Requirements: 8.4_

  - [ ]* 11.4 Write property test for rating validity
    - **Property 20: Rating Validity**
    - **Validates: Requirements 8.4**

  - [ ] 11.5 Implement candidate anonymization
    - Convert full names to initials in comparison tables
    - _Requirements: 8.7_

  - [ ]* 11.6 Write property test for anonymization
    - **Property 21: Candidate Anonymization**
    - **Validates: Requirements 8.7**

- [ ] 12. Implement Module G: Funnel Report
  - [ ] 12.1 Create FunnelReport types
    - Create `src/tata/modules/report/funnel.py`
    - Define FunnelReportInput, FunnelReport, FunnelStage, Bottleneck dataclasses
    - _Requirements: 9.1, 9.5_

  - [ ] 12.2 Implement conversion rate calculator
    - Calculate conversion rate as (count_B / count_A) × 100
    - Handle division by zero
    - _Requirements: 9.2_

  - [ ]* 12.3 Write property test for conversion calculation
    - **Property 22: Conversion Rate Calculation**
    - **Validates: Requirements 9.2**

  - [ ] 12.4 Implement bottleneck detection
    - Flag stages with low conversion or high time-in-stage
    - _Requirements: 9.3_

  - [ ]* 12.5 Write property test for bottleneck identification
    - **Property 23: Bottleneck Identification**
    - **Validates: Requirements 9.3**

  - [ ] 12.6 Implement fix and owner assignment
    - Assign one fix and one owner per bottleneck
    - Link to existing artifacts when relevant
    - _Requirements: 9.4, 9.6_

  - [ ]* 12.7 Write property test for fix assignment
    - **Property 24: Fix and Owner Assignment**
    - **Validates: Requirements 9.6**

- [ ] 13. Checkpoint - Reports complete
  - Run `uv run pytest` to ensure all tests pass
  - Ask the user if questions arise.

- [ ] 14. Implement Module I: D&I Review
  - [ ] 14.1 Create DIReview types
    - Create `src/tata/modules/review/di.py`
    - Define DIReviewInput, DIReview, FlaggedItem, BiasCategory dataclasses
    - _Requirements: 10.1, 10.5_

  - [ ] 14.2 Implement bias word pools for all languages
    - Create comprehensive word pools for gender, age, disability, etc.
    - Support EN, SV, DA, NO, DE
    - _Requirements: 10.6_

  - [ ] 14.3 Implement bias detection scanner
    - Scan text against all bias categories
    - Return flagged items with severity
    - _Requirements: 10.1, 10.2_

  - [ ]* 14.4 Write property test for bias category coverage
    - **Property 25: Bias Category Coverage**
    - **Validates: Requirements 10.1, 10.6**

  - [ ] 14.5 Implement alternative suggestions
    - Generate alternative wording for each flagged item
    - _Requirements: 10.3_

  - [ ]* 14.6 Write property test for alternatives
    - **Property 26: Flagged Items With Alternatives**
    - **Validates: Requirements 10.2, 10.3**

  - [ ] 14.7 Implement no-change guarantee
    - Return suggestions separately, never modify original
    - _Requirements: 10.4_

  - [ ]* 14.8 Write property test for no automatic changes
    - **Property 27: No Automatic Changes**
    - **Validates: Requirements 10.4**

- [ ] 15. Implement Module J: Calendar Invitation
  - [ ] 15.1 Create CalendarInvite types
    - Create `src/tata/modules/calendar/invite.py`
    - Define CalendarInviteInput, CalendarInvite, OfficeLocation dataclasses
    - _Requirements: 11.1, 11.6_

  - [ ] 15.2 Implement office location lookup
    - Create OFFICE_LOCATIONS dict with addresses and map links
    - Return correct location for selected city
    - _Requirements: 11.2_

  - [ ]* 15.3 Write property test for office address
    - **Property 28: Office Address Correctness**
    - **Validates: Requirements 11.2**

  - [ ] 15.4 Implement conditional content logic
    - Include Jobylon instruction for Jobylon booking
    - Include date/time for manual booking
    - _Requirements: 11.3, 11.4_

  - [ ]* 15.5 Write property test for conditional content
    - **Property 29: Conditional Content - Booking Method**
    - **Validates: Requirements 11.3, 11.4**

  - [ ] 15.6 Implement candidate name placement
    - Ensure candidate placeholder in subject and greeting
    - _Requirements: 11.5_

  - [ ]* 15.7 Write property test for candidate name
    - **Property 30: Candidate Name Placement**
    - **Validates: Requirements 11.5**

- [ ] 16. Implement Module H: Job Ad Review
  - [ ] 16.1 Create JobAdReview types
    - Create `src/tata/modules/review/jobad.py`
    - Define review structure with scorecard and recommendations
    - _Requirements: Module H specification_

  - [ ] 16.2 Implement section mapping and gap analysis
    - Map ad sections to expected structure
    - Identify missing or duplicated content
    - _Requirements: Module H specification_

- [ ] 17. Checkpoint - All modules complete
  - Run `uv run pytest` to ensure all tests pass
  - Ask the user if questions arise.

- [ ] 18. Implement Recruiter Interaction Flow
  - [ ] 18.1 Implement greeting and service menu
    - Create `src/tata/interaction/greeting.py`
    - Create default English greeting
    - Display all available modules
    - _Requirements: 12.1, 12.3, 12.4_

  - [ ] 18.2 Implement no recruiter name request
    - Ensure system never asks for recruiter's personal name
    - _Requirements: 12.5_

  - [ ]* 18.3 Write property test for no recruiter name request
    - **Property 31: No Recruiter Name Request**
    - **Validates: Requirements 12.5**

- [ ] 19. Implement Document Generator and Validator
  - [ ] 19.1 Create document output formatters
    - Create `src/tata/output/generator.py`
    - Implement Word-ready text generation
    - Implement comparison table generation
    - _Requirements: Output formatting_

  - [ ] 19.2 Implement comprehensive validator
    - Create `src/tata/validator/validator.py`
    - Validate against requirement profile
    - Validate language compliance
    - Validate must-have visibility
    - _Requirements: 13.1, 13.3, 13.4_

- [ ] 20. Final checkpoint - Full system integration
  - Run `uv run pytest` to ensure all tests pass
  - Ask the user if questions arise.
  - Run full workflow integration tests
  - Verify all 31 properties pass

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using `hypothesis`
- Unit tests validate specific examples and edge cases
- Implementation uses Python with `uv` for environment management
- Project structure follows Python conventions: `src/tata/`, `tests/`
- Run tests with `uv run pytest` at each checkpoint
- Run tests with coverage: `uv run pytest --cov=src/tata`
