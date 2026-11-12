# Privacy

This plugin collects, stores and sends no data of its own. Its skills are instruction files that run inside your agent; they have no server, account, analytics or telemetry.

What leaves your machine depends on the tools you use with it:

- **Your agent's model provider** receives what you and the skills put into the conversation, including any client records you share. Its terms govern that data. Follow your firm's privacy rules before sharing client information.
- **The bundled MCP server** (`aus-accounting-mcp`) is downloaded from PyPI by `uvx` when your agent first starts it. It then runs on your machine and makes no network request of its own; its results go back to your agent and so to the model provider.
- **Web reads and connectors** that a skill asks your agent to use, such as an ATO page or a ledger connector, send requests to those services under their own terms.

Questions or concerns: open an issue at <https://github.com/ryanduguid/australian-accounting-skills/issues>, or report a security problem as [SECURITY.md](SECURITY.md) describes.
