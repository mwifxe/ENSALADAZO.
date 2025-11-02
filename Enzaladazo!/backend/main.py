from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os

from database import engine, get_db, Base
from models import CartItem, ContactMessage, OrderHistory, User
from schemas import (
    CartItemCreate, CartItemResponse, CartItemUpdate,
    ContactMessageCreate, ContactMessageResponse,
    OrderCreate, OrderResponse,
    UserCreate, UserLogin, UserResponse, TokenResponse
)

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Inicializar FastAPI
app = FastAPI(
    title="Ensaladazo! API",
    description="Backend para el sistema de ventas de ensaladas saludables",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== CONFIGURACIÓN AUTH ====================

SECRET_KEY = os.getenv("SECRET_KEY", "superclaveultrasecreta_ensaladazo")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 día

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ---------- UTILIDADES ----------
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Obtiene el usuario actual a partir del token JWT"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# ==================== RUTAS DE SALUD ====================

@app.get("/")
def read_root():
    """Endpoint raíz para verificar que el API está funcionando"""
    return {
        "message": "Bienvenido a Ensaladazo! API",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    """Verificar el estado de salud del API"""
    return {"status": "healthy"}


# ==================== CARRITO DE COMPRAS ====================

@app.post("/api/cart/add", response_model=CartItemResponse)
def add_to_cart(item: CartItemCreate, db: Session = Depends(get_db)):
    """Agregar un producto al carrito"""
    
    # Verificar si el producto ya existe en el carrito para este usuario
    existing_item = db.query(CartItem).filter(
        CartItem.user_session == item.user_session,
        CartItem.product_name == item.product_name
    ).first()
    
    if existing_item:
        # Si existe, incrementar la cantidad
        existing_item.quantity += item.quantity
        existing_item.total_price = existing_item.quantity * existing_item.unit_price
        db.commit()
        db.refresh(existing_item)
        return existing_item
    
    # Si no existe, crear nuevo item
    total_price = item.quantity * item.unit_price
    db_item = CartItem(
        user_session=item.user_session,
        product_name=item.product_name,
        quantity=item.quantity,
        unit_price=item.unit_price,
        total_price=total_price
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/api/cart/{user_session}", response_model=List[CartItemResponse])
def get_cart(user_session: str, db: Session = Depends(get_db)):
    """Obtener todos los items del carrito de un usuario"""
    items = db.query(CartItem).filter(
        CartItem.user_session == user_session
    ).all()
    return items


@app.put("/api/cart/{item_id}", response_model=CartItemResponse)
def update_cart_item(item_id: int, item_update: CartItemUpdate, db: Session = Depends(get_db)):
    """Actualizar la cantidad de un item en el carrito"""
    db_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Item no encontrado en el carrito")
    
    db_item.quantity = item_update.quantity
    db_item.total_price = db_item.quantity * db_item.unit_price
    
    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete("/api/cart/{item_id}")
def remove_from_cart(item_id: int, db: Session = Depends(get_db)):
    """Eliminar un item del carrito"""
    db_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Item no encontrado en el carrito")
    
    db.delete(db_item)
    db.commit()
    return {"message": "Item eliminado del carrito"}


@app.delete("/api/cart/clear/{user_session}")
def clear_cart(user_session: str, db: Session = Depends(get_db)):
    """Vaciar todo el carrito de un usuario"""
    db.query(CartItem).filter(CartItem.user_session == user_session).delete()
    db.commit()
    return {"message": "Carrito vaciado exitosamente"}


@app.get("/api/cart/{user_session}/total")
def get_cart_total(user_session: str, db: Session = Depends(get_db)):
    """Obtener el total del carrito"""
    items = db.query(CartItem).filter(CartItem.user_session == user_session).all()
    total = sum(item.total_price for item in items)
    item_count = sum(item.quantity for item in items)
    
    return {
        "total": round(total, 2),
        "item_count": item_count,
        "items": len(items)
    }


# ==================== ÓRDENES ====================

@app.post("/api/orders/create", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """Crear una orden desde el carrito"""
    
    # Obtener items del carrito
    cart_items = db.query(CartItem).filter(
        CartItem.user_session == order.user_session
    ).all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="El carrito está vacío")
    
    # Calcular total
    total = sum(item.total_price for item in cart_items)
    
    # Crear orden
    db_order = OrderHistory(
        user_session=order.user_session,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_phone=order.customer_phone,
        total_amount=total,
        status="pending"
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Limpiar carrito después de crear la orden
    db.query(CartItem).filter(CartItem.user_session == order.user_session).delete()
    db.commit()
    
    return db_order


@app.get("/api/orders/{user_session}", response_model=List[OrderResponse])
def get_user_orders(user_session: str, db: Session = Depends(get_db)):
    """Obtener historial de órdenes de un usuario"""
    orders = db.query(OrderHistory).filter(
        OrderHistory.user_session == user_session
    ).order_by(OrderHistory.created_at.desc()).all()
    return orders


# ==================== CONTACTO ====================

@app.post("/api/contact", response_model=ContactMessageResponse)
def submit_contact(message: ContactMessageCreate, db: Session = Depends(get_db)):
    """Recibir y guardar mensaje de contacto"""
    
    db_message = ContactMessage(
        name=message.name,
        email=message.email,
        message=message.message,
        phone=message.phone
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message


@app.get("/api/contact/messages", response_model=List[ContactMessageResponse])
def get_all_messages(db: Session = Depends(get_db)):
    """Obtener todos los mensajes de contacto (admin)"""
    messages = db.query(ContactMessage).order_by(
        ContactMessage.created_at.desc()
    ).all()
    return messages


@app.get("/api/contact/messages/{message_id}", response_model=ContactMessageResponse)
def get_message(message_id: int, db: Session = Depends(get_db)):
    """Obtener un mensaje específico"""
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    return message


@app.delete("/api/contact/messages/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db)):
    """Eliminar un mensaje de contacto"""
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    db.delete(message)
    db.commit()
    return {"message": "Mensaje eliminado exitosamente"}


# ==================== PRODUCTOS ====================

@app.get("/api/products")
def get_products():
    """Obtener catálogo de productos disponibles"""
    products = [
        {
            "id": 1,
            "name": "Ensalada CobbFit",
            "description": "Mezcla fresca de lechuga, tomate, cebolla morada, aguacate, queso mozarella, tocino, pechuga de pollo, huevo duro, y rodajas de pan tostado.",
            "price": 4.00,
            "category": "ensalada",
            "available": True
        },
        {
            "id": 2,
            "name": "Ensalada César",
            "description": "Una ensalada a base de lechuga, pechuga de pollo, huevo duro, tomate, queso mozarella y rodajas de pan tostado.",
            "price": 3.25,
            "category": "ensalada",
            "available": True
        },
        {
            "id": 3,
            "name": "Ensalada Tropical",
            "description": "Mix de lechugas, pollo a la parrilla, piña fresca, mango, aguacate, almendras tostadas y vinagreta de cítricos.",
            "price": 3.75,
            "category": "ensalada",
            "available": True
        },
        {
            "id": 4,
            "name": "Ensalada Mediterránea",
            "description": "Lechugas mixtas, tomates cherry, pepino, aceitunas negras, queso feta, cebolla morada y pollo marinado.",
            "price": 3.50,
            "category": "ensalada",
            "available": True
        },
        {
            "id": 5,
            "name": "Smoothie Verde",
            "description": "Batido energizante de espinaca, manzana verde, jengibre y menta",
            "price": 2.75,
            "category": "bebida",
            "available": True
        }
    ]
    return products


# ==================== ENDPOINTS DE USUARIOS ====================

@app.post("/api/auth/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario"""
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Usuario o correo ya registrado")

    hashed_password = hash_password(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        is_admin=False  # Por defecto todos son usuarios normales
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/api/auth/login", response_model=TokenResponse)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Iniciar sesión y generar token JWT"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "is_admin": user.is_admin
    }


@app.get("/api/auth/users/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Obtener datos del usuario autenticado"""
    return current_user


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3004))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)