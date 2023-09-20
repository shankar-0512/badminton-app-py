FUNCTION generate_pairing():

    FETCH all active players who are not playing
    IF number of such players is less than 4:
        RETURN error response
    
    SORT players based on unmatched priority

    INITIALIZE empty teams list
    FOR each team to be generated:
        INITIALIZE two empty teams as team1 and team2
        FOR each team:
            FOR two players:
                SELECT player avoiding ones with prior history with existing team members
                ADD selected player to team

        SORT all four selected players based on uncertainty and elo_rating
        DIVIDE the sorted players into two balanced teams (min_diff_team1 and min_diff_team2)
        ADD these teams to the teams list

    UPDATE database with selected player's statuses
    UPDATE or CREATE player history based on the generated teams

    CHECK for available court
    IF court available:
        UPDATE court status to occupied

    FETCH updated court statuses
    DISPATCH WebSocket messages to update frontend
    RETURN success response with teams and court status




FUNCTION update_elo(request):

    PARSE request to get team details

    INITIALIZE constants: K, F1, F2

    FUNCTION calculate_average_rating(players):
        RETURN average ELO rating of players

    COMPUTE average ratings for winners and losers

    CALCULATE expected scores for both winners and losers

    FUNCTION handle_players(team, outcome, expected_outcome):
        FOR EACH player in team:
            COMPUTE rating change based on outcome and expected outcome
            UPDATE player's details in the database
            NOTIFY frontend about updates

    HANDLE winners using handle_players() with outcome as 1
    HANDLE losers using handle_players() with outcome as 0

    RETURN success response with updated details







