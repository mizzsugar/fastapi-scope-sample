
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt

from models import User, Article, get_db
from schemas import UserInDB



SECRET_KEY = "your-secret-key"  # 本来は環境変数にするけど割愛
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "articles:read": "記事の閲覧",
        "articles:write": "記事の作成・編集",
        "articles:delete": "記事の削除",
        "articles:admin": "記事の管理者権限"
    }
)


def get_user_scopes(user_id: int, db: Session) -> list[str]:
    # 余力があれば、RedisでScopeのキャッシュをするといいかも
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    
    scopes = [scope.name for scope in user.scopes]
    return scopes


def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    user_scopes = get_user_scopes(user.id, db)
    
    for required_scope in security_scopes.scopes:
        if required_scope not in user_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Not enough permissions",
                    "required_scopes": security_scopes.scopes,
                    "user_scopes": user_scopes
                },
                headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
            )
    
    return UserInDB(
        id=user.id,
        username=user.username,
        scopes=user_scopes
    )


app = FastAPI()


@app.get("/articles/")
def list_articles(
    current_user: UserInDB = Security(get_current_user, scopes=["articles:read"]),
    db: Session = Depends(get_db)
):
    # 記事の一覧取得は省略
    return {"message": "Articles list", "user_scopes": current_user.scopes}


@app.post("/articles/")
def create_article(
    current_user: UserInDB = Security(get_current_user, scopes=["articles:write"]),
    db: Session = Depends(get_db)
):
    # 記事の作成は省略
    return {"message": "Article created", "user_scopes": current_user.scopes}


@app.delete("/articles/{article_id}")
def delete_article(
    article_id: int,
    current_user: UserInDB = Security(get_current_user, scopes=["articles:delete"]),
    db: Session = Depends(get_db)
):
    user_scopes = get_user_scopes(current_user.id, db)

    if "articles:admin" not in user_scopes:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article or article.author_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only delete your own articles"
            )
    
    return {"message": "Article deleted", "user_scopes": user_scopes}
