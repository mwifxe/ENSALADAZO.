// ==============================================
//    CONFIGURACIÓN DEL BACKEND
// ==============================================
const API_URL = 'http://localhost:3004';

// ==============================================
//    SESIÓN DEL USUARIO
// ==============================================
function getUserSession() {
  let session = localStorage.getItem('user_session');
  if (!session) {
    session = 'user_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('user_session', session);
  }
  return session;
}

// ==============================================
//    ELEMENTOS DEL DOM
// ==============================================
const cartContainer = document.getElementById('cart-items');
const cartTotal = document.getElementById('cart-total');
const checkoutBtn = document.getElementById('checkout-btn');

// ==============================================
//    CARGAR Y MOSTRAR CARRITO
// ==============================================
async function loadCart() {
  const userSession = getUserSession();
  try {
    const response = await fetch(`${API_URL}/api/cart/${userSession}`);
    if (!response.ok) throw new Error('Error al cargar el carrito');

    const cartItems = await response.json();
    renderCart(cartItems);
  } catch (error) {
    console.error('❌ Error al cargar carrito:', error);
    showNotification('Error al cargar el carrito', 'error');
    cartContainer.innerHTML = `
      <p class="text-center text-danger mt-5">
        Error al conectar con el servidor. Verifica que el backend esté activo.
      </p>`;
  }
}

// ==============================================
//    RENDERIZAR CARRITO
// ==============================================
function renderCart(items) {
  cartContainer.innerHTML = '';

  if (items.length === 0) {
    cartContainer.innerHTML = `
      <div class="text-center py-5">
        <i data-lucide="shopping-cart" style="width: 80px; height: 80px; color: #ccc;"></i>
        <h4 class="mt-3 text-muted">Tu carrito está vacío</h4>
        <p class="text-muted">Agrega productos desde el menú</p>
        <a href="Menu.html" class="btn btn-success mt-3">Ver Menú</a>
      </div>`;
    cartTotal.textContent = '0.00';
    lucide.createIcons();
    return;
  }

  let total = 0;

  items.forEach(item => {
    total += item.total_price;
    const itemDiv = document.createElement('div');
    itemDiv.className = 'cart-item card mb-3 p-3 shadow-sm';
    itemDiv.innerHTML = `
      <div class="row align-items-center">
        <div class="col-md-6">
          <h5 class="mb-1">${item.product_name}</h5>
          <p class="text-muted mb-0">$${item.unit_price.toFixed(2)} c/u</p>
        </div>
        <div class="col-md-3 d-flex align-items-center">
          <button class="btn btn-sm btn-outline-secondary" onclick="updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
          <span class="mx-3 fw-bold">${item.quantity}</span>
          <button class="btn btn-sm btn-outline-secondary" onclick="updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
        </div>
        <div class="col-md-2 text-success fw-bold">$${item.total_price.toFixed(2)}</div>
        <div class="col-md-1">
          <button class="btn btn-sm btn-danger" onclick="removeItem(${item.id})">
            <i data-lucide="trash-2" style="width: 16px; height: 16px;"></i>
          </button>
        </div>
      </div>`;
    cartContainer.appendChild(itemDiv);
  });

  cartTotal.textContent = total.toFixed(2);
  lucide.createIcons();
}

