# Udacity Relational Database FullStack Project
This project is a demonstration of the use of a server-side scripting language 
(in this case Python) with a relational database back-end (in this case PostgreSQL).
The "business logic" in this project explores the concept of _Swiss Tournaments_,
which is a style of competition in which players in a given competition are paired
in each round based on their win/loss record, yet no team actually stops playing
until there is only one team left with no losses. Rather than in single-elimination
tournaments where a team stops playing as soon as they lose a match, teams in
a _Swiss Tournament_ continue playing and will often do so for ranking as 2nd,
3rd, 4th, etc., place. This style of play is a format in use for familiar tournaments
such as the World Cup.

### This project uses a relational database to keep track of:
* A tournament, including the time it occurred and whether it has started/completed.
* The players registered to a given tournament.
* The matches in each round of play, including who won and who lost.

### This project uses server-side scripting to:
* Register a new player by name to an open tournament.
* Record the result of a match between two competitors (winner/loser).
* Determine the way to match each player in the tournament for the next round
base on the rules of _Swiss Tournament_ style of play.
* View the current number of players and the current standings.
* Clear all the matches and/or players for an open tournament (if you want to
start the process over before a winner has been declared).

### The Code Flow
You start by registering multiple players for a new tournament, and for each
player you invoke the `registerPlayer()` function, passing in the name of a
player. Once you've registered every player in your tournament, you begin
competition by recording the result between a head-to-head match of two players.
Invoking `reportMatch()` is done with the unique id of the winning and losing
teams (respectively), and this is performed the number of times it takes until
every player you registered has engaged in a match in this round.

After every player has been matched for a round, it's time to retrieve the 
calculated pairings for the next round. Invoking `swissPairings()` will return
to you the best estimated pairings between players for the next round (you can
invoke this method at the beginning of the tournament too of course, but 
because no player has any wins or losses, the pairing will be completely
arbitrary and no different than if you picked and paired them yourself at random).
For the next round you can now invoke `reportMatch()` once for each player-to-player
pairing returned to you from the swiss pairings result. This process can continue
until there is only one player left who has all wins and no losses.

#### Example:

    # Register players for a tournament
    registerPlayer("Germany")
    registerPlayer("Spain")
    registerPlayer("Japan")
    registerPlayer("Greece")
    
    # Retrieve the ids of each team
    players = playerStandings()
    [player1, player2, player3, player4] = [row[0] for row in players]
    
    # Match players head to head
    reportMatch(player1, player2)
    reportMatch(player3, player4)
    
    # Retrieve the best projected pairings for the next round
    [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4)] = swissPairings()
    
    # Match these players into the next round
    reportMatch(pid1, pid2)
    reportMatch(pid4, pid3)
    ....

### Project dependencies
* Vagrant
* VirtualBox

#### VirtualBox
To run this project, you will need to have VirtualBox installed, which can be
downloaded [here](https://www.virtualbox.org/wiki/Downloads) and installed onto
a machine running Mac OSX, Windows, Linux or Solaris.

#### Vagrant
You will also need to have Vagrant installed, so that the VirtualBox VM can be
configured for the particular tools needed by this project. It can be
downloaded [here](https://www.vagrantup.com/downloads) and installed onto
a machine running Mac OSX, Windows, or Linux.

### Running the project
If the dependencies have been installed, you are ready to run launch the vagrant
virtual machine. 

So first, open the command prompt and navigate inside the project directory to 
the `vagrant/tournament/` folder, then type:

```
vagrant up
```

This will start the virtual machine and may take a minute or so. As long as no 
errors occurred, you should now be able to log into the machine through ssh, so
next type:

```
vagrant ssh
```

This should return a prompt that shows you logged in under the generic username
"vagrant". Now you need to move yourself to the `/vagrant/tournament/` subfolder:

```
cd /vagrant/tournament/
```

Next, we need to create the PostgreSQL database, which is done by importing the 
`tournament.sql` file found in this directory. First though, we have to start
postgres, so type `psql` at the prompt.

Now your commant prompt should have changed from the generic "vagrant" user to the
generic "psql" user. The next step is to import the sql file for creating the database,
so type: 

```
\i tournament.sql
```

The prompt should confirm to you that tables and views have been created. Log out of
the postgres client:

```
\q
```

Now that you're back at the "vagrant" user prompt, we can test out the functionality
in the python scripts contained in the `tournament.py` script by running all the
unit tests in the `tournament_test.py` script. In this last step, we simply type:

```
python tournament_test.py
```

At the prompt you should see the result of all eight unit tests, indicating the logic
contained in the `tournament.py` file was successfully validated!