from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import projects
from app.api.routes import qa_sessions
from app.api.routes import gateway
from app.api.routes import code_repos

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/v1")
app.include_router(qa_sessions.router, prefix="/api/v1")  # /api/v1/refine
app.include_router(qa_sessions.projects_router, prefix="/api/v1")  # /api/v1/projects/{id}/qa-sessions
app.include_router(gateway.router, prefix="/api/v1")  # /api/v1/requirements/{id}/gateway
app.include_router(code_repos.router, prefix="/api/v1")  # /api/v1/code


@app.get("/")
async def root():
    return {
        "message": "AI Agent Builder Pipeline API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
