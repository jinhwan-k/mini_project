import certifi
from pymongo import MongoClient

ca = certifi.where()

import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

client = MongoClient('mongodb+srv://test:sparta@cluster0.mlljfme.mongodb.net/Cluster0?retryWrites=true&w=majority',
                     tlsCAFile=ca)
db = client.test


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    # Client에 mytoken 쿠키 값이 없으면 index 페이지를 렌더링 합니다.
    if token_receive is None:
        return render_template('index.html')

    # Client에 mytoken 쿠키 값이 있고, 만료되지 않은 토큰 값일 경우 서비스 페이지로 이동합니다.
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]}, {'_id': False})
        if user_info is not None:
            return redirect(url_for("league", username=user_info["username"], nickname=user_info["nickname"]))
        return render_template('index.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="timeout"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="invalid_token"))


@app.route('/register')
def register():
    return render_template('sign_up.html')


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('index.html', msg=msg)


@app.route('/league')
def league():
    token_receive = request.cookies.get('mytoken')
    if token_receive is None:
        return redirect(url_for("home"))
    return render_template('league_select.html')


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "nickname": nickname_receive,  # 닉네임
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup/<keyword>', methods=['POST'])
def check_dup(keyword):
    username_receive = request.form['username_give']
    if keyword == "username":
        exists = bool(db.users.find_one({"username": username_receive}))
    else:
        exists = bool(db.users.find_one({"nickname": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/player_select')
def player_select():
    token_receive = request.cookies.get('mytoken')
    if token_receive is None:
        return redirect(url_for("home"))
    id = request.args.get('id')
    return render_template('player_select.html', id=id)


@app.route('/player_comment')
def temp():
    card = request.args.get('card')
    return render_template('player_comment.html', card=card)


@app.route('/player_comment/save', methods=['POST'])
def save_comment():
    comment_receive = request.form['comment_give']
    username = request.form['username_give']
    player_receive = request.form['player_give']
    nickname = request.form['nickname_give']
    doc = {
        "player" : player_receive,
        "comment" : comment_receive,
        "username": username,  # 아이디
        "nickname": nickname,  # 닉네임
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route("/player_comment/show", methods=["GET"])
def player_comment_get():
    player = request.cookies.get("id3")
    comment_list = list(db.users.find({'player':player},{'_id':False}))
    return jsonify({'comments': comment_list})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
