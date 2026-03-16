import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from models import AsyncSessionFactory
from models.user import User

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


# 添加全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 打印详细错误堆栈到控制台
    print(f"请求路径：{request.url.path}")
    print(f"错误类型：{type(exc).__name__}")
    print(f"错误信息：{str(exc)}")
    print("=" * 50)
    print("完整堆栈跟踪:")
    print(traceback.format_exc())
    print("=" * 50)

    # 返回友好的错误响应
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "type": type(exc).__name__,
            "path": request.url.path
        }
    )


# 添加 SQLAlchemy 特定异常处理
from sqlalchemy.exc import SQLAlchemyError


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    print(f"[SQLAlchemy 错误] {str(exc)}")
    print(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "error": "Database Error",
            "message": str(exc),
            "type": type(exc).__name__,
            "path": request.url.path
        }
    )
@asynccontextmanager
async def db_error_handler(operation_name: str):
    """数据库操作异常处理上下文管理器"""
    try:
        yield
    except Exception as e:
        import traceback
        print(f"[{operation_name} 失败] 错误：{str(e)}")
        print(traceback.format_exc())
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"{operation_name} 失败：{str(e)}"
        )


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

async def get_session():
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()

class UserRespSchema(BaseModel):
    id: int
    email: str
    username: str

    class Config:
        from_attributes = True

class UserCreateReqSchema(BaseModel):
    email: str
    username: str
    password: str
    mobile: str

@app.post('/article/add', response_model=UserRespSchema)
async def add_user(user_body: UserCreateReqSchema, session: AsyncSession = Depends(get_session)):
    async with db_error_handler("添加用户"):
        async with session.begin():
            user = User(username=user_body.username, email=user_body.email, password=user_body.password, mobile=user_body.mobile)
            session.add(user)
    return user

from sqlalchemy import delete, select


@app.delete('/user/delete/{user_id}')
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    async with session.begin():
        await session.execute(delete(User).where(User.id == user_id))
        return {"message": "删除成功！"}

# 查找一条数据
@app.get('/select/{user_id}', response_model=UserRespSchema)
async def select_user_by_id(user_id: int, session: AsyncSession = Depends(get_session)):
    async with db_error_handler("查找用户"):
        async with session.begin():
            query = await session.execute(select(User).where(User.id==user_id))
            result = query.scalar() # scalar是获取单个结果
            return result

# 查找多条数据
from typing import List
from sqlalchemy import or_
@app.get('/select', response_model=List[UserRespSchema])
async def select_user(session: AsyncSession=Depends(get_session), q: str|None=None):
    async with session.begin():
        stmt = select(User)\
            .where(or_(User.email.contains(q), User.username.contains(q)))\
            .limit(2).offset(0).order_by(User.id.desc())
        query = await session.execute(stmt)
        result = query.scalars()
        return result


# 1. 查找，修改，再保存
class UserCreateReq(BaseModel):
    email: str
    username: str


class UserResp(BaseModel):
    id: int
    email: str
    username: str


@app.put('/user/update/{user_id}', response_model=UserResp)
async def update_user(request: Request, user_id: int, user_data: UserCreateReq):
    session = request.state.session
    async with session.begin():
        query = await session.execute(select(User).where(User.id==user_id))
        user = query.scalar()
        user.email = user_data.email
        user.username = user_data.username
    return user

# 2. 直接修改
from sqlalchemy import update


class UserCreateReq(BaseModel):
    email: str
    username: str


@app.put('/user/update/{user_id}')
async def update_user(request: Request, user_id: int, user_data: UserCreateReq):
    session = request.state.session
    async with session.begin():
        await session.execute(update(User).where(User.id==user_id).values(**(user_data.model_dump())))
    return {"message": "数据修改成功！"}
