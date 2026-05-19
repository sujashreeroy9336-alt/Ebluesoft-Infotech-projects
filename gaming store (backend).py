from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uuid
import uvicorn
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ DATA STORAGE ============
users_db = {}        # username -> {id, password}
carts_db = {}        # user_id -> [game_ids]
purchased_db = {}    # user_id -> [purchased_game_objects]

# Categories
categories = [
    {"id": 1, "name": "Action", "emoji": "⚡"},
    {"id": 2, "name": "RPG", "emoji": "🗡️"},
    {"id": 3, "name": "Sports", "emoji": "⚽"},
    {"id": 4, "name": "Racing", "emoji": "🏎️"},
    {"id": 5, "name": "Horror", "emoji": "👻"},
]

# Games (25 games, 5 per category)
games = [
    # Action (category_id: 1)
    {"id": 1, "name": "GTA V", "category_id": 1, "price": 29.99},
    {"id": 2, "name": "Call of Duty", "category_id": 1, "price": 59.99},
    {"id": 3, "name": "Far Cry", "category_id": 1, "price": 39.99},
    {"id": 4, "name": "Assassin's Creed", "category_id": 1, "price": 49.99},
    {"id": 5, "name": "Watch Dogs", "category_id": 1, "price": 34.99},
    # RPG (category_id: 2)
    {"id": 6, "name": "Witcher 3", "category_id": 2, "price": 39.99},
    {"id": 7, "name": "Honkai Star Rail", "category_id": 2, "price": 0},
    {"id": 8, "name": "Elden Ring", "category_id": 2, "price": 59.99},
    {"id": 9, "name": "Cyberpunk", "category_id": 2, "price": 49.99},
    {"id": 10, "name": "Genshin Impact", "category_id": 2, "price": 0},
    # Sports (category_id: 3)
    {"id": 11, "name": "FIFA", "category_id": 3, "price": 59.99},
    {"id": 12, "name": "NBA 2K", "category_id": 3, "price": 59.99},
    {"id": 13, "name": "Madden NFL", "category_id": 3, "price": 59.99},
    {"id": 14, "name": "WWE 2K", "category_id": 3, "price": 49.99},
    {"id": 15, "name": "PES", "category_id": 3, "price": 29.99},
    # Racing (category_id: 4)
    {"id": 16, "name": "NFS", "category_id": 4, "price": 39.99},
    {"id": 17, "name": "Forza", "category_id": 4, "price": 59.99},
    {"id": 18, "name": "Gran Turismo", "category_id": 4, "price": 69.99},
    {"id": 19, "name": "F1", "category_id": 4, "price": 49.99},
    {"id": 20, "name": "Hill Climb Racing", "category_id": 4, "price": 0},
    # Horror (category_id: 5)
    {"id": 21, "name": "Resident Evil", "category_id": 5, "price": 39.99},
    {"id": 22, "name": "Outlast", "category_id": 5, "price": 19.99},
    {"id": 23, "name": "Silent Hill", "category_id": 5, "price": 29.99},
    {"id": 24, "name": "Phasmophobia", "category_id": 5, "price": 13.99},
    {"id": 25, "name": "Dead Space", "category_id": 5, "price": 59.99},
]

# Helper function
def get_game_by_id(game_id):
    for game in games:
        if game["id"] == game_id:
            return game.copy()
    return None

# ============ AUTH ENDPOINTS ============

@app.post("/api/register")
async def register(username: str = Query(...), password: str = Query(...)):
    if username in users_db:
        raise HTTPException(400, "Username already exists")
    
    user_id = str(uuid.uuid4())
    users_db[username] = {"id": user_id, "password": password}
    carts_db[user_id] = []
    purchased_db[user_id] = []  # Initialize purchase history
    
    print(f"✅ Registered: {username} (ID: {user_id})")
    return {"success": True, "user_id": user_id, "message": "Registration successful!"}

@app.post("/api/login")
async def login(username: str = Query(...), password: str = Query(...)):
    user = users_db.get(username)
    
    if not user or user["password"] != password:
        raise HTTPException(401, "Invalid username or password")
    
    # Ensure cart and purchase history exist
    if user["id"] not in carts_db:
        carts_db[user["id"]] = []
    if user["id"] not in purchased_db:
        purchased_db[user["id"]] = []
    
    print(f"✅ Logged in: {username} (ID: {user['id']})")
    print(f"   Cart has {len(carts_db[user['id']])} items")
    print(f"   Purchase history has {len(purchased_db[user['id']])} items")
    
    return {"success": True, "user_id": user["id"], "username": username, "message": "Login successful!"}

# ============ GAME ENDPOINTS ============

@app.get("/api/categories")
async def get_categories():
    return categories

@app.get("/api/games/{category_id}")
async def get_games_by_category(category_id: int):
    return [g for g in games if g["category_id"] == category_id]

