diff --git a/README.md b/README.md
index 3c84412103d6a3b93829c082286794c134c742ae..fef887c9aef9c9b5dbc8f7b62e86db8656273ce4 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,52 @@
-fb# simpleChess
+# simplechess - Chess Server
+
+Flask chess server with an HTML frontend and Stockfish backend.
+
+## Requirements
+
+- Python 3.10+
+- `pip install flask python-chess`
+- Stockfish binary
+
+## Stockfish setup
+
+The server searches for Stockfish in this order:
+
+1. `STOCKFISH_PATH` environment variable
+2. `./stockfish-windows-x86-64-avx2/stockfish/stockfish.exe`
+3. `./stockfish-windows-x86-64-avx2/stockfish/stockfish`
+4. `./stockfish.exe`
+5. `./stockfish`
+
+## Run
+
+```bash
+python server.py
+```
+
+Open: `http://localhost:5050`
+
+## Features
+
+- Legal move validation (illegal moves are rejected)
+- White player vs Black Stockfish
+- ELO slider (800-3000) via `/set_elo`
+- Move list panel
+- Check/checkmate/stalemate detection
+- Checkmate popup + game over messaging
+- Piece move animations (player + AI)
+- Right-click board annotations (red square toggle + square-to-square arrows)
+- Annotation auto-clear after legal moves
+- Mobile-friendly responsive board layout
+- Start/end game buttons with UI feedback
+
+## Endpoints
+
+- `GET /` - UI
+- `GET /state` - current board/game state
+- `GET /start` - reset/start game
+- `GET /end` - reset game
+- `POST /move` - play white move (`{"move":"e2e4"}`)
+- `GET /ai` - ask Stockfish to play black move
+- `POST /set_elo` - set Stockfish ELO (`{"elo":1320}`)
+- `GET /health` - engine health
