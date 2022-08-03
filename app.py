#! /usr/bin/env python3

from flask import Flask, request
from redis import Redis
import json
import random

app = Flask("qpassword_manager")
redis = Redis(decode_responses=True)


@app.route("/register", methods=["post"])
def register():
    username = request.json["username"]
    password = request.json["password"]
    email = request.json["email"]

    tokens = redis.keys("*")
    while True:
        token = random.randint(100000, 999999)
        if token not in tokens:
            break

    print(token)
    redis.set(token, f'["{username}", "{password}", "{email}"]', 3600)
    return ""


@app.route('/confirm_email/<token>')
def confirm_email(token):
    account = json.loads(redis.get(token))

    redis.json().set(f'{account[0]}', '$', f'{{ \"master_key\": \"{account[1]}\", \"email\": \"{account[2]}\", \"passwords\": [] }}')
    return token


@app.route("/add_to_database", methods=["post"])
def add_to_database():
    if request.authorization:
        print(redis.keys("*"))
    return "hi"


app.run(debug=True)
