# ReasonFuse bounded cloud Operations fixture

This is a deliberately small, in-memory MCP service used only for the
bounded Hosted Agent cloud validation. It exposes:

- `operations___service_status` — read-only status (`UNHEALTHY/g1` initially)
- `operations___restart_service` — one accepted `202` restart that advances to `g2`

Reset is fixture administration outside MCP: send `POST /test/reset` with
`{"mode":"verified"}`, `{"mode":"failed"}`, or `{"mode":"unknown"}`.
It is absent from the agent tool inventory and native approval configuration.

The service does not touch real infrastructure, persist data, or contain
credentials. It is not a production Operations backend.

For local use, `MCP_ALLOWED_HOSTS` defaults to localhost-only host patterns.
For a cloud deployment, set `MCP_ALLOWED_HOSTS` to the deployed MCP host at
deployment time. Do not hardcode temporary cloud hostnames in this repository.
