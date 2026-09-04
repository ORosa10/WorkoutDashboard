# WorkoutDashboard

Personal Strava MCP connector for a future training dashboard.

The connector is deliberately limited to **sport and training data**. It does not read nutrition, Apple Health, or any other health source.

## Exposed MCP tools

- `connection_status`
- `list_activities`
- `get_activity`
- `get_activity_streams`
- `get_activity_zones`
- `get_athlete_stats`
- `get_training_summary`

## Local setup

1. Create a Strava API application at <https://www.strava.com/settings/api>.
2. Copy `.env.example` to `.env`.
3. Set an access token with `activity:read` or `activity:read_all`.
4. Install dependencies:

   ```bash
   python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```

5. Start the MCP server:

   ```bash
   PYTHONPATH=src python -m workoutdashboard_mcp.server
   ```

The Streamable HTTP MCP endpoint is exposed at `http://localhost:8000/mcp`.

## Deployment

Deploy the repository as a Python web service using the included `Dockerfile`. Set the Strava credentials as platform secrets, never as committed files.

For ChatGPT Work, the deployed HTTPS `/mcp` URL can be registered as a custom MCP app where custom MCP apps are available. ChatGPT connects to remote MCP servers; it cannot directly connect to a local process. See the official OpenAI guidance on [developer mode and MCP apps](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt).

## Security

- Keep the repository private.
- Never commit `.env`, Strava access tokens, refresh tokens, client secrets, or raw activity exports.
- Grant only read scopes.
- Keep write actions out of this first version.
- If a token is exposed, revoke it in Strava and issue a new one.

## Next implementation step

Add a small persistent token store and Strava OAuth callback so the deployed service can authorize the account without manually copying an access token. Until then, the service intentionally requires an environment token.
