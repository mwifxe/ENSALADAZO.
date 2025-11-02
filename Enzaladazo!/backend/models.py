from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


# ==========================
#   MODELO DE USUARIOS
# ==========================
class User(Base):
    """Modelo para usuarios del sistema (clientes o administradores)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    cart_items = relationship("CartItem", back_populates="user")
    orders = relationship("OrderHistory", back_populates="user")

    def __repr__(self):
        return f"<User(username='{self.username}', admin={self.is_admin})>"


# ==========================
#   MODELO DE CARRITO
# ==========================
class CartItem(Base):
    """Modelo para items en el carrito de compras"""
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    # user_id es OPCIONAL para permitir carritos de invitados
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # user_session es obligatorio para identificar carritos
    user_session = Column(String(100), index=True, nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación inversa (opcional)
    user = relationship("User", back_populates="cart_items")


# ==========================
#   MODELO DE MENSAJES
# ==========================
class ContactMessage(Base):
    """Modelo para mensajes de contacto"""
    __tablename__ = "contact_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==========================
#   MODELO DE ÓRDENES
# ==========================
class OrderHistory(Base):
    """Modelo para historial de órdenes"""
    __tablename__ = "order_history"
    
    id = Column(Integer, primary_key=True, index=True)
    # user_id es OPCIONAL para permitir órdenes de invitados
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # user_session identifica la orden
    user_session = Column(String(100), index=True, nullable=False)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    customer_phone = Column(String, nullable=True)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, completed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación inversa (opcional)
    user = relationship("User", back_populates="orders")