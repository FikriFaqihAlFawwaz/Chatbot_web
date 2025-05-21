CREATE DATABASE IF NOT EXISTS multimodal_assistant_db;
USE multimodal_assistant_db;

CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_format VARCHAR(20) NOT NULL,
    text_content MEDIUMTEXT,
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS general_logs (
    id VARCHAR(36) PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    metadata JSON
);

CREATE TABLE IF NOT EXISTS coder_logs (
    id VARCHAR(36) PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    metadata JSON
);

CREATE TABLE IF NOT EXISTS rag_logs (
    id VARCHAR(36) PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    metadata JSON
);

CREATE TABLE IF NOT EXISTS ocr_notes (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    extracted_text TEXT NOT NULL,
    save_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS translate_logs (
    id VARCHAR(36) PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    metadata JSON
);

CREATE TABLE IF NOT EXISTS translate_preferences (
    user_id VARCHAR(36),
    length ENUM('standard', 'concise', 'expanded') DEFAULT 'standard',
    tone ENUM('neutral', 'casual', 'formal', 'authoritative', 'empathetic') DEFAULT 'neutral',
    style ENUM('dynamic_equivalence', 'literal', 'creative_adaptation') DEFAULT 'dynamic_equivalence',
    complexity ENUM('standard', 'layman', 'expert') DEFAULT 'standard',
    PRIMARY KEY (user_id)
);