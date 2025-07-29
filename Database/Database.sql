-- 1. Enable UUID extension if needed (for UUID support)
-- You can use UUID as CHAR(36) in MySQL
-- MySQL doesn't have native UUID types like PostgreSQL

-- 2. USERS TABLE
CREATE TABLE Users (
    user_id CHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. SETTINGS TABLE
CREATE TABLE Settings (
    settings_id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) UNIQUE,
    volume INT CHECK (volume BETWEEN 0 AND 100),
    gender_voice ENUM('male', 'female'),
    provider_voice VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 4. CATEGORIES TABLE
CREATE TABLE Categories (
    category_id CHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- 5. PLACES TABLE
CREATE TABLE Places (
    place_id CHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    alamat TEXT,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    description TEXT,
    category_id CHAR(36),
    created_by CHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES Users(user_id) ON DELETE SET NULL
);

-- 6. FAVORITES TABLE
CREATE TABLE Favorites (
    favorite_id CHAR(36) PRIMARY KEY,
    user_id CHAR(36),
    place_id CHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (place_id) REFERENCES Places(place_id) ON DELETE CASCADE,
    UNIQUE (user_id, place_id) -- Prevent duplicate favorites
);
