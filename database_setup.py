import sqlite3

def create_all_tables():
    conn = sqlite3.connect('smartfit.db')
    cursor = conn.cursor()

    # 1. user table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        waist_circumference REAL NOT NULL,
        chest_circumference REAL NOT NULL,
        hip_circumference REAL NOT NULL,
        height_cm REAL NOT NULL,
        inseam_cm REAL,
        shoulder_width REAL,
        arm_length REAL,
        thigh_circumference REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Scans_History (
        scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        recommended_size TEXT,
        fabric_type TEXT,
        chart_hash TEXT,
        scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
    )
    ''')

    # 3. fabric table for the logic
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Fabrics (
        fabric_id INTEGER PRIMARY KEY AUTOINCREMENT,
        fabric_name TEXT UNIQUE NOT NULL,
        stretch_factor REAL NOT NULL 
    )
    ''')

    conn.commit()
    conn.close()
    print("the tabels were created secssecfully")

def seed_data():
    # creating the fabric table and user for checking
    conn = sqlite3.connect('smartfit.db')
    cursor = conn.cursor()

    market_fabrics = [
        ('Polyester (Rigid)', 0.0), 
        ('Polyamide / Nylon (Rigid)', 0.0),
        ('Linen', 0.0), 
        ('Rigid Denim', 0.0), 
        ('Silk/Satin', 0.0),
        
        ('Cotton (Woven/Shirt)', 0.02),
        ('Wool', 0.05), 
        ('Lyocell/Tencel', 0.05),
        
        ('Cotton Jersey', 0.15), 
        ('Viscose/Rayon', 0.08), 
        ('Fleece', 0.1),
        ('Ribbed Knit', 0.30),
        
        ('Polyester Blend', 0.07), 
        ('Stretch Denim', 0.12), 
        ('Soft Shell (Ski)', 0.12),
        ('Swimwear Fabric', 0.45),
        ('Lycra/Spandex (Full Stretch)', 0.5)
    ]
    cursor.executemany("INSERT OR REPLACE INTO Fabrics (fabric_name, stretch_factor) VALUES (?, ?)", market_fabrics)
    # user profile check
    try:
        cursor.execute('''
        INSERT OR IGNORE INTO Users (email, full_name, waist_circumference, chest_circumference, 
                                     hip_circumference, height_cm, inseam_cm)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ("test@matchmyfit.com", "Demo User", 70.0, 90.0, 95.0, 165.0, 75.0))
    except sqlite3.Error as e:
        print(f"Error inserting user data: {e}")

    conn.commit()
    conn.close()
    print("done: fabric table amd user")

if __name__ == "__main__":
    print("Starting database initialization...")
    create_all_tables()
    seed_data()
    print("Database setup complete!")