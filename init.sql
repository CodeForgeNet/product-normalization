-- Product Normalization Database Schema
-- PostgreSQL Version

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS normalized_products CASCADE;

-- Create normalized_products table
CREATE TABLE normalized_products (
    id SERIAL PRIMARY KEY,
    fingerprint TEXT UNIQUE NOT NULL,
    vector TEXT NULL,
    brand_name VARCHAR(255) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity VARCHAR(100) NULL,
    category VARCHAR(255) NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(100) NOT NULL,
    platform_url TEXT NULL,
    product_id INTEGER NOT NULL,
    brand_name VARCHAR(255) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    mrp NUMERIC(10, 2) NOT NULL,
    price NUMERIC(10, 2) NULL,
    discount NUMERIC(10, 2) DEFAULT 0,
    quantity VARCHAR(100) NULL,
    category VARCHAR(255) NULL,
    image_url TEXT NOT NULL,
    available BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    search TEXT NULL,
    
    CONSTRAINT fk_product_id FOREIGN KEY (product_id) 
        REFERENCES normalized_products(id) ON DELETE CASCADE
);

-- Create indexes for normalized_products
CREATE INDEX idx_np_brand_name ON normalized_products(brand_name);
CREATE INDEX idx_np_product_name ON normalized_products(product_name);
CREATE INDEX idx_np_fingerprint ON normalized_products(fingerprint);
CREATE INDEX idx_np_category ON normalized_products(category);
CREATE INDEX idx_np_updated_at ON normalized_products(updated_at);

-- Create indexes for products
CREATE INDEX idx_p_platform ON products(platform);
CREATE INDEX idx_p_product_id ON products(product_id);
CREATE INDEX idx_p_brand_name ON products(brand_name);
CREATE INDEX idx_p_product_name ON products(product_name);
CREATE INDEX idx_p_category ON products(category);
CREATE INDEX idx_p_available ON products(available);
CREATE INDEX idx_p_updated_at ON products(updated_at);
CREATE INDEX idx_p_created_at ON products(created_at);
CREATE INDEX idx_p_price ON products(price);
CREATE INDEX idx_p_mrp ON products(mrp);

-- Create composite indexes for common queries
CREATE INDEX idx_np_brand_category ON normalized_products(brand_name, category);
CREATE INDEX idx_p_platform_available ON products(platform, available);

-- Add trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_normalized_products_updated_at 
    BEFORE UPDATE ON normalized_products 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at 
    BEFORE UPDATE ON products 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing
INSERT INTO normalized_products (fingerprint, brand_name, product_name, quantity, category) VALUES
('500_gram_gold_tata_tea', 'tata', 'tea gold', '500_gram', 'Beverages'),
('100_gram_amul_butter', 'amul', 'butter', '100_gram', 'Dairy'),
('100_ml_facewash_himalaya', 'himalaya', 'face wash', '100_ml', 'Personal Care');

-- Verify tables created
SELECT 'Database initialized successfully!' AS status;
SELECT 'Tables created:' AS info;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;