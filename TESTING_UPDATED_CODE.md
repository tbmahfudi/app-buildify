# Testing Codex Updates Without Merging Main

You can try the latest Codex changes locally without touching your already-working `main` branch by checking the update out into a throwaway branch (or even a separate worktree). The steps below assume your local clone already tracks your `origin` remote.

## 1. Fetch the Codex commit
The Codex drop you reviewed lives on the `work` branch in the upstream repository and is rooted at commit `77f4be75a2af2934d82186b2a8308a9dd7bbd582`.

```bash
git fetch origin work:codex-tailwind-updates
```

This command downloads the branch and creates a local branch named `codex-tailwind-updates` pointing at the Codex changes.

## 2. Spin up a disposable checkout
You now have two good options:

### Option A – switch branches in-place
```bash
git switch codex-tailwind-updates
```
Run your usual backend/frontend startup commands (e.g., `./manage.sh start` or `python -m http.server 8080` in `frontend/`) to exercise the new code. When you are finished:
```bash
git switch main
```
All of your main-branch work remains untouched.

### Option B – use a Git worktree (keeps two directories side-by-side)
```bash
git worktree add ../app-buildify-codex codex-tailwind-updates
cd ../app-buildify-codex
```
This gives you an isolated directory that tracks the Codex branch while your original clone can stay on `main`. Delete it when you are done:
```bash
cd ../app-buildify
git worktree remove ../app-buildify-codex
```

## 3. Run the stack
With the Codex branch checked out, follow the usual project instructions:

- **Docker path** – `./manage.sh start` (backend on 8000, frontend on 8080)
- **Manual path** – create/activate the virtualenv, run `uvicorn app.main:app --reload --port 8000`, and serve `frontend/` with your preferred static server.

Because you are not merging anything into `main`, you can discard the branch at any time:
```bash
git branch -D codex-tailwind-updates
```

## 4. Reset if needed
If you accidentally switch back to `main` with Codex files still checked out, just run:
```bash
git reset --hard origin/main
```
This returns your local `main` to the upstream state.

With this workflow you can poke at every file that changed in the Codex drop while keeping your `main` branch clean and production-ready.
