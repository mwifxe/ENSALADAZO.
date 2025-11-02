from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# ============================================================
# ==================== USUARIOS ===============================
# ============================================================

class UserBase(BaseModel):
    """Datos básicos del usuario"""
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario")
    email: EmailStr = Field(..., description="Correo electrónico del usuario")


class UserCreate(UserBase):
    """Esquema para registrar un nuevo usuario"""
    password: str = Field(..., min_length=6, description="Contraseña del usuario")


class UserLogin(BaseModel):
    """Esquema para inicio de sesión"""
    username: str = Field(..., description="Nombre de usuario")
    password: str = Field(..., description="Contraseña del usuario")


class UserResponse(UserBase):
    """Esquema de respuesta al obtener info del usuario"""
    id: int
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Respuesta después del login (con token y rol)"""
    access_token: str
    token_type: str = "bearer"
    username: str
    is_admin: bool


# ============================================================
# ==================== CARRITO DE COMPRAS ====================
# ============================================================

class CartItemCreate(BaseModel):
    """Esquema para crear un item en el carrito"""
    user_session: str = Field(..., description="ID de sesión del usuario")
    product_name: str = Field(..., description="Nombre del producto")
    quantity: int = Field(default=1, ge=1, description="Cantidad del producto")
    unit_price: float = Field(..., gt=0, description="Precio unitario")


class CartItemUpdate(BaseModel):
    """Esquema para actualizar un item en el carrito"""
    quantity: int = Field(..., ge=1, description="Nueva cantidad")


class CartItemResponse(BaseModel):
    """Esquema de respuesta para items del carrito"""
    id: int
    user_session: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================
# ==================== MENSAJES DE CONTACTO ==================
# ============================================================

class ContactMessageCreate(BaseModel):
    """Esquema para crear un mensaje de contacto"""
    name: str = Field(..., min_length=2, max_length=100, description="Nombre del contacto")
    email: EmailStr = Field(..., description="Email del contacto")
    phone: Optional[str] = Field(None, max_length=20, description="Teléfono del contacto")
    message: str = Field(..., min_length=3, max_length=1000, description="Mensaje")


class ContactMessageResponse(BaseModel):
    """Esquema de respuesta para mensajes de contacto"""
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    message: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================
# ==================== ÓRDENES ================================
# ============================================================

class OrderCreate(BaseModel):
    """Esquema para crear una orden"""
    user_session: str = Field(..., description="ID de sesión del usuario")
    customer_name: str = Field(..., min_length=2, max_length=100, description="Nombre del cliente")
    customer_email: EmailStr = Field(..., description="Email del cliente")
    customer_phone: Optional[str] = Field(None, max_length=20, description="Teléfono del cliente")


class OrderResponse(BaseModel):
    """Esquema de respuesta para órdenes"""
    id: int
    user_session: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    total_amount: float
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True