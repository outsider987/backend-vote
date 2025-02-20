-- 建立活動資料表
CREATE TABLE IF NOT EXISTS events (
  id UUID PRIMARY KEY,
  event_date DATE NOT NULL,
  member_count INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  options JSONB NOT NULL,
  votes_per_user INT NOT NULL,
  show_count INT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 建立票券資料表
CREATE TABLE IF NOT EXISTS tickets (
  vote_code UUID PRIMARY KEY,
  event_id UUID NOT NULL,
  used BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT fk_event
    FOREIGN KEY(event_id)
      REFERENCES events(id) ON DELETE CASCADE
);

-- 建立投票記錄資料表
CREATE TABLE IF NOT EXISTS votes (
  id UUID PRIMARY KEY,
  event_id UUID NOT NULL,
  vote_code UUID NOT NULL,
  candidate VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT fk_event_vote
    FOREIGN KEY(event_id)
      REFERENCES events(id) ON DELETE CASCADE,
  CONSTRAINT fk_ticket_vote
    FOREIGN KEY(vote_code)
      REFERENCES tickets(vote_code) ON DELETE CASCADE
);
