"""
AI Customer Support Chatbot - Demo Server
A standalone demo server that works without external API dependencies.
Perfect for portfolio showcases and local testing.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random
import uuid
import os

# Create FastAPI app
app = FastAPI(
    title="AI Customer Support Chatbot - Demo",
    description="Demo server for AI-powered customer support chatbot",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Pydantic Models
# ============================================================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    customer_id: Optional[str] = None
    channel: str = "web"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str = "active"
    confidence: float = 0.95
    sources: List[str] = []
    suggested_actions: List[Dict[str, str]] = []
    escalate: bool = False

# ============================================================
# Demo Data
# ============================================================

# Simulated conversations storage
conversations: Dict[str, List[Dict]] = {}

# Demo FAQ responses
FAQ_RESPONSES = {
    "return": """I'd be happy to help with returns! 📦

**Our Return Policy:**
• Returns accepted within **30 days** of delivery
• Items must be unused and in original packaging
• Free pickup available in metro cities

**To initiate a return:**
1. Go to "My Orders" in your account
2. Select the order and click "Request Return"
3. Choose pickup or drop-off option

Would you like me to help you start a return for a specific order?""",

    "refund": """Here's our **Refund Policy** 💰

**Refund Timeline:**
• UPI/Wallet: 24-48 hours
• Credit/Debit Card: 5-7 business days
• Net Banking: 5-7 business days

**Refund Eligibility:**
✅ Unused items in original packaging
✅ Defective products (verified)
✅ Wrong item shipped

Once your return is received, we'll process your refund within 2-3 business days.

Do you have a specific order you'd like to check?""",

    "shipping": """Here's our **Shipping Information** 🚚

**Delivery Times:**
• Metro Cities: 2-4 business days
• Tier 2 Cities: 4-6 business days
• Other Areas: 6-10 business days

**Shipping Cost:**
• FREE on orders above ₹999
• ₹99 for orders below ₹999
• Express (24-48hrs): ₹199

You can track your order anytime using your Order ID!

Would you like to track an existing order?""",

    "track": """I can help you track your order! 📍

Please share your **Order ID** (looks like: ORD-2024-XXXXX) and I'll fetch the latest status for you.

**Quick tracking options:**
• Share your Order ID here
• Check "My Orders" in your account
• Click the tracking link in your shipping email""",

    "payment": """We accept multiple **Payment Methods** 💳

**Available Options:**
• UPI: GPay, PhonePe, Paytm
• Cards: Visa, Mastercard, Rupay, AMEX
• Net Banking: All major banks
• Wallets: Paytm, Amazon Pay
• EMI: No-cost EMI on orders above ₹3000
• COD: Cash on Delivery (₹50 fee)

All payments are secured with bank-grade encryption! 🔒

Having trouble with a payment?""",

    "size": """Here's our **Size Guide** 📏

**General Tips:**
• Check the size chart on each product page
• Measure yourself and compare with the chart
• When in doubt, go one size up

**For Audio Products:**
• Headphones: One-size-fits-all with adjustable band
• Earbuds: Comes with S/M/L ear tips

Need help with a specific product size?""",

    "human": """I understand you'd like to speak with a human agent. 🙋

I'm connecting you to our support team now. A human agent will be with you shortly.

**Current wait time:** ~2 minutes

While you wait, is there anything specific I can help document for the agent?""",

    "cancel": """I can help you **Cancel an Order** ❌

**Cancellation Policy:**
• Orders can be cancelled before shipping
• Once shipped, you'll need to initiate a return instead
• Refunds for cancelled orders: 24-48 hours

**To cancel:**
1. Go to "My Orders"
2. Select the order
3. Click "Cancel Order"

Would you like me to help cancel a specific order?"""
}

# Demo order statuses
ORDER_STATUSES = ["processing", "shipped", "out_for_delivery", "delivered"]

# ============================================================
# AI Response Logic (Demo Mode)
# ============================================================

