from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random

app = Flask(__name__)
DATABASE = 'players.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_players():
    conn = get_db_connection()
    players = conn.execute('SELECT * FROM players ORDER BY year, gender, level').fetchall()
    conn.close()
    return players

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/players')
def players():
    players = get_players()
    return render_template('players.html', players=players)

@app.route('/add_player', methods=['POST'])
def add_player():
    name = request.form['name']
    gender = request.form['gender']
    year = int(request.form['year'])
    level = int(request.form['level'])
    active = 1 if 'active' in request.form else 0
    conn = get_db_connection()
    conn.execute('INSERT INTO players (name, gender, year, level, active) VALUES (?, ?, ?, ?, ?)',
                 (name, gender, year, level, active))
    conn.commit()
    conn.close()
    return redirect(url_for('players'))

@app.route('/toggle_active/<int:player_id>', methods=['POST'])
def toggle_active(player_id):
    conn = get_db_connection()
    player = conn.execute('SELECT active FROM players WHERE id = ?', (player_id,)).fetchone()
    new_active_status = 0 if player['active'] else 1
    conn.execute('UPDATE players SET active = ? WHERE id = ?', (new_active_status, player_id))
    conn.commit()
    conn.close()
    return redirect(url_for('players'))

@app.route('/edit_player/<int:player_id>', methods=['GET', 'POST'])
def edit_player(player_id):
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        gender = request.form['gender']
        year = int(request.form['year'])
        level = int(request.form['level'])
        active = 1 if 'active' in request.form else 0
        conn.execute('UPDATE players SET name = ?, gender = ?, year = ?, level = ?, active = ? WHERE id = ?',
                     (name, gender, year, level, active, player_id))
        conn.commit()
        conn.close()
        return redirect(url_for('players'))
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    conn.close()
    return render_template('edit_player.html', player=player)

@app.route('/delete_player/<int:player_id>')
def delete_player(player_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM players WHERE id = ?', (player_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('players'))

def organize_matches():
    players = get_players()
    active_players = [player for player in players if player['active']]

    # 性別ごとに分ける
    males = [player for player in active_players if player['gender'] == '男']
    females = [player for player in active_players if player['gender'] == '女']

    male_matches, male_remaining = create_matches_for_gender(males)
    female_matches, female_remaining = create_matches_for_gender(females)

    return {
        'male_matches': male_matches,
        'female_matches': female_matches,
        'male_remaining': male_remaining,
        'female_remaining': female_remaining
    }

def create_matches_for_gender(players):
    groups = {
        "1-2": [player for player in players if player['level'] in [1, 2]],
        "3-4": [player for player in players if player['level'] in [3, 4]],
        "5-8": [player for player in players if player['level'] in [5, 6, 7, 8]],
        "9-10": [player for player in players if player['level'] in [9, 10]]
    }

    matches = []
    remaining_players = []

    # 同じグループ内で試合を組む
    for group_name, group in groups.items():
        if group_name == "1-2":
            # レベル1-2のプレイヤーはレベル5以上のプレイヤーと組まなければならない
            while len(group) > 0:
                player1 = group.pop()
                found_partner = False
                for higher_group_name in ["5-8", "9-10"]:
                    higher_group = groups[higher_group_name]
                    if len(higher_group) > 0:
                        player2 = higher_group.pop()
                        matches.append((player1, player2))
                        found_partner = True
                        break
                if not found_partner:
                    remaining_players.append(player1)
        else:
            while len(group) >= 4:
                team1 = [group.pop(), group.pop()]
                team2 = [group.pop(), group.pop()]
                matches.append((team1, team2))
            remaining_players.extend(group)

    # 残りのプレイヤーをランダムに組み合わせる
    if len(remaining_players) > 0:
        random.shuffle(remaining_players)
        while len(remaining_players) >= 4:
            team1 = [remaining_players.pop(), remaining_players.pop()]
            team2 = [remaining_players.pop(), remaining_players.pop()]
            matches.append((team1, team2))

    return matches, remaining_players

@app.route('/matches')
def matches():
    match_data = organize_matches()
    return render_template('matches.html', **match_data)

if __name__ == '__main__':
    app.run(debug=True)
