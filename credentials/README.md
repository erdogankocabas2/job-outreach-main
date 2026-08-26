# Credentials

Place OAuth/API credential files here locally. Never commit them.

## Gmail
Use a Google OAuth Desktop App credential and request the minimum scope needed for sending mail (`gmail.send`).
Expected local paths:
- `credentials/client_secret.json`
- `credentials/token.json` (created after OAuth flow)

The implementation should use Gmail API `users.messages.send` with a MIME multipart message containing the PDF CV attachment.
