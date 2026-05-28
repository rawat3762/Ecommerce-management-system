import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import io

# Database setup
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            image TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    # Cart table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Insert sample products if table is empty
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ('Headphones', 6999, 'https://images.unsplash.com/photo-1599669454699-248893623440?w=400&h=400&fit=crop', 'High-quality wireless headphones with noise cancellation'),
            ('Shoes', 10999, 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop', 'Comfortable running shoes with excellent cushioning'),
            ('Smart Watch', 16999, 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400&h=400&fit=crop', 'Feature-rich smartwatch with health tracking'),
            ('Gaming Mouse', 4199, 'https://images.unsplash.com/photo-1527814050087-3793815479db?w=400&h=400&fit=crop', 'Precision gaming mouse with RGB lighting'),
            ('Backpack', 4999, 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop', 'Durable backpack with laptop compartment'),
            ('Laptop', 74999, 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=400&fit=crop', 'High-performance laptop for work and gaming'),
            ('Smart Television', 58999, 'https://images.unsplash.com/photo-1461151304267-38535e780c79?w=400&h=400&fit=crop', '4K Smart Television with streaming capabilities'),
            ('Bullet Bike', 249999, 'https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=400&h=400&fit=crop', 'Classic bullet bike with powerful engine')
        ]
        cursor.executemany('INSERT INTO products (name, price, image, description) VALUES (?, ?, ?, ?)', sample_products)
    
    # Insert sample user if table is empty
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', 'admin123'))
    
    conn.commit()
    conn.close()

# Helper function for Indian number formatting
def format_indian_currency(amount):
    amount_str = str(int(amount))
    if len(amount_str) <= 3:
        return amount_str
    elif len(amount_str) <= 5:
        return amount_str[:-3] + ',' + amount_str[-3:]
    else:
        # Indian numbering system: first 3 digits, then groups of 2
        last_three = amount_str[-3:]
        remaining = amount_str[:-3]
        # Split remaining into groups of 2 from right
        groups = []
        for i in range(len(remaining), 0, -2):
            groups.insert(0, remaining[max(0, i-2):i])
        formatted_remaining = ','.join(groups)
        return formatted_remaining + ',' + last_three

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return products

def search_products(query):
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE name LIKE ? OR description LIKE ?', 
                           (f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    return products

def add_to_cart(user_id, product_id):
    conn = get_db_connection()
    # Check if product already in cart
    existing = conn.execute('SELECT * FROM cart WHERE user_id = ? AND product_id = ?', 
                          (user_id, product_id)).fetchone()
    if existing:
        conn.execute('UPDATE cart SET quantity = quantity + 1 WHERE user_id = ? AND product_id = ?', 
                     (user_id, product_id))
    else:
        conn.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)', 
                     (user_id, product_id))
    conn.commit()
    conn.close()

def get_cart(user_id):
    conn = get_db_connection()
    cart_items = conn.execute('''
        SELECT cart.*, products.name, products.price, products.image 
        FROM cart 
        JOIN products ON cart.product_id = products.id 
        WHERE cart.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return cart_items

def remove_from_cart(user_id, product_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM cart WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    conn.commit()
    conn.close()

def update_cart_quantity(user_id, product_id, quantity):
    conn = get_db_connection()
    if quantity <= 0:
        conn.execute('DELETE FROM cart WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    else:
        conn.execute('UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?', 
                    (quantity, user_id, product_id))
    conn.commit()
    conn.close()

def authenticate_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                       (username, password)).fetchone()
    conn.close()
    return user

# Page configurations
st.set_page_config(
    page_title="SHOPPING ADDA",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark modern UI
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a2e;
    }
    .stButton>button {
        background-color: #e94560 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 6px 12px !important;
        font-weight: bold !important;
        width: 250px !important;
        height: 35px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .stButton {
        width: 140px !important;
        max-width: 140px !important;
        margin: 0 auto !important;
    }
    div[data-testid="stButton"] {
        width: 140px !important;
        max-width: 140px !important;
        margin: 0 auto !important;
    }
    .stButton>button:hover {
        background-color: #ff6b6b;
    }
    .product-card {
        background-color: #16213e;
        padding: 8px;
        border-radius: 12px;
        margin: 0 auto;
        border: 1px solid #0f3460;
        width: 250px;
        text-align: center;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 150px;
    }
    .cart-item {
        background-color: #16213e;
        padding: 15px;
        border-radius: 8px;
        margin: 5px 0;
        border: 1px solid #0f3460;
    }
    h1, h2, h3 {
        color: #e94560 !important;
    }
    .stTextInput>div>div>input {
        background-color: #16213e;
        color: white;
    }
    div[data-testid="stVerticalBlock"] > div > div {
        display: flex;
        justify-content: center;
    }
    div[data-testid="column"] {
        padding: 0 5px;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
init_db()

# Session state management
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'

# Login page
def login_page():
    st.title("🔐 Login")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("**Username**")
        username = st.text_input("", placeholder="Enter your username", key="username_input", label_visibility="collapsed")
        st.markdown("**Password**")
        password = st.text_input("", type="password", placeholder="Enter your password", key="password_input", label_visibility="collapsed")
        
        if st.button("Login", use_container_width=True):
            user = authenticate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user['id']
                st.session_state.current_page = 'home'
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
        
        st.markdown("---")
        st.info("📝 Demo credentials: Username: admin, Password: admin123")

# Homepage
def home_page():
    st.title("🛒 SHOPPING ADDA")
    st.markdown("---")
    
    # Search bar
    search_query = st.text_input("🔍 Search products", placeholder="Search for products...")
    
    # Get products
    if search_query:
        products = search_products(search_query)
    else:
        products = get_products()
    
    # Display products
    if products:
        cols = st.columns(4)
        for idx, product in enumerate(products):
            col = cols[idx % 4]
            with col:
                try:
                    st.image(product['image'], width=250)
                except:
                    st.error("Image not available")
                
                st.markdown(f"""
                <div class="product-card">
                    <h3 style="color: #e94560; margin-bottom: 10px; font-size: 18px; text-align: center;">{product['name']}</h3>
                    <p style="color: #ffffff; font-size: 14px;">{product['description']}</p>
                    <p style="color: #4ecdc4; font-size: 24px; font-weight: bold; margin: 10px 0;">INR {format_indian_currency(product['price'])}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🛒 Add to Cart", key=f"add_{product['id']}", use_container_width=True):
                    add_to_cart(st.session_state.user_id, product['id'])
                    st.success(f"{product['name']} added to cart!")
                    st.rerun()
    else:
        st.warning("No products found.")

# Shopping cart page
def cart_page():
    st.title("🛍️ Shopping Cart")
    st.markdown("---")
    
    cart_items = get_cart(st.session_state.user_id)
    
    if cart_items:
        total = 0
        for item in cart_items:
            item_total = item['price'] * item['quantity']
            total += item_total
            
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 1])
            with col1:
                try:
                    st.image(item['image'], width=80, caption=item['name'])
                except:
                    st.error("No image")
            with col2:
                st.markdown(f"<h4 style='color: white;'>{item['name']}</h4>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<p style='color: #4ecdc4;'>INR {format_indian_currency(item['price'])}</p>", unsafe_allow_html=True)
            with col4:
                quantity = st.number_input(
                    "Quantity", 
                    min_value=1, 
                    max_value=10, 
                    value=item['quantity'],
                    key=f"qty_{item['id']}"
                )
                if quantity != item['quantity']:
                    update_cart_quantity(st.session_state.user_id, item['product_id'], quantity)
                    st.rerun()
            with col5:
                if st.button("🗑️", key=f"remove_{item['id']}"):
                    remove_from_cart(st.session_state.user_id, item['product_id'])
                    st.rerun()
            
            st.markdown(f"<p style='color: #ffffff; margin-bottom: 20px;'>Item Total: INR {format_indian_currency(item_total)}</p>", unsafe_allow_html=True)
            st.markdown("---")
        
        st.markdown(f"<h2 style='color: #4ecdc4; text-align: right;'>Total: INR {format_indian_currency(total)}</h2>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🛒 Checkout", use_container_width=True):
                st.success("Order placed successfully! Thank you for shopping with us.")
                # Clear cart
                conn = get_db_connection()
                conn.execute('DELETE FROM cart WHERE user_id = ?', (st.session_state.user_id,))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.warning("Your cart is empty.")
        if st.button("Continue Shopping", use_container_width=True):
            st.session_state.current_page = 'home'
            st.rerun()

# Sidebar navigation
def sidebar():
    with st.sidebar:
        st.markdown("# 🛒 SHOPPING ADDA")
        st.markdown("---")
        
        if st.session_state.logged_in:
            st.success(f"✅ Logged in as User {st.session_state.user_id}")
            
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.current_page = 'home'
                st.rerun()
            
            if st.button("🛍️ Cart", use_container_width=True):
                st.session_state.current_page = 'cart'
                st.rerun()
            
            st.markdown("---")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.current_page = 'login'
                st.rerun()
        else:
            st.info("Please login to continue")

# Main app logic
sidebar()

if st.session_state.logged_in:
    if st.session_state.current_page == 'home':
        home_page()
    elif st.session_state.current_page == 'cart':
        cart_page()
    else:
        st.session_state.current_page = 'home'
        home_page()
else:
    login_page()
