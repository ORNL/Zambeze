--- DDL SQL code for Local Zambeze DB

CREATE TABLE IF NOT EXISTS activity (

    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    created_at INTEGER NOT NULL,
    started_at INTEGER,
    ended_at INTEGER,
    -- campaign_id TEXT NOT NULL, 
    -- depends_on TEXT NOT NULL, -- list of other activity_id's?
    -- user_id INTEGER,
    params TEXT -- JSON object?
    

);
