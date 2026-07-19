"""FastAPI backend for ZBGym Dashboard."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware


@dataclass
class TrainingSession:
    """Training session data."""

    id: str
    env_id: str = "BattleArena-v1"
    algorithm: str = "PPO"
    total_timesteps: int = 0
    current_timestep: int = 0
    episode_count: int = 0
    mean_reward: float = 0.0
    fps: int = 0
    status: str = "idle"
    started_at: float = field(default_factory=time.time)
    logs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ModelInfo:
    """Model information."""

    id: str
    name: str
    path: str
    algorithm: str
    env_id: str
    created_at: float
    file_size: int = 0


class DashboardAPI:
    """Dashboard API manager."""

    def __init__(self) -> None:
        self.app = FastAPI(
            title="ZBGym Dashboard API",
            description="API for ZBGym RL training dashboard",
            version="1.0.0",
        )
        self._sessions: dict[str, TrainingSession] = {}
        self._models: dict[str, ModelInfo] = {}
        self._websockets: list[WebSocket] = []
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Setup CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self) -> None:
        """Setup API routes."""
        from fastapi import APIRouter

        router = APIRouter()

        @router.get("/")
        async def root():
            return {"message": "ZBGym Dashboard API", "version": "1.0.0"}

        @router.get("/health")
        async def health():
            return {"status": "healthy"}

        @router.get("/sessions")
        async def list_sessions():
            return {
                "sessions": [
                    {
                        "id": s.id,
                        "env_id": s.env_id,
                        "algorithm": s.algorithm,
                        "status": s.status,
                        "current_timestep": s.current_timestep,
                        "mean_reward": s.mean_reward,
                    }
                    for s in self._sessions.values()
                ]
            }

        @router.post("/sessions")
        async def create_session(data: dict[str, Any]):
            import uuid
            session_id = str(uuid.uuid4())[:8]
            session = TrainingSession(
                id=session_id,
                env_id=data.get("env_id", "BattleArena-v1"),
                algorithm=data.get("algorithm", "PPO"),
                total_timesteps=data.get("total_timesteps", 1_000_000),
                status="running",
            )
            self._sessions[session_id] = session
            return {"id": session_id, "session": session}

        @router.get("/sessions/{session_id}")
        async def get_session(session_id: str):
            if session_id not in self._sessions:
                return {"error": "Session not found"}
            return self._sessions[session_id]

        @router.delete("/sessions/{session_id}")
        async def delete_session(session_id: str):
            if session_id in self._sessions:
                del self._sessions[session_id]
                return {"message": "Session deleted"}
            return {"error": "Session not found"}

        @router.get("/models")
        async def list_models():
            return {
                "models": [
                    {
                        "id": m.id,
                        "name": m.name,
                        "algorithm": m.algorithm,
                        "env_id": m.env_id,
                        "created_at": m.created_at,
                    }
                    for m in self._models.values()
                ]
            }

        @router.get("/models/{model_id}")
        async def get_model(model_id: str):
            if model_id not in self._models:
                return {"error": "Model not found"}
            return self._models[model_id]

        @router.post("/models/{model_id}/evaluate")
        async def evaluate_model(model_id: str, n_episodes: int = 10):
            if model_id not in self._models:
                return {"error": "Model not found"}
            # Placeholder for evaluation
            return {
                "model_id": model_id,
                "n_episodes": n_episodes,
                "mean_reward": 0.0,
                "std_reward": 0.0,
            }

        @router.get("/stats")
        async def get_stats():
            return {
                "total_sessions": len(self._sessions),
                "total_models": len(self._models),
                "active_sessions": sum(1 for s in self._sessions.values() if s.status == "running"),
            }

        @router.get("/logs")
        async def get_logs(session_id: str | None = None, limit: int = 100):
            logs = []
            if session_id:
                if session_id in self._sessions:
                    logs = self._sessions[session_id].logs[-limit:]
            else:
                for session in self._sessions.values():
                    logs.extend(session.logs[-limit:])
            return {"logs": logs[-limit:]}

        self.app.include_router(router)

        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self._websockets.append(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    # Broadcast to all other clients
                    for ws in self._websockets:
                        if ws != websocket:
                            await ws.send_text(data)
            except WebSocketDisconnect:
                self._websockets.remove(websocket)

    def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all WebSocket clients."""
        import asyncio
        data = json.dumps(message)
        for ws in self._websockets:
            try:
                asyncio.create_task(ws.send_text(data))
            except Exception:
                pass

    def add_session(self, session: TrainingSession) -> None:
        """Add a training session."""
        self._sessions[session.id] = session

    def add_model(self, model: ModelInfo) -> None:
        """Add a model."""
        self._models[model.id] = model

    def get_app(self) -> FastAPI:
        """Get the FastAPI app."""
        return self.app


# Global API instance
api = DashboardAPI()
