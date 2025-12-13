-- AI Customer Support Chatbot - Supabase Database Schema
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable vector extension for RAG
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- CONVERSATIONS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    customer_id VARCHAR(100),
    channel VARCHAR(20) NOT NULL DEFAULT 'web',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    agent_id VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_customer_id ON conversations(customer_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);

-- =====================================================
-- MESSAGES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) NOT NULL REFERENCES conversations(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for messages
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);

-- =====================================================
-- FAQS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS faqs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'general',
    keywords TEXT[] DEFAULT '{}',
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for FAQs
CREATE INDEX IF NOT EXISTS idx_faqs_category ON faqs(category);
CREATE INDEX IF NOT EXISTS idx_faqs_is_active ON faqs(is_active);
CREATE INDEX IF NOT EXISTS idx_faqs_priority ON faqs(priority DESC);

-- =====================================================
-- ORDERS TABLE (Demo data)
-- =====================================================
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id VARCHAR(50) UNIQUE NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    items JSONB NOT NULL DEFAULT '[]',
    subtotal DECIMAL(10, 2) NOT NULL,
    shipping_cost DECIMAL(10, 2) DEFAULT 0,
    tax DECIMAL(10, 2) DEFAULT 0,
    total DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50),
    payment_status VARCHAR(30) DEFAULT 'pending',
    shipping_address JSONB,
    tracking JSONB,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ
);

-- Indexes for orders
CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- =====================================================
-- DOCUMENT EMBEDDINGS TABLE (RAG)
-- =====================================================
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create vector similarity search function
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        de.id,
        de.content,
        de.metadata,
        1 - (de.embedding <=> query_embedding) AS similarity
    FROM document_embeddings de
    WHERE 1 - (de.embedding <=> query_embedding) > match_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- =====================================================
-- FEEDBACK TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) REFERENCES conversations(session_id),
    message_id UUID,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- SAMPLE DATA - FAQs
-- =====================================================
INSERT INTO faqs (question, answer, category, keywords, priority) VALUES
(
    'How do I return a product?',
    'To return a product, follow these steps:\n\n1. Log in to your account\n2. Go to "My Orders"\n3. Select the order containing the item you want to return\n4. Click "Request Return"\n5. Select the reason for return\n6. Choose pickup or drop-off\n\nYou have 30 days from delivery to initiate a return. Refunds are processed within 5-7 business days after we receive the item.',
    'returns',
    ARRAY['return', 'refund', 'send back', 'exchange'],
    10
),
(
    'What is your refund policy?',
    'Our refund policy:\n\n• **Full Refund**: Unused items in original packaging within 30 days\n• **Partial Refund**: Items with minor defects or opened packaging\n• **No Refund**: Customized items, perishables, or items past 30 days\n\nRefunds are credited to the original payment method within 5-7 business days.',
    'refunds',
    ARRAY['refund', 'money back', 'return policy'],
    10
),
(
    'How long does shipping take?',
    'Shipping times vary by location:\n\n• **Metro Cities**: 2-4 business days\n• **Tier 2 Cities**: 4-6 business days\n• **Other Areas**: 6-10 business days\n\nExpress shipping (available in select areas) delivers within 24-48 hours for an additional fee.',
    'shipping',
    ARRAY['shipping', 'delivery', 'when arrive', 'how long'],
    9
),
(
    'How do I track my order?',
    'You can track your order in several ways:\n\n1. **Website**: Log in > My Orders > Select Order > View Tracking\n2. **Email**: Click the tracking link in your shipping confirmation email\n3. **SMS**: Reply TRACK to any order update SMS\n4. **This Chat**: Just share your order ID (e.g., ORD-12345) and I''ll look it up for you!',
    'orders',
    ARRAY['track', 'tracking', 'where is my order', 'order status'],
    10
),
(
    'What payment methods do you accept?',
    'We accept the following payment methods:\n\n• **UPI**: Google Pay, PhonePe, Paytm, BHIM\n• **Cards**: Visa, Mastercard, Rupay, AMEX\n• **Net Banking**: All major banks\n• **Wallets**: Paytm, Amazon Pay, Mobikwik\n• **EMI**: No-cost EMI on orders above ₹3000\n• **COD**: Cash on Delivery (₹50 fee, max ₹25,000)',
    'payments',
    ARRAY['payment', 'pay', 'upi', 'card', 'emi', 'cod'],
    8
),
(
    'How do I cancel my order?',
    'To cancel an order:\n\n1. Go to "My Orders"\n2. Select the order you want to cancel\n3. Click "Cancel Order"\n4. Select reason and confirm\n\n**Note**: Orders can only be cancelled before shipping. Once shipped, you''ll need to initiate a return instead. Refunds for cancelled orders are processed within 24-48 hours.',
    'orders',
    ARRAY['cancel', 'cancellation', 'cancel order'],
    9
),
(
    'Do you have a size guide?',
    'Yes! Each product page has a detailed size guide. Here are some general tips:\n\n• **Clothing**: Measure your chest, waist, and hips. Compare with the size chart.\n• **Shoes**: Measure your foot length in cm. We recommend going half a size up if between sizes.\n• **Accessories**: Check individual product dimensions.\n\nStill unsure? Our AI can help you find your perfect size - just tell me what you''re looking for!',
    'products',
    ARRAY['size', 'sizing', 'fit', 'measurements'],
    7
),
(
    'How do I contact customer support?',
    'You can reach us through:\n\n• **This Chat**: I''m here 24/7! For complex issues, type "human" to connect with an agent.\n• **Email**: support@example.com (Response within 24 hours)\n• **Phone**: 1800-XXX-XXXX (10 AM - 8 PM, Mon-Sat)\n• **WhatsApp**: +91 XXXXX XXXXX\n\nWe''re here to help!',
    'general',
    ARRAY['contact', 'support', 'help', 'customer service', 'human'],
    10
);

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================
-- Enable RLS on tables
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE faqs ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_embeddings ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your auth setup)
-- For demo, allowing all operations
CREATE POLICY "Allow all for conversations" ON conversations FOR ALL USING (true);
CREATE POLICY "Allow all for messages" ON messages FOR ALL USING (true);
CREATE POLICY "Allow all for faqs" ON faqs FOR ALL USING (true);
CREATE POLICY "Allow all for orders" ON orders FOR ALL USING (true);
CREATE POLICY "Allow all for embeddings" ON document_embeddings FOR ALL USING (true);

-- =====================================================
-- TRIGGERS
-- =====================================================
-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER faqs_updated_at
    BEFORE UPDATE ON faqs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
