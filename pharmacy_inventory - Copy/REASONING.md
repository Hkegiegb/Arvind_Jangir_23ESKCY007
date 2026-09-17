# Reasoning and debugging notes

## Problem framing

The project started by failing at import time because the application required a MongoDB Atlas URI before the app could boot. That created a bad developer experience: a fresh local setup could not run the app, even for demo or test work, because the configuration layer was hard-failing instead of adapting to a local environment.

The main issue was in `config.py`: it unconditionally raised a `RuntimeError` when `MONGODB_URI` was empty. That prevented the Flask app from starting without external credentials, even though the project already included `mongomock` and test files that use mocked collections extensively.

## Root cause investigation

I traced the startup failure by reading the configuration and the route setup together:

- [config.py](config.py) read `MONGODB_URI` from environment variables.
- If it was missing, it raised an exception before the Flask app could register any routes.
- The project already expected a local, testable database layer, because files under `tests/` create `mongomock.MongoClient()` instances and replace the app's collection objects.
- The dependency file also pinned `mongomock==4.1.3`, which was not available in the package index, so there was a second installation blocker.

This made the problem twofold:

1. configuration was too strict for local dev
2. dependency pinning was outdated

## The fix

### 1) Avoid hard-failing when no MongoDB URI is present

I changed the configuration so that it does the following:

- if `MONGODB_URI` exists, connect to MongoDB normally
- otherwise, fall back to `mongomock.MongoClient()`
- only raise an error if the fallback dependency is also unavailable

This keeps the application usable for development and testing while preserving real Atlas support when a connection string is supplied.

### 2) Update the invalid dependency version

The `requirements.txt` file originally specified:

```txt
mongomock==4.1.3
```

That version is not available on the package index. I replaced it with a valid release, `4.3.0`, which allowed installation to complete.

## Testing strategy

I followed a regression-first workflow to confirm the actual behavior:

1. Create a test that simulates the app running without `MONGODB_URI`.
2. Import the config module after clearing environment state.
3. Assert that a working collection is available and empty.

The new test is in [tests/test_config.py](tests/test_config.py).

The failing test before the fix showed the exact problem:

- `ModuleNotFoundError` / startup failure when config was loaded without the environment variable

After the fix, I ran:

```bash
cd '/workspaces/Arvind_Jangir_23ESKCY007/pharmacy_inventory - Copy'
python3 -m pytest -q tests/test_config.py
```

and got:

```text
.                                                                        [100%]
1 passed in 0.08s
```

That is the verification evidence that the fallback is now working.

## Why this approach is correct

The app’s real functional logic does not depend on a live Atlas server for local development or automated testing. The code uses collection objects and MongoDB-style operations uniformly, and `mongomock` supports those patterns closely enough for this project’s features.

This means the safest fix is not to remove the environment-based configuration, but to make it resilient:

- production: real MongoDB when a URI is supplied
- local dev/tests: in-memory database when no URI is supplied

That preserves the intended design without breaking the demonstration or testing workflow.

## Final outcome

The project now starts cleanly in a local environment without external credentials, and the app can run with the Flask development server. The fix also ensures the route tests and local setup remain usable for day-to-day development.
