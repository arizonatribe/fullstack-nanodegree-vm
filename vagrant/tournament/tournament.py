#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import bleach

# Basic Operational methods and convenience wrappers to cut down on unnecessary repetition in the code
def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=swiss_tournament")

def __commit_and_close(query, params=None):
    """Convenience wrapper for insert/update statements"""
    db = connect()
    cur = db.cursor()
    if params:
        cur.execute(query, params)
    else:
        cur.execute(query)
    db.commit()
    db.close()

def __get_scalar(query):
    """Convenience wrapper for retrieving a single column from a single row in a given query"""
    db = connect()
    cur = db.cursor()
    cur.execute(query)
    result = cur.fetchone()
    db.close()
    if result is not None:
        return result[0]

def __get_results(query):
    """Convenience wrapper for a multi-column and/or multi-row result set for a given query"""
    db = connect()
    cur = db.cursor()
    cur.execute(query)
    results = cur.fetchall()
    db.close()
    return results

def __get_current_tournament():
    return __get_scalar("SELECT id FROM tournaments WHERE is_won IS FALSE AND is_closed IS FALSE;")


def deleteMatches():
    """Remove all the match records from the database."""
    __commit_and_close(
        "DELETE FROM matches "
        "WHERE winner IN ("
        "SELECT p.id FROM players p "
        "INNER JOIN tournaments t ON p.tournament_id = t.id AND t.is_won IS FALSE);"
    )

def deletePlayers():
    """Remove all the player records from the database."""
    __commit_and_close("DELETE FROM players WHERE tournament_id IN (SELECT id FROM tournaments WHERE is_won IS FALSE);")

def countPlayers():
    """Returns the number of players currently registered."""
    return __get_scalar("SELECT * FROM number_of_players_in_tournament;")

def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """

    # Get or create the current tournament
    tournament_id = __get_current_tournament()
    if not tournament_id:
        __commit_and_close("INSERT INTO tournaments (is_won) VALUES (FALSE);")
        tournament_id = __get_current_tournament()

    # Register this new player to the current tournament
    __commit_and_close("INSERT INTO players (name, tournament_id) VALUES (%s, %s)", (bleach.clean(name), tournament_id))

def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """

    # Retrieve the players with their win and match counts
    return __get_results("SELECT * FROM player_standings;")

def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """

    # Close the tournament to which these players belong from any further players registering to it
    __commit_and_close(
        "UPDATE tournaments SET is_closed = TRUE "
        "WHERE is_closed IS FALSE AND id IN ("
        "SELECT tournament_id FROM players "
        "WHERE id IN (%s, %s) "
        "GROUP BY tournament_id);",
        (winner, loser)
    )

    # Report this particular match-up (only if these players are part of an active tournament)
    __commit_and_close(
        "INSERT INTO matches (winner, loser) "
        "SELECT %s, %s FROM tournaments "
        "WHERE id IN ("
        "SELECT tournament_id FROM players "
        "WHERE is_closed IS TRUE AND is_won IS FALSE AND id IN (%s, %s));",
        (winner, loser, winner, loser)
    )

    # If the tournament has a winner (only one player with all wins and no losses), close the tournament
    __commit_and_close(
        "UPDATE tournaments SET is_won = TRUE "
        "WHERE is_won IS FALSE "
        "AND (SELECT * FROM current_tournament_is_won) IS TRUE;"
    )

def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """

    pairings = []

    # Check to see if any matches have occurred yet, if none, just mix the pairings arbitrarily
    if __get_scalar("SELECT SUM(match_count) FROM player_standings;") == 0:
        player_count = countPlayers()
        # Here, we're just cutting the list into two equal halves
        player1s = __get_results("SELECT id, name FROM player_standings LIMIT {0};".format(player_count/2))
        player2s = __get_results("SELECT id, name FROM player_standings LIMIT {0} OFFSET {0};".format(player_count/2))

        if player1s and player2s:
            # now the two halves are zipped together into a new list of tuples
            pairings.extend(map(tuple.__add__, player1s, player2s))
    else:
        # Here, we have a grouping available, by wins and losses, so teams in each group are paired against each other
        groups = __get_results("SELECT * FROM win_loss_groups;")
        for w, l in groups:
            # Find the players that match this particular win/loss group (there will be at least two)
            player_standings = __get_results(
                "SELECT id, name FROM player_standings WHERE wins = {0} AND (match_count - wins) = {1}".format(w, l)
            )

            # now the list of players that fit this win/loss group are zipped together into a new list of tuples
            pairings.extend(
                map(
                    tuple.__add__,
                    player_standings[:len(player_standings)/2],
                    player_standings[len(player_standings)/2:len(player_standings)]
                )
            )

    return pairings