def generate_demo_response(message: str, session_id: str) -> Dict:
    """Generate a demo AI response based on keywords."""
    message_lower = message.lower()
    
    # Check for order ID pattern
    if "ord-" in message_lower or "ord" in message_lower:
        # Extract and generate mock order info
        order_id = extract_order_id(message)
        if order_id:
            return generate_order_response(order_id)
    
    # Check for FAQ matches
    for keyword, response in FAQ_RESPONSES.items():
        if keyword in message_lower:
            actions = get_suggested_actions(keyword)
            escalate = keyword == "human"
            return {
                "response": response,
                "suggested_actions": actions,
                "escalate": escalate,
                "sources": ["faq_knowledge_base"]
            }
    
    # Check for greetings
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    if any(g in message_lower for g in greetings):
        return {
            "response": """Hello! 👋 Welcome to TechStore support!

I'm your AI assistant, here to help you 24/7. I can assist with:

• 📦 **Order Tracking** - Check your order status
• 🔄 **Returns & Refunds** - Process returns
• 🚚 **Shipping** - Delivery information
• ❓ **General Questions** - Product info, sizing, etc.

How can I help you today?""",
            "suggested_actions": [
                {"label": "Track Order", "action": "track_order"},
                {"label": "Return/Refund", "action": "returns"},
                {"label": "Shipping Info", "action": "shipping"}
            ],
            "escalate": False,
            "sources": []
        }
    
    # Check for thanks
    if any(w in message_lower for w in ["thanks", "thank you", "thx", "helpful"]):
        return {
            "response": """You're welcome! 😊 

I'm glad I could help. Is there anything else you'd like to know?

If you're all set, have a great day! Don't hesitate to reach out if you need anything else.""",
            "suggested_actions": [
                {"label": "I'm all set!", "action": "close"},
                {"label": "I have another question", "action": "continue"}
            ],
            "escalate": False,
            "sources": []
        }
    
    # Default response
    return {
        "response": f"""I understand you're asking about: *"{message[:50]}..."*

Let me help you with that! Here are some things I can assist with:

• **Order Status** - Just share your Order ID
• **Returns** - Type "return" to learn about our policy
• **Shipping** - Type "shipping" for delivery info
• **Talk to Human** - Type "human" to connect with an agent

Could you please provide more details or choose one of the options above?""",
        "suggested_actions": [
            {"label": "Track Order", "action": "track_order"},
            {"label": "Returns", "action": "returns"},
            {"label": "Talk to Human", "action": "human"}
        ],
        "escalate": False,
        "sources": []
    }


def extract_order_id(message: str) -> Optional[str]:
    """Extract order ID from message."""
    import re
    patterns = [
        r'(ORD[-_]?\d{4}[-_]?\d+)',
        r'(ORD\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message.upper())
        if match:
            return match.group(1)
    
    # Check for any number that looks like order ID
    numbers = re.findall(r'\d{5,}', message)
    if numbers:
        return f"ORD-{numbers[0]}"
    
    return None


def generate_order_response(order_id: str) -> Dict:
    """Generate mock order status response."""
    # Use order_id to seed random for consistent results
    seed = sum(ord(c) for c in order_id)
    random.seed(seed)
    
    status = random.choice(ORDER_STATUSES)
    
    status_messages = {
        "processing": "Your order is being packed and will ship soon! 📦",
        "shipped": "Your order has been shipped and is on the way! 🚚",
        "out_for_delivery": "Your order is out for delivery today! 🎉",
        "delivered": "Your order was delivered! We hope you love it! ✅"
    }
    
    carriers = ["Delhivery", "BlueDart", "DTDC"]
    carrier = random.choice(carriers)
    tracking = f"{carrier[:2].upper()}{random.randint(1000000000, 9999999999)}"
    
    days = random.randint(2, 5)
    est_delivery = (datetime.now() + timedelta(days=days)).strftime("%B %d, %Y")
    
    response = f"""📦 **Order Status for {order_id.upper()}**

**Status:** {status.replace('_', ' ').title()}
{status_messages[status]}

**Tracking Details:**
• Carrier: {carrier}
• Tracking #: {tracking}
• Estimated Delivery: {est_delivery}

**Order Timeline:**
✅ Order Placed
✅ Order Confirmed
{"✅" if status != "processing" else "⏳"} Shipped
{"✅" if status == "out_for_delivery" or status == "delivered" else "⏳"} Out for Delivery
{"✅" if status == "delivered" else "⏳"} Delivered

Need more help with this order?"""
    
    return {
        "response": response,
        "suggested_actions": [
            {"label": "Track Another Order", "action": "track_order"},
            {"label": "Return This Order", "action": "returns"},
            {"label": "Contact Support", "action": "human"}
        ],
        "escalate": False,
        "sources": ["order_tracking_system"]
    }


def get_suggested_actions(topic: str) -> List[Dict[str, str]]:
    """Get suggested actions based on topic."""
    actions_map = {
        "return": [
            {"label": "Start Return", "action": "start_return"},
            {"label": "Track Order", "action": "track_order"}
        ],
        "refund": [
            {"label": "Check Refund Status", "action": "refund_status"},
            {"label": "Return Policy", "action": "return_policy"}
        ],
        "shipping": [
            {"label": "Track Order", "action": "track_order"},
            {"label": "Delivery Areas", "action": "delivery_areas"}
        ],
        "track": [
            {"label": "My Orders", "action": "my_orders"},
            {"label": "Shipping Info", "action": "shipping"}
        ],
        "payment": [
            {"label": "EMI Options", "action": "emi"},
            {"label": "Payment Failed?", "action": "payment_help"}
        ],
        "human": [
            {"label": "Continue with AI", "action": "continue_ai"}
        ]
    }
    return actions_map.get(topic, [])


# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
async def root():
    """Root endpoint - redirect to demo store."""
    return {"message": "AI Customer Support Chatbot API", "docs": "/docs", "demo": "/demo"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "mode": "demo", "timestamp": datetime.now().isoformat()}


@app.post("/api/v1/chat/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint."""
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"
    
    # Store conversation
    if session_id not in conversations:
        conversations[session_id] = []
    
    conversations[session_id].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    })
    
    # Generate response
    result = generate_demo_response(request.message, session_id)
    
    conversations[session_id].append({
        "role": "assistant",
        "content": result["response"],
        "timestamp": datetime.now().isoformat()
    })
    
    return ChatResponse(
        response=result["response"],
        session_id=session_id,
        status="escalated" if result.get("escalate") else "active",
        confidence=0.95,
        sources=result.get("sources", []),
        suggested_actions=result.get("suggested_actions", []),
        escalate=result.get("escalate", False)
    )