// ==============================================
//    ACTUALIZAR CANTIDAD
// ==============================================
async function updateQuantity(itemId, newQuantity) {
  if (newQuantity < 1) return removeItem(itemId);

  try {
    const response = await fetch(`${API_URL}/api/cart/${itemId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity: newQuantity })
    });

    if (!response.ok) throw new Error('Error al actualizar cantidad');

    showNotification('Cantidad actualizada', 'success');
    await loadCart(); // 🟢 refresca el carrito visualmente
  } catch (error) {
    console.error('❌ Error:', error);
    showNotification('Error al actualizar cantidad', 'error');
  }
}

// ==============================================
//    ELIMINAR ITEM
// ==============================================
async function removeItem(itemId) {
  if (!confirm('¿Eliminar este producto del carrito?')) return;

  try {
    const response = await fetch(`${API_URL}/api/cart/${itemId}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Error al eliminar producto');

    showNotification('Producto eliminado', 'success');
    await loadCart();
  } catch (error) {
    console.error('❌ Error:', error);
    showNotification('Error al eliminar producto', 'error');
  }
}

// ==============================================
//    CHECKOUT
// ==============================================
checkoutBtn.addEventListener('click', () => {
  const cartItems = cartContainer.querySelectorAll('.cart-item');
  if (cartItems.length === 0) return showNotification('Tu carrito está vacío', 'error');

  const token = localStorage.getItem('token');
  if (!token) {
    if (confirm('Debes iniciar sesión para proceder al pago. ¿Ir a login?')) {
      window.location.href = 'login.html';
    }
    return;
  }

  const checkoutModal = new bootstrap.Modal(document.getElementById('checkoutModal'));
  checkoutModal.show();
});

// ==============================================
//    FORMULARIO DE PAGO
// ==============================================
document.getElementById('checkout-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const btn = e.target.querySelector('button[type="submit"]');
  btn.disabled = true; // 🟢 evitar doble envío
  btn.textContent = 'Procesando...';

  const userSession = getUserSession();
  const name = document.getElementById('name').value.trim();
  const phone = document.getElementById('phone').value.trim();
  const address = document.getElementById('address').value.trim();
  const card = document.getElementById('card-number').value.trim();

  // 🟢 Validaciones simples
  if (!name || !phone || !address || card.length < 12) {
    showNotification('Por favor completa todos los campos correctamente', 'error');
    btn.disabled = false;
    btn.textContent = 'Confirmar Pago';
    return;
  }

  const username = localStorage.getItem('username') || 'invitado@ensaladazo.com';

  const orderData = {
    user_session: userSession,
    customer_name: name,
    customer_email: username,
    customer_phone: phone,
    customer_address: address
  };

  try {
    const response = await fetch(`${API_URL}/api/orders/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orderData)
    });

    if (!response.ok) throw new Error('Error al procesar la orden');

    const order = await response.json();
    console.log('✅ Orden creada:', order);

    bootstrap.Modal.getInstance(document.getElementById('checkoutModal')).hide();
    showNotification('¡Pago realizado con éxito! 🎉', 'success');
    setTimeout(loadCart, 1000);
  } catch (error) {
    console.error('❌ Error:', error);
    showNotification('Error al procesar el pago: ' + error.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Confirmar Pago';
  }
});

// ==============================================
//    NOTIFICACIONES MODERNAS
// ==============================================
function showNotification(message, type = 'info') {
  let container = document.getElementById('notification-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'notification-container';
    container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
    `;
    document.body.appendChild(container);
  }

  const colors = {
    success: '#16a34a',
    error: '#dc2626',
    info: '#2563eb'
  };

  const notification = document.createElement('div');
  notification.textContent = message;
  notification.style.cssText = `
    background: ${colors[type] || colors.info};
    color: #fff;
    padding: 12px 18px;
    margin-top: 10px;
    border-radius: 10px;
    font-weight: 500;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    animation: fadeIn 0.3s ease;
    min-width: 240px;
  `;

  container.appendChild(notification);
  setTimeout(() => {
    notification.style.animation = 'fadeOut 0.4s ease';
    setTimeout(() => notification.remove(), 400);
  }, 3000);
}

// Animaciones 🟢
const style = document.createElement('style');
style.textContent = `
  @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes fadeOut { from { opacity: 1; transform: translateY(0); } to { opacity: 0; transform: translateY(-10px); } }
`;
document.head.appendChild(style);

// ==============================================
//    INICIALIZACIÓN
// ==============================================
document.addEventListener('DOMContentLoaded', () => {
  console.log('🛒 Cart.js iniciado');
  loadCart();
});
