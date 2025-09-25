-- Postgres schema
CREATE TABLE multiplication_table (
  id SERIAL PRIMARY KEY,
  multiplicand SMALLINT NOT NULL,
  multiplier   SMALLINT NOT NULL,
  product      SMALLINT NOT NULL,
  UNIQUE (multiplicand, multiplier)
);

CREATE INDEX idx_mt_product ON multiplication_table (product);
CREATE INDEX idx_mt_pair ON multiplication_table (multiplicand, multiplier);

CREATE TABLE user_progress (
  user_id      INT NOT NULL,
  multiplicand SMALLINT NOT NULL,
  multiplier   SMALLINT NOT NULL,
  attempts     INT DEFAULT 0,
  correct      INT DEFAULT 0,
  last_attempt TIMESTAMP,
  PRIMARY KEY (user_id, multiplicand, multiplier)
);
CREATE INDEX idx_up_user ON user_progress (user_id);
