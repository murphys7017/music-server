"""
认证中间件
基于 STATIC_TOKEN 的简单认证机制
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import Config
from app.log import logger


class TokenAuthMiddleware(BaseHTTPMiddleware):
    """
    Token 认证中间件
    验证请求头中的 Authorization Token
    """
    
    # 不需要认证的路径（白名单）
    WHITELIST_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/",
    ]
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            响应对象
        """
        # 检查路径是否在白名单中
        if self._is_whitelisted(request.url.path):
            return await call_next(request)
        
        # 获取 Authorization 头
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            logger.warning(f"未提供认证令牌 | Missing token: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 验证 Token 格式 (Bearer <token>)
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(f"令牌格式错误 | Invalid token format: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication token format. Expected: Bearer <token>"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = parts[1]
        
        # 验证 Token
        if token != Config.STATIC_TOKEN:
            logger.warning(f"令牌验证失败 | Invalid token: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Token 验证通过
        logger.debug(f"认证通过 | Authenticated: {request.url.path}")
        response = await call_next(request)
        return response
    
    def _is_whitelisted(self, path: str) -> bool:
        """
        检查路径是否在白名单中
        
        Args:
            path: 请求路径
            
        Returns:
            是否在白名单中
        """
        # 精确匹配白名单路径
        return path in self.WHITELIST_PATHS
