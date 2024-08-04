from flask import render_template, request, redirect, url_for
from app import app, db
from app.models import Player

@app.route('/')
def index():
    players = Player.query.order_by(Player.grade, Player.gender, Player.level).all()
    return render_template('index.html', players=players)

@app.route('/add_player', methods=['POST'])
def add_player():
    name = request.form.get('name')
    gender = request.form.get('gender')
    grade = request.form.get('grade')
    level = request.form.get('level')
    new_player = Player(name=name, gender=gender, grade=int(grade), level=int(level))
    db.session.add(new_player)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/toggle_participation/<int:player_id>')
def toggle_participation(player_id):
    player = Player.query.get(player_id)
    player.participation = not player.participation
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_player/<int:player_id>')
def delete_player(player_id):
    player = Player.query.get(player_id)
    db.session.delete(player)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/generate_matches')
def generate_matches():
    players = Player.query.filter_by(participation=True).all()
    matches = []

    def create_match(player_group):
        random.shuffle(player_group)
        while len(player_group) >= 4:
            team1 = player_group.pop()
            team2 = player_group.pop()
            team3 = player_group.pop()
            team4 = player_group.pop()
            matches.append((team1, team2, team3, team4))

    # レベルごとにグループを作成
    level_groups = {i: [] for i in range(1, 11)}
    for player in players:
        level_groups[player.level].append(player)

    # レベル1-2とレベル5以上のペア
    low_high_groups = level_groups[1] + level_groups[2]
    mid_high_groups = level_groups[5] + level_groups[6] + level_groups[7] + level_groups[8] + level_groups[9] + level_groups[10]

    create_match(low_high_groups)
    create_match(mid_high_groups)

    return render_template('matches.html', matches=matches)
