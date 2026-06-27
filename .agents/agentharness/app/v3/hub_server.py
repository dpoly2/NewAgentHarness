"""ArchonHub hub server entry point."""
from __future__ import annotations

import asyncio
import hmac
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

HERE = Path(__file__).parent
for _path in (HERE, HERE.parent, HERE.parent.parent, HERE.parent.parent.parent):
    if str(_path) not in sys.path:
        sys.path.append(str(_path))

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import RedirectResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn

    FASTAPI_OK = True
except ImportError:
    FASTAPI_OK = False
    uvicorn = None  # type: ignore

if FASTAPI_OK:
    from core.auth import _unhandled_exception_handler, create_access_token, verify_token
    from core.config import APP_VERSION, PID_FILE, SECRET_KEY, WEB_DIR, _JWT_SECRET_DEFAULT, _cors_origins
    from core.database import _config_value, _count_queued_jobs, _init_schema
    from core.hub import build_scheduler, hub
    from routers import (
        agents,
        alpaca,
        capitol_trades,
        auth_routes,
        automations,
        briefing,
        config_api,
        connectors,
        conversations,
        email_cleanup,
        feedback,
        files,
        inez,
        intelligence,
        knowledge,
        memory,
        models_api,
        notifications,
        projects,
        prompt_templates,
        providers,
        plans,
        reports,
        runs,
        sandbox,
        scheduler,
        search,
        skills,
        todos,
        trips,
        users,
        web_search_api,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _init_schema()
        hub._loop = asyncio.get_running_loop()
        _unsafe_ok = os.environ.get('ARCHONHUB_UNSAFE_DEFAULTS', '').lower() in ('1', 'true', 'yes')
        _default_admin_pw = "ArchonHub2024!"
        _secret_insecure = SECRET_KEY == _JWT_SECRET_DEFAULT
        _admin_insecure = os.environ.get('ADMIN_PASSWORD', _default_admin_pw) == _default_admin_pw
        if _secret_insecure or _admin_insecure:
            _msg_parts = []
            if _secret_insecure:
                _msg_parts.append('JWT_SECRET is set to the default insecure value — set JWT_SECRET in .env')
            if _admin_insecure:
                _msg_parts.append('ADMIN_PASSWORD is set to the default insecure value — set ADMIN_PASSWORD in .env')
            _msg = 'SECURITY: ' + '; '.join(_msg_parts) + '.'
            if _unsafe_ok:
                hub.logger.warning(_msg + ' Continuing because ARCHONHUB_UNSAFE_DEFAULTS=1.')
            else:
                hub.logger.error(_msg + ' Set ARCHONHUB_UNSAFE_DEFAULTS=1 to override (dev only).')
                raise SystemExit(1)
        # Start 5 DB-backed worker coroutines (each polls job_queue for unclaimed jobs)
        for _ in range(5):
            hub._worker_tasks.append(asyncio.create_task(hub._db_worker_loop()))
        # Start the WebSocket event broadcast poll (one per process)
        hub._event_poll_task = asyncio.create_task(hub._event_poll_loop())
        # Only one worker process should run APScheduler (distributed lock via hub_config)
        hub._scheduler = build_scheduler(hub)
        if hub._try_scheduler_lock():
            hub._is_scheduler_leader = True
            try:
                hub._scheduler.start()
            except Exception:
                hub.logger.exception('Unable to start scheduler')
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(os.getpid()), encoding='utf-8')
        try:
            yield
        finally:
            for task in hub._worker_tasks:
                task.cancel()
            if hub._event_poll_task:
                hub._event_poll_task.cancel()
            if hub._is_scheduler_leader and hub._scheduler:
                try:
                    hub._scheduler.shutdown()
                except Exception:
                    pass
                hub._release_scheduler_lock_safe()
            hub._executor.shutdown(wait=False)
            if PID_FILE.exists():
                PID_FILE.unlink()

    def build_app() -> FastAPI:
        app = FastAPI(title='ArchonHub', version=APP_VERSION, lifespan=lifespan)
        _wildcard_cors = _cors_origins == ['*']
        app.add_middleware(
            CORSMiddleware,
            allow_origins=_cors_origins,
            allow_credentials=not _wildcard_cors,  # credentials=True is unsafe with allow_origins='*'
            allow_methods=['*'],
            allow_headers=['*'],
        )
        app.add_exception_handler(Exception, _unhandled_exception_handler)
        try:
            app.mount('/web', StaticFiles(directory=str(WEB_DIR), html=True), name='web')
        except Exception:
            pass

        @app.get('/')
        async def root():
            return RedirectResponse(url='/web')

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                first_message = await asyncio.wait_for(websocket.receive_json(), timeout=15.0)
            except asyncio.TimeoutError:
                try:
                    await websocket.close(code=1008)
                except Exception:
                    pass
                return
            except WebSocketDisconnect:
                return
            except Exception:
                try:
                    await websocket.close(code=1008)
                except Exception:
                    pass
                return
            token = None
            if isinstance(first_message, dict) and first_message.get("type") == "auth":
                token = first_message.get("token")
                api_token = first_message.get("api_token")
                if api_token:
                    configured = _config_value("api_token")
                    if configured and hmac.compare_digest(str(api_token), str(configured)):
                        token = create_access_token({"sub": "api-token", "username": "api-token", "user_id": 0, "role": "admin"})
            if not token or not verify_token(token):
                try:
                    await websocket.close(code=1008)
                except Exception:
                    pass
                return
            hub._clients.add(websocket)
            try:
                await websocket.send_json(
                    {
                        "type": "connected",
                        "queue_depth": _count_queued_jobs(),
                        "active_runs": list(hub._active_runs.keys()),
                    }
                )
            except Exception:
                hub._clients.discard(websocket)
                return
            try:
                while True:
                    message = await websocket.receive_json()
                    if not isinstance(message, dict):
                        continue
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                pass
            except Exception:
                try:
                    await websocket.close(code=1008)
                except Exception:
                    pass
            finally:
                hub._clients.discard(websocket)



        for _router in (
            auth_routes.router,
            runs.router,
            todos.router,
            notifications.router,
            trips.router,
            connectors.router,
            projects.router,
            conversations.router,
            agents.router,
            automations.router,
            scheduler.router,
            skills.router,
            memory.router,
            inez.router,
            briefing.router,
            search.router,
            prompt_templates.router,
            knowledge.router,
            files.router,
            feedback.router,
            email_cleanup.router,
            reports.router,
            models_api.router,
            sandbox.router,
            intelligence.router,
            users.router,
            config_api.router,
            providers.router,
            plans.router,
            alpaca.router,
            capitol_trades.router,
            web_search_api.router,
        ):
            app.include_router(_router, prefix='/api')
        return app

    app = build_app()
else:
    def build_app():
        raise SystemExit('FastAPI is not installed')

    app = None


if __name__ == '__main__':
    if not FASTAPI_OK:
        raise SystemExit('FastAPI is not installed')

    import sys as _sys

    _workers = 5
    _loop = 'asyncio' if _sys.platform == 'win32' else 'auto'
    port = int(os.environ.get('HUB_PORT', 8765))
    host = os.environ.get('HUB_HOST', '0.0.0.0')

    uvicorn.run(
        'hub_server:app',
        host=host,
        port=port,
        reload=False,
        workers=_workers,
        log_level='warning',
        access_log=False,
        loop=_loop,
    )
