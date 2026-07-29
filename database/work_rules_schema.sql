-- Emerald work rules SQL table (MySQL 8.0+)
CREATE TABLE IF NOT EXISTS work_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(40) NOT NULL,
    content_zh TEXT NOT NULL,
    source_document VARCHAR(200) NOT NULL DEFAULT 'Emerald_工作規章_繁體中文譯本.pdf',
    source_page INT NOT NULL DEFAULT 1,
    sort_order INT NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT 1,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY ix_work_rules_code (code),
    KEY ix_work_rules_category (category),
    KEY ix_work_rules_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
