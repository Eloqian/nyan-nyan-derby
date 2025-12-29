# Meow Meow Cup Tournament Management System - Architecture Design

## 1. Technical Stack & Environment

### 1.1 Backend
*   **Language**: Python 3.11+
*   **Framework**: **FastAPI** (Async, high performance, auto-documentation).
*   **ORM**: **SQLModel** (Combines Pydantic & SQLAlchemy, excellent for type safety).
*   **Migrations**: Alembic.
*   **Dependencies Management**: Poetry.

### 1.2 Database & Caching
*   **Primary DB**: **PostgreSQL 15+**.
    *   Chosen for strong relational integrity required by the complex stage/match structure.
*   **Cache/Queue**: **Redis**.
    *   Used for caching leaderboards (real-time view).
    *   Potential future use as a message broker for Bot notifications.

### 1.3 Frontend
*   **Framework**: **Vue 3** (Composition API).
*   **Build Tool**: Vite.
*   **Language**: TypeScript.
*   **UI Library**: **Naive UI** (Clean, modern, highly customizable, good TypeScript support).
*   **State Management**: Pinia.

### 1.4 Development Environment (Mac/ARM64 Optimized)
*   **Containerization**: Docker & Docker Compose.
    *   Base images will be official multi-arch images (e.g., `python:3.11-slim`, `postgres:15-alpine`).
*   **Port Configuration**:
    *   Backend: `8080` (Avoids MacOS AirPlay port 5000 and common 8000).
    *   Frontend: `3000`.
    *   Postgres: `5432`.
    *   Redis: `6379`.
*   **Automation**: `Makefile` included for common tasks (`make dev`, `make db-migrate`, `make test`).

---

## 2. Database Schema Design (ER Concepts)

### 2.1 User & Identity ("Shadow Account" Model)
We separate the physical person (User) from the tournament entity (Player).

*   **User**: Represents a login account (Admin or Participant).
    *   `id`, `username`, `email`, `hashed_password`, `role` (admin/user).
*   **Player**: Represents a participant in the tournament roster.
    *   `id`, `qq_id` (Unique, indexed), `in_game_name`.
    *   `user_id` (FK to User, Nullable).
    *   `data` (JSONB): Stores generic info like "Seed Status", "Initial Group", etc.
*   **Logic**:
    1.  Admin imports CSV -> Creates `Player` rows with `user_id=None`.
    2.  User registers -> Creates `User` row.
    3.  User "Claims" QQ -> Updates `Player.user_id`.

### 2.2 Tournament Structure
The system must handle: Audition (Points) -> Group Stage (Points) -> Elimination (Double Elimination/BO5).

*   **Tournament**: Root entity.
    *   `id`, `name`, `status` (Setup, Active, Completed).
*   **Stage**: A phase of the tournament (e.g., "Audition", "Group Stage Round 1").
    *   `id`, `tournament_id`, `name`, `type` (ROUND_ROBIN, ELIMINATION, DOUBLE_ELIMINATION).
    *   `rules_config` (JSONB): Stores scoring rules (e.g., `{"1st": 9, "2nd": 5...}`, `"ace_bonus": true`).
*   **Phase/Round**: (Optional logical grouping, e.g., "Winner Bracket Round 1").
*   **Group**: A container for a set of players competing together.
    *   `id`, `stage_id`, `name` (e.g., "Group A").
*   **Match**: A scheduled competition event.
    *   `id`, `group_id`, `start_time`.
    *   `state` (Pending, Ready, Finished).
*   **Race**: The atomic unit of competition.
    *   `id`, `match_id`, `race_number` (1, 2, 3...).
*   **RaceResult**: The raw result.
    *   `id`, `race_id`, `player_id`, `rank` (1-9).

### 2.3 Calculated Data (Views/Cached)
*   **MatchScore**: Aggregates `RaceResult`s for a `Match` to determine the match winner.
    *   *Logic*: Sum of points based on `Stage.rules_config` + Bonus checks.
*   **StageRanking**: Aggregates `MatchScore`s to determine who advances to the next Stage.

---

## 3. Core Logic & API Design

### 3.1 Authentication & Binding
*   `POST /api/v1/auth/register`: Create `User`.
*   `POST /api/v1/auth/login`: Get JWT.
*   `POST /api/v1/players/claim`: Input QQ ID to link `User` to `Player`.

### 3.2 Tournament Management
*   `POST /api/v1/tournaments/{id}/import-roster`: Upload CSV. Parses and creates `Player` entries.
*   `POST /api/v1/tournaments/{id}/generate-stage`:
    *   Input: `source_stage_id` (or roster), `algorithm` (e.g., "random_with_seeds").
    *   Output: Creates `Stage`, `Group`s, and `Match`es.

### 3.3 Match Execution & Scoring
*   `GET /api/v1/matches/{id}`: Get match details and players.
*   `POST /api/v1/matches/{id}/result`:
    *   Input: `races`: list of `{ race_number: 1, rankings: [player_id_1, player_id_2...] }`.
    *   Logic:
        1.  Save `RaceResult`s.
        2.  Calculate Points (9-5-3-2-1).
        3.  Check for Ace Bonus (Win count > 50% of races).
        4.  Update Match State to 'Finished'.
*   `POST /api/v1/matches/{id}/override`: Admin "God Mode" to force set a score.

### 3.4 Progression & Tie-Breaking
*   `GET /api/v1/stages/{id}/standings`:
    *   Calculates leaderboard based on:
        1.  Total Points.
        2.  (Tie-breaker 1) Head-to-head (if applicable).
        3.  (Tie-breaker 2) Count of 1st places.
    *   Returns list sorted by Rank.
*   `POST /api/v1/stages/{id}/advance`:
    *   Takes the top N players (configurable) and moves them to a buffer for the next stage.
    *   Allows Admin manual selection if ties are unresolved.

## 4. Extensibility (Bots & OCR)

### 4.1 API-First Approach
*   The API is the source of truth.
*   **QQ Bot**: Can poll `GET /matches?status=pending` to remind players.
*   **OCR Service**:
    *   Can parse a screenshot to extract text.
    *   Maps text names to `Player` IDs.
    *   Calls `POST /matches/{id}/result` automatically.
    *   *Security*: OCR endpoint will require an API Key.

---

## 5. Development Roadmap

1.  **Project Init**: Docker Compose, Makefile, FastAPI skeleton.
2.  **DB Implementation**: SQLModel definitions, Alembic setup.
3.  **Core API (Roster)**: CSV Import, User Claim.
4.  **Core API (Tournament)**: Match Generation, Scoring Logic, Leaderboard Calculation.
5.  **Frontend**: Vue 3 + Naive UI Dashboard.
