"""
登录态管理器
"""
import asyncio
import io
import base64
from datetime import datetime, timedelta
from typing import Optional
from asyncpg import Pool
import qrcode
from qrcode.image.pil import PilImage
from .utils.crypto import get_cipher
from .models import (
    Platform, LoginType, AuthStatus,
    AuthConfigRequest, AuthConfigResult,
    QRCodeResult, AuthStatusResult
)


class AuthManager:
    def __init__(self, db_pool: Pool):
        self.db_pool = db_pool
        self.cipher = get_cipher()
    
    async def configure_cookie(self, request: AuthConfigRequest) -> AuthConfigResult:
        encrypted_cookie = self.cipher.encrypt(request.cookie_value)
        
        is_valid = await self._validate_cookie_with_platform(
            request.platform.value, 
            request.cookie_value
        )
        
        status = AuthStatus.VALID if is_valid else AuthStatus.INVALID
        expires_at = datetime.now() + timedelta(days=30)
        
        query = """
        INSERT INTO crawler_auth_config 
            (platform, login_type, encrypted_cookie, status, expires_at, last_validated_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (platform) DO UPDATE SET
            login_type = EXCLUDED.login_type,
            encrypted_cookie = EXCLUDED.encrypted_cookie,
            status = EXCLUDED.status,
            expires_at = EXCLUDED.expires_at,
            last_validated_at = EXCLUDED.last_validated_at,
            updated_at = CURRENT_TIMESTAMP
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                query,
                request.platform.value,
                request.login_type.value,
                encrypted_cookie,
                status.value,
                expires_at,
                datetime.now()
            )
        
        message = "登录态配置成功" if is_valid else "登录态配置失败：Cookie无效"
        return AuthConfigResult(
            platform=request.platform,
            status=status,
            message=message,
            expires_at=expires_at if is_valid else None
        )
    
    async def generate_qrcode(self, platform: Platform) -> QRCodeResult:
        import uuid
        session_id = str(uuid.uuid4())
        
        if platform == Platform.XIAOHONGSHU:
            login_url = f"https://www.xiaohongshu.com/login?session={session_id}"
        else:
            login_url = f"https://www.zhihu.com/signin?session={session_id}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(login_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        qrcode_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        expires_in = 300
        
        asyncio.create_task(
            self._listen_qrcode_scan(platform, session_id)
        )
        
        return QRCodeResult(
            platform=platform,
            qrcode_url=login_url,
            qrcode_base64=qrcode_base64,
            expires_in=expires_in
        )
    
    async def _listen_qrcode_scan(self, platform: Platform, qrcode_url: str):
        await asyncio.sleep(60)
    
    async def validate_auth(self, platform: Platform) -> AuthStatusResult:
        query = """
        SELECT encrypted_cookie, status, expires_at, last_validated_at
        FROM crawler_auth_config
        WHERE platform = $1
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, platform.value)
            
            if not row:
                return AuthStatusResult(
                    platform=platform,
                    status=AuthStatus.INVALID,
                    message="未配置登录态"
                )
            
            encrypted_cookie = row['encrypted_cookie']
            current_status = AuthStatus(row['status'])
            expires_at = row['expires_at']
            last_validated_at = row['last_validated_at']
            
            try:
                cookie = self.cipher.decrypt(encrypted_cookie)
                is_valid = await self._validate_cookie_with_platform(
                    platform.value, cookie
                )
                
                if not is_valid:
                    new_status = AuthStatus.INVALID
                    message = "登录态已失效"
                elif expires_at and expires_at < datetime.now() + timedelta(days=3):
                    new_status = AuthStatus.EXPIRING
                    message = "登录态即将过期"
                elif expires_at and expires_at < datetime.now():
                    new_status = AuthStatus.EXPIRED
                    message = "登录态已过期"
                else:
                    new_status = AuthStatus.VALID
                    message = "登录态有效"
                
                await conn.execute(
                    """
                    UPDATE crawler_auth_config
                    SET status = $1, last_validated_at = $2, updated_at = CURRENT_TIMESTAMP
                    WHERE platform = $3
                    """,
                    new_status.value,
                    datetime.now(),
                    platform.value
                )
                
                return AuthStatusResult(
                    platform=platform,
                    status=new_status,
                    last_validated_at=datetime.now(),
                    expires_at=expires_at,
                    message=message
                )
                
            except Exception as e:
                return AuthStatusResult(
                    platform=platform,
                    status=AuthStatus.INVALID,
                    message=f"验证失败：{str(e)}"
                )
    
    async def get_decrypted_cookie(self, platform: Platform) -> Optional[str]:
        query = """
        SELECT encrypted_cookie, status
        FROM crawler_auth_config
        WHERE platform = $1
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, platform.value)
            
            if not row:
                return None
            
            status = AuthStatus(row['status'])
            if status in [AuthStatus.EXPIRED, AuthStatus.INVALID]:
                return None
            
            encrypted_cookie = row['encrypted_cookie']
            return self.cipher.decrypt(encrypted_cookie)
    
    async def _validate_cookie_with_platform(
        self, platform: str, cookie: str
    ) -> bool:
        if len(cookie) < 10:
            return False
        return True
