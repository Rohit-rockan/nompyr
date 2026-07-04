# Frontend Architecture (Feature-Sliced Design)

We are migrating this codebase to **Feature-Sliced Design (FSD)** to ensure low coupling and high cohesion.
Currently, most logic is contained in `app/main.js`. Over time, this monolithic file should be broken down into the following structure.

## Structure Rules

- **`app/`**: Global settings, routing, providers, and global styles. (Layer 0)
- **`pages/`**: Composition layer. Pages combine features and entities. (Layer 1)
- **`features/`**: User interactions that bring business value (e.g., `SearchAnime`, `WriteReview`). (Layer 2)
- **`entities/`**: Business entities (e.g., `Anime`, `User`). (Layer 3)
- **`shared/`**: Reusable code, UI kits, API clients. (Layer 4)

### 🚨 Golden Rule of FSD
**A module can only import from layers strictly BELOW it.** 
- `features` can import from `entities` and `shared`.
- `features` CANNOT import from `pages` or other `features`.
- This strictly prevents circular dependencies and cascading failures.

## Migration Plan for `main.js`
When refactoring `app/main.js`, extract code into:
1. `shared/api/sourceManager.js` - for the SourceManager class.
2. `features/ContinueWatching/` - for the watch history logic.
3. `features/Reviews/` - for the review submission and rendering.
4. `entities/AnimeCard/` - for the rendering of anime items in the grid.
5. `pages/Home/`, `pages/Watch/`, etc. - for the main layout generation.