@app.get("/api/all-games")
async def get_all_games():
    return games

# ============ CART ENDPOINTS ============

@app.post("/api/cart/add")
async def add_to_cart(user_id: str = Query(...), game_id: int = Query(...)):
    print(f"📥 Add to cart: user={user_id}, game={game_id}")
    
    if user_id not in carts_db:
        raise HTTPException(404, "User not found")
    
    game = get_game_by_id(game_id)
    if not game:
        raise HTTPException(404, "Game not found")
    
    if game_id in carts_db[user_id]:
        raise HTTPException(400, "Game already in cart")
    
    carts_db[user_id].append(game_id)
    print(f"✅ Added {game['name']} to cart. Cart now: {carts_db[user_id]}")
    
    return {
        "success": True,
        "message": f"{game['name']} added to cart",
        "cart_count": len(carts_db[user_id])
    }

@app.get("/api/cart/{user_id}")
async def get_cart(user_id: str):
    print(f"📥 Get cart: user={user_id}")
    
    if user_id not in carts_db:
        raise HTTPException(404, "User not found")
    
    cart_items = []
    for game_id in carts_db[user_id]:
        game = get_game_by_id(game_id)
        if game:
            cart_items.append(game)
    
    print(f"📦 Cart has {len(cart_items)} items")
    return cart_items

@app.delete("/api/cart/remove")
async def remove_from_cart(user_id: str = Query(...), game_id: int = Query(...)):
    print(f"📥 Remove from cart: user={user_id}, game={game_id}")
    
    if user_id not in carts_db:
        raise HTTPException(404, "User not found")
    
    if game_id not in carts_db[user_id]:
        raise HTTPException(404, "Game not in cart")
    
    carts_db[user_id].remove(game_id)
    game = get_game_by_id(game_id)
    print(f" Removed {game['name'] if game else game_id} from cart")
    
    return {"success": True, "message": "Removed from cart"}

# ============ PURCHASE ENDPOINTS ============

@app.post("/api/cart/purchase")
async def purchase_cart(user_id: str = Query(...)):
    print(f"💰 PURCHASE requested for user: {user_id}")
    
    if user_id not in carts_db:
        raise HTTPException(404, "User not found")
    
    if not carts_db[user_id]:
        raise HTTPException(400, "Cart is empty")
    
    purchased_games = []
    total = 0
    
    # Get all games from cart
    for game_id in carts_db[user_id]:
        game = get_game_by_id(game_id)
        if game:
            purchased_games.append(game)
            total += game["price"]
    
    # Store in purchase history
    if user_id not in purchased_db:
        purchased_db[user_id] = []
    
    # Add each game to purchase history (avoid duplicates)
    for game in purchased_games:
        # Check if already purchased
        already_purchased = any(g["id"] == game["id"] for g in purchased_db[user_id])
        if not already_purchased:
            purchased_db[user_id].append(game)
    
    # Clear the cart
    carts_db[user_id] = []
    
    print(f"✅ PURCHASE COMPLETE!")
    print(f"   Purchased {len(purchased_games)} games: {[g['name'] for g in purchased_games]}")
    print(f"   Total spent: ${total}")
    print(f"   Total purchase history: {len(purchased_db[user_id])} games")
    
    return {
        "success": True,
        "message": f"✨ Purchase successful! You bought {len(purchased_games)} games for ${total} ✨",
        "games": purchased_games,
        "total": total
    }

@app.get("/api/purchased/{user_id}")
async def get_purchased_games(user_id: str):
    print(f"📥 Get purchase history for user: {user_id}")
    
    if user_id not in purchased_db:
        print(f"No purchase history found for {user_id}, returning empty list")
        return []
    
    print(f"📚 Returning {len(purchased_db[user_id])} purchased games")
    for game in purchased_db[user_id]:
        print(f"   - {game['name']} (${game['price']})")
    
    return purchased_db[user_id]

# ============ DEBUG ENDPOINT ============

@app.get("/api/debug")
async def debug():
    debug_info = {
        "users": {name: user["id"] for name, user in users_db.items()},
        "carts": {user_id: {"count": len(cart), "game_ids": cart} for user_id, cart in carts_db.items()},
        "purchased": {user_id: {"count": len(purchased), "games": [g["name"] for g in purchased]} 
                     for user_id, purchased in purchased_db.items()}
    }
    return debug_info

# ============ FRONTEND ============

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except:
        return HTMLResponse(content="<h1>Place index.html in the same directory</h1>")

# ============ RUN ============

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎮 GAME STORE API STARTING...")
    print("="*60)
    print("📍 Server: http://127.0.0.1:8000")
    print("📖 API Docs: http://127.0.0.1:8000/docs")
    print("🔍 Debug: http://127.0.0.1:8000/api/debug")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)
