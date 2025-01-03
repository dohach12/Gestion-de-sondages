import sqlite3

conn = sqlite3.connect('polls.db')
cursor = conn.cursor()

# Définir les requêtes de création de table
create_users_table = """
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role TEXT CHECK(role IN ('Admin', 'User')) DEFAULT 'User',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

create_polls_table = """
CREATE TABLE IF NOT EXISTS Polls (
    poll_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES Users(user_id) ON DELETE SET NULL
);
"""

create_questions_table = """
CREATE TABLE IF NOT EXISTS Questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER,
    question_text TEXT NOT NULL,
    question_type TEXT CHECK(question_type IN ('Multiple Choice', 'Open Text')) NOT NULL,
    FOREIGN KEY (poll_id) REFERENCES Polls(poll_id) ON DELETE CASCADE
);
"""

create_options_table = """
CREATE TABLE IF NOT EXISTS Options (
    option_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    option_text VARCHAR(255) NOT NULL,
    FOREIGN KEY (question_id) REFERENCES Questions(question_id) ON DELETE CASCADE
);
"""

create_responses_table = """
CREATE TABLE IF NOT EXISTS Responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    question_id INTEGER,
    option_id INTEGER,
    response_text TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES Questions(question_id) ON DELETE CASCADE,
    FOREIGN KEY (option_id) REFERENCES Options(option_id) ON DELETE CASCADE
);
"""

create_profiles_table = """
CREATE TABLE IF NOT EXISTS Profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    full_name VARCHAR(100),
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);
"""

create_poll_history_table = """
CREATE TABLE IF NOT EXISTS PollHistory (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    poll_id INTEGER,
    participation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (poll_id) REFERENCES Polls(poll_id) ON DELETE CASCADE
);
"""

# Exécuter les requêtes de création de table
cursor.execute(create_users_table)
cursor.execute(create_polls_table)
cursor.execute(create_questions_table)
cursor.execute(create_options_table)
cursor.execute(create_responses_table)
cursor.execute(create_profiles_table)
cursor.execute(create_poll_history_table)

# Valider les changements
conn.commit()


# Insérer des données dans la table Users
cursor.execute("""
INSERT INTO Users (username, email, password_hash, role)
VALUES (?, ?, ?, ?)
""", ('johndoe', 'john@example.com', 'hashed_password', 'User'))

# Valider les changements
conn.commit()

cursor.execute("SELECT * FROM Users")
users = cursor.fetchall()

for user in users:
    print(user)

conn.close()