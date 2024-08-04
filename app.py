from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///players.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    participating = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Player {self.name}>'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/players')
def players():
    players = Player.query.order_by(Player.grade, Player.gender, Player.level).all()
    return render_template('players.html', players=players)

@app.route('/add', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        name = request.form['name']
        level = int(request.form['level'])
        gender = request.form['gender']
        grade = int(request.form['grade'])
        participating = 'participating' in request.form
        new_player = Player(name=name, level=level, gender=gender, grade=grade, participating=participating)
        try:
            db.session.add(new_player)
            db.session.commit()
            return redirect(url_for('players'))
        except:
            return '選手の追加に問題が発生しました'
    else:
        return render_template('player_form.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_player(id):
    player = Player.query.get_or_404(id)
    if request.method == 'POST':
        player.name = request.form['name']
        player.level = int(request.form['level'])
        player.gender = request.form['gender']
        player.grade = int(request.form['grade'])
        player.participating = 'participating' in request.form
        try:
            db.session.commit()
            return redirect(url_for('players'))
        except:
            return '選手の更新に問題が発生しました'
    else:
        return render_template('player_form.html', player=player)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_player(id):
    player = Player.query.get_or_404(id)
    try:
        db.session.delete(player)
        db.session.commit()
        return redirect(url_for('players'))
    except:
        return '選手の削除に問題が発生しました'

@app.route('/toggle_participation/<int:id>', methods=['POST'])
def toggle_participation(id):
    player = Player.query.get_or_404(id)
    player.participating = not player.participating
    try:
        db.session.commit()
        return redirect(url_for('players'))
    except:
        return '参加状況の切り替えに問題が発生しました'

def create_sets(players):
    players.sort(key=lambda p: p.level)
    sets = []
    unpaired = []
    used_players = set()  # 使用済みプレイヤーの追跡
    while len(players) > 1:
        player1 = players.pop(0)
        if player1 in used_players:
            continue  # プレイヤーが既に使用されている場合はスキップ
        found_partner = False
        for diff in range(6):
            candidate_partners = [p for p in players if abs(p.level - player1.level) <= diff and p not in used_players]
            if candidate_partners:
                partner = random.choice(candidate_partners)
                players.remove(partner)
                sets.append((player1, partner))
                used_players.update([player1, partner])
                found_partner = True
                break
        if not found_partner:
            unpaired.append(player1)
            used_players.add(player1)
    if players:
        for player in players:
            if player not in used_players:
                unpaired.append(player)
                used_players.add(player)
    return sets, unpaired

def create_matches(sets, unpaired):
    matches = []
    all_sets = sets

    used_players = set()
    for i in range(0, len(all_sets), 2):
        if i + 1 < len(all_sets):
            set1, set2 = all_sets[i], all_sets[i + 1]
            if set1[0] not in used_players and set1[1] not in used_players and set2[0] not in used_players and set2[1] not in used_players:
                matches.append((set1[0], set2[0], set1[1], set2[1]))
                used_players.update(set1)
                used_players.update(set2)

    remaining_unpaired = unpaired + [player for player_set in all_sets for player in player_set if player not in used_players]

    return matches, remaining_unpaired

@app.route('/matches')
def matches():
    players = Player.query.filter_by(participating=True).all()

    male_players = [p for p in players if p.gender == 'male']
    female_players = [p for p in players if p.gender == 'female']

    male_sets, male_unpaired = create_sets(male_players)
    female_sets, female_unpaired = create_sets(female_players)

    male_matches, male_remaining_unpaired = create_matches(male_sets, male_unpaired)
    female_matches, female_remaining_unpaired = create_matches(female_sets, female_unpaired)

    return render_template('matches.html', male_matches=male_matches, female_matches=female_matches, male_unpaired=male_remaining_unpaired, female_unpaired=female_remaining_unpaired)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
