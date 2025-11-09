# backend/app/main.py

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.models.database import init_db
from app.api import projects, calculations, mds
import os

# 環境変数
ENV_MODE = os.getenv('ENV_MODE', 'local')  # 'local' or 'web'

app = FastAPI(
    title="Deep Traceability API",
    description="複雑システムの意思決定支援ツール",
    version="1.0.0"
)

# バリデーションエラーハンドラー
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """バリデーションエラーの詳細を返す"""
    print(f"❌ Validation Error: {exc.errors()}")
    print(f"   Body: {exc.body}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )

# CORS設定
origins = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",
]

if ENV_MODE == 'web':
    origins.append("https://your-domain.com")  # 本番環境のドメイン

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データベース初期化
@app.on_event("startup")
async def startup_event():
    """起動時の処理"""
    # データディレクトリ作成
    os.makedirs('./data', exist_ok=True)
    
    # データベーステーブル作成
    init_db()
    print(f"🚀 Server started in {ENV_MODE} mode")


# ルーター登録
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(calculations.router, prefix="/api/calculations", tags=["calculations"])
app.include_router(mds.router, prefix="/api/mds", tags=["mds"])


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Deep Traceability API",
        "mode": ENV_MODE,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok", "mode": ENV_MODE}
