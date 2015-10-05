-- Table definitions for the tournament project.
DROP DATABASE IF EXISTS swiss_tournament;

CREATE DATABASE swiss_tournament;
\c swiss_tournament;

CREATE TABLE tournaments (
  id SERIAL PRIMARY KEY,
  tournament_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_won BOOLEAN NOT NULL DEFAULT FALSE,
  is_closed BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE players (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE NOT NULL
);

CREATE TABLE matches (
  winner INTEGER REFERENCES players(id) ON DELETE CASCADE NOT NULL,
  loser INTEGER REFERENCES players(id) ON DELETE CASCADE NOT NULL,
  time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (winner, loser)
);

CREATE VIEW number_of_players_in_tournament AS
  SELECT COUNT(p.id) tournament_players FROM players p
  INNER JOIN tournaments t ON p.tournament_id = t.id AND t.is_won IS FALSE;

CREATE VIEW player_standings AS
  SELECT p.id, p.name, COALESCE(w.wins, 0) wins, COALESCE(w.wins, 0)+COALESCE(l.losses, 0) match_count
  FROM players p
  INNER JOIN tournaments t on p.tournament_id = t.id AND t.is_won IS FALSE
  LEFT OUTER JOIN (
      SELECT winner, COUNT(*) wins FROM matches GROUP BY winner
  ) w ON p.id = w.winner
  LEFT OUTER JOIN (
      SELECT loser, COUNT(*) losses FROM matches GROUP BY loser
  ) l ON p.id = l.loser
  ORDER BY COALESCE(w.wins, 0) DESC, COALESCE(l.losses, 0);

CREATE VIEW win_loss_groups AS
  SELECT COALESCE(w.wins, 0) wins, COALESCE(l.losses, 0) losses
  FROM players p
  INNER JOIN tournaments t on p.tournament_id = t.id AND t.is_won IS FALSE
  LEFT OUTER JOIN (
      SELECT winner, COUNT(*) wins FROM matches GROUP BY winner
  ) w ON p.id = w.winner
  LEFT OUTER JOIN (
      SELECT loser, COUNT(*) losses FROM matches GROUP BY loser
  ) l ON p.id = l.loser
  GROUP BY COALESCE(w.wins, 0), COALESCE(l.losses, 0)
  ORDER BY 1 DESC, 2;

CREATE VIEW number_of_undefeated_players AS
  SELECT COUNT(winner) win_count FROM (
    SELECT w.winner
    FROM matches w
    INNER JOIN players p ON w.winner = p.id
    INNER JOIN tournaments t ON t.id = p.tournament_id AND t.is_won IS FALSE
    LEFT OUTER JOIN matches l ON w.winner = l.loser
    WHERE l.loser IS NULL
    GROUP BY w.winner
  ) winners;

CREATE VIEW current_tournament_is_won AS
  SELECT (SELECT win_count FROM number_of_undefeated_players) = 1 is_over FROM (
    SELECT SUM(match_count) match_sum, COUNT(id) player_count
    FROM player_standings
  ) p_counts
  WHERE p_counts.match_sum > 0
  AND p_counts.match_sum % p_counts.player_count = 0;
