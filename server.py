import os
from pathlib import Path

import chess
import chess.engine
from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


def find_stockfish_path() -> str | None:
    env_path = os.getenv("STOCKFISH_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    candidates = [
        BASE_DIR / "stockfish-windows-x86-64-avx2" / "stockfish" / "stockfish.exe",
        BASE_DIR / "stockfish-windows-x86-64-avx2" / "stockfish" / "stockfish",
        BASE_DIR / "stockfish.exe",
        BASE_DIR / "stockfish",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
board = chess.Board()
current_elo = 1320

stockfish_path = find_stockfish_path()
engine = None
engine_error = None

if stockfish_path:
    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        engine.configure({"UCI_LimitStrength": True, "UCI_Elo": current_elo})
    except Exception as exc:  # pragma: no cover
        engine_error = str(exc)
else:
    engine_error = "Stockfish binary not found. Set STOCKFISH_PATH or place stockfish binary in repo root."


def get_move_list_san() -> list[str]:
    replay = chess.Board()
    sans: list[str] = []
    for move in board.move_stack:
        sans.append(replay.san(move))
        replay.push(move)
    return sans


def state_payload() -> dict:
    return {
        "fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "is_check": board.is_check(),
        "is_checkmate": board.is_checkmate(),
        "is_stalemate": board.is_stalemate(),
        "is_game_over": board.is_game_over(),
        "result": board.result(claim_draw=True) if board.is_game_over() else None,
        "move_list": get_move_list_san(),
        "elo": current_elo,
    }


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/state")
def state():
    return jsonify(state_payload())


@app.get("/start")
def start():
    board.reset()
    return jsonify({"ok": True, **state_payload()})


@app.get("/end")
def end():
    board.reset()
    return jsonify({"ok": True, **state_payload()})


@app.post("/set_elo")
def set_elo():
    global current_elo
    data = request.get_json(silent=True) or {}
    try:
        elo = int(data.get("elo", current_elo))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "Invalid ELO"}), 400

    elo = max(800, min(3000, elo))
    current_elo = elo

    if engine is None:
        return jsonify({"ok": False, "message": engine_error or "Engine unavailable", "elo": current_elo}), 503

    engine.configure({"UCI_LimitStrength": True, "UCI_Elo": current_elo})
    return jsonify({"ok": True, "elo": current_elo})


def _classify_move(move: chess.Move) -> dict:
    piece = board.piece_at(move.from_square)
    capture = board.is_capture(move)
    castle = piece is not None and piece.piece_type == chess.KING and abs(
        chess.square_file(move.to_square) - chess.square_file(move.from_square)
    ) == 2

    board.push(move)

    return {
        "capture": capture,
        "castle": castle,
        "check": board.is_check(),
        "game_over": board.is_game_over(),
        "checkmate": board.is_checkmate(),
        **state_payload(),
    }


@app.post("/move")
def move():
    data = request.get_json(silent=True) or {}
    move_text = str(data.get("move", "")).strip()

    try:
        move_obj = chess.Move.from_uci(move_text)
    except ValueError:
        return jsonify({"status": "illegal", "reason": "invalid_uci"})

    if board.turn != chess.WHITE:
        return jsonify({"status": "illegal", "reason": "not_player_turn"})

    if move_obj not in board.legal_moves:
        return jsonify({"status": "illegal", "reason": "not_legal"})

    details = _classify_move(move_obj)
    return jsonify({"status": "legal", **details})


@app.get("/ai")
def ai_move():
    if board.is_game_over():
        return jsonify({"status": "done", **state_payload()})

    if board.turn != chess.BLACK:
        return jsonify({"status": "idle", "message": "AI waits for black turn", **state_payload()})

    if engine is None:
        return jsonify({"status": "error", "message": engine_error or "Engine unavailable"}), 500

    result = engine.play(board, chess.engine.Limit(time=0.35))
    details = _classify_move(result.move)
    return jsonify({"status": "ok", "move": result.move.uci(), **details})


@app.get("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "engine_ready": engine is not None,
            "engine_path": stockfish_path,
            "engine_error": engine_error,
            "elo": current_elo,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False, use_reloader=False)
