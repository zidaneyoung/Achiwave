# Achiwave

Achiwave is a native gamified personal progress application for iOS and Android.

The product turns personal goals into campaigns, quests, streaks, XP, levels, and rule-based achievements. The mobile clients are responsible for input, presentation, native feedback, push notifications, secure local storage, and supported offline queues. The backend remains authoritative for quest validation, progression, XP, levels, streaks, achievements, recurrence, duplicate prevention, and persistence.

## Planned Stack

- React Native, TypeScript, Expo, and Expo Router
- FastAPI, Python, PostgreSQL, SQLAlchemy, Alembic, Redis, Celery, and Celery Beat
- Expo SecureStore, Expo Notifications, Expo Audio, Expo Haptics, Expo FileSystem, SQLite, EAS Build, and EAS Submit

## Repository Structure

- `apps/mobile`: React Native and Expo mobile application
- `apps/backend`: FastAPI backend and Celery application code
- `infrastructure`: local and production infrastructure configuration
- `docs`: architecture, product rules, release, and testing documentation

No user-facing web application is planned for the initial product direction.

## Product rules

Stage 1 domain rules and acceptance evidence are indexed in
[`docs/README.md`](docs/README.md).

## Local development

- [Set up and run the Stage 2 local stack](docs/local-development.md)
- [Review Stage 2 issue-by-issue acceptance evidence](docs/testing/stage-2-acceptance.md)
- [Review the Stage 3 PostgreSQL schema](docs/database/stage-3-schema.md)
- [Review Stage 3 issue-by-issue acceptance evidence](docs/testing/stage-3-acceptance.md)
