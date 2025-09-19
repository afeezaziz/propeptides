-- Migration script to create tracker tables
-- Run this script on your database to add the tracker functionality

CREATE TABLE IF NOT EXISTS peptide_cycle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER,
    name VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    target_dosage DECIMAL(10,2),
    frequency VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (product_id) REFERENCES product (id)
);

CREATE TABLE IF NOT EXISTS dosage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id INTEGER NOT NULL,
    dosage_amount DECIMAL(10,2) NOT NULL,
    injection_time DATETIME NOT NULL,
    injection_site VARCHAR(100),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cycle_id) REFERENCES peptide_cycle (id)
);

CREATE TABLE IF NOT EXISTS progress_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id INTEGER NOT NULL,
    entry_date DATE NOT NULL,
    weight DECIMAL(6,2),
    body_fat_percentage DECIMAL(5,2),
    muscle_mass DECIMAL(6,2),
    notes TEXT,
    energy_level INTEGER,
    mood VARCHAR(50),
    side_effects TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cycle_id) REFERENCES peptide_cycle (id)
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_peptide_cycle_user_id ON peptide_cycle(user_id);
CREATE INDEX IF NOT EXISTS idx_peptide_cycle_status ON peptide_cycle(status);
CREATE INDEX IF NOT EXISTS idx_dosage_log_cycle_id ON dosage_log(cycle_id);
CREATE INDEX IF NOT EXISTS idx_dosage_log_injection_time ON dosage_log(injection_time);
CREATE INDEX IF NOT EXISTS idx_progress_entry_cycle_id ON progress_entry(cycle_id);
CREATE INDEX IF NOT EXISTS idx_progress_entry_entry_date ON progress_entry(entry_date);