@app.get("/api/v1/chat/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history."""
    if session_id not in conversations:
        return {"session_id": session_id, "messages": [], "status": "not_found"}
    return {
        "session_id": session_id,
        "messages": conversations[session_id],
        "status": "active"
    }


@app.get("/api/v1/orders/{order_id}")
async def get_order(order_id: str):
    """Get order status."""
    seed = sum(ord(c) for c in order_id)
    random.seed(seed)
    
    status = random.choice(ORDER_STATUSES)
    carriers = ["Delhivery", "BlueDart", "DTDC"]
    
    return {
        "order_id": order_id.upper(),
        "status": status,
        "status_description": f"Order is {status.replace('_', ' ')}",
        "items_count": random.randint(1, 3),
        "total": random.randint(1000, 10000),
        "tracking": {
            "carrier": random.choice(carriers),
            "tracking_number": f"DL{random.randint(1000000000, 9999999999)}"
        },
        "estimated_delivery": (datetime.now() + timedelta(days=random.randint(2, 5))).strftime("%B %d, %Y"),
        "can_cancel": status == "processing",
        "can_return": status == "delivered"
    }


@app.get("/api/v1/faqs/")
async def get_faqs():
    """Get FAQs."""
    return [
        {"id": "1", "question": "How do I return a product?", "answer": FAQ_RESPONSES["return"], "category": "returns"},
        {"id": "2", "question": "What is your refund policy?", "answer": FAQ_RESPONSES["refund"], "category": "refunds"},
        {"id": "3", "question": "How long does shipping take?", "answer": FAQ_RESPONSES["shipping"], "category": "shipping"},
        {"id": "4", "question": "How do I track my order?", "answer": FAQ_RESPONSES["track"], "category": "orders"},
        {"id": "5", "question": "What payment methods do you accept?", "answer": FAQ_RESPONSES["payment"], "category": "payments"},
    ]


@app.get("/api/v1/admin/stats")
async def get_stats():
    """Get dashboard stats (demo data)."""
    return {
        "total_conversations": 1247,
        "total_messages": 8723,
        "active_conversations": 15,
        "escalated_conversations": 3,
        "avg_response_time_seconds": 2.5,
        "resolution_rate": 0.87,
        "customer_satisfaction": 4.6,
        "messages_today": 145,
        "conversations_today": 32
    }


@app.get("/api/v1/admin/conversations")
async def get_conversations():
    """Get recent conversations (demo data)."""
    demo_conversations = [
        {"session_id": "sess_abc123", "customer": "John D.", "last_message": "Where is my order?", "status": "active", "time": "2 min ago"},
        {"session_id": "sess_def456", "customer": "Sarah M.", "last_message": "I want to return", "status": "escalated", "time": "15 min ago"},
        {"session_id": "sess_ghi789", "customer": "Mike R.", "last_message": "Thanks for your help!", "status": "closed", "time": "1 hour ago"},
    ]
    return {"conversations": demo_conversations, "count": len(demo_conversations)}


# ============================================================
# Serve Static Files
# ============================================================

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# Serve demo store
@app.get("/demo", response_class=HTMLResponse)
async def demo_store():
    """Serve demo store page."""
    demo_path = os.path.join(FRONTEND_DIR, "demo-store", "index.html")
    if os.path.exists(demo_path):
        with open(demo_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Demo store not found</h1>")


@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/", response_class=HTMLResponse)
async def admin_dashboard():
    """Serve admin dashboard."""
    admin_path = os.path.join(FRONTEND_DIR, "admin-dashboard", "index.html")
    if os.path.exists(admin_path):
        with open(admin_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Admin dashboard not found</h1>")


# Serve admin static files (CSS, JS) at /admin/ path for relative imports
@app.get("/admin/{filename}")
async def admin_static(filename: str):
    """Serve admin dashboard static files."""
    file_path = os.path.join(FRONTEND_DIR, "admin-dashboard", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")


# Serve widget static files
@app.get("/widget/", response_class=HTMLResponse)
async def widget_index():
    """Serve chat widget page."""
    widget_path = os.path.join(FRONTEND_DIR, "chat-widget", "index.html")
    if os.path.exists(widget_path):
        with open(widget_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Chat widget not found</h1>")


@app.get("/widget/{filename}")
async def widget_static(filename: str):
    """Serve chat widget static files."""
    file_path = os.path.join(FRONTEND_DIR, "chat-widget", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")


# ============================================================
# Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Customer Support Chatbot Demo Server...")
    print("=" * 50)
    print("📍 API Docs:      http://localhost:8000/docs")
    print("🏪 Demo Store:    http://localhost:8000/demo")
    print("📊 Admin Panel:   http://localhost:8000/admin")
    print("💬 Chat Widget:   http://localhost:8000/widget/")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
