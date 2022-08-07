#! /usr/bin/env python3

from flask import Flask, request
from redis import Redis
import random

app = Flask("qpassword_manager")
redis = Redis(decode_responses=True)


@app.route("/register", methods=["post"])
def register():
    taken_usernames = []
    for username in filter(lambda key: not key.isdigit(), redis.keys("*")):
        taken_usernames.append(username)

    for username in map(
        lambda code: redis.json().get(code)[0],
        filter(lambda key: key.isdigit(), redis.keys("*")),
    ):
        taken_usernames.append(username)

    username = request.json["username"]

    if username in taken_usernames:
        return "Username already taken"

    if username[0].isdigit():
        return "Invalid name: Your username can't start with a number"

    password = request.json["password"]
    email = request.json["email"]

    if redis.ttl("0emails") == -2:
        redis.json().set("0emails", "$", [])

    elif email in redis.json().get("0emails", "$")[0]:
        return "Account with this email address is already registered"

    keys = redis.keys("*")
    while True:
        code = random.randint(100000, 999999)
        if code not in keys:
            break

    print(code)
    redis.json().set(code, "$", [username, password, email], 3600)
    return (
        "Please confirm your email to finish the registration"
        + f": http://localhost:5000/confirm_email/{username}/{code}"
    )


@app.route("/confirm_email/<username>/<code>")
def confirm_email(username, code):
    try:
        account = redis.json().get(code)

        if account[0] == username:
            redis.json().set(
                f"{account[0]}",
                "$",
                {
                    "master_key": account[1],
                    "email": account[2],
                    "next_id": 0,
                    "passwords": {},
                },
            )
            redis.delete(code)
            redis.json().arrappend("0emails", "$", account[2])
            return "Successfully verified"

    except TypeError:
        print(f"Code {code} not in database")

    return "Invalid/Expired code"


@app.route("/check_credentials", methods=["post"])
def check_credentials():
    if redis.ttl(request.authorization["username"]) != -2:
        user = redis.json().get(request.authorization["username"])
        if user["master_key"] == request.authorization["password"]:
            return "1"

    return ""


@app.route("/add_to_database", methods=["post"])
def add_to_database():
    if request.authorization:
        if check_credentials():
            username = request.authorization["username"]
            entry_id = redis.json().get(username, "$.next_id")[0]
            redis.json().set(
                username,
                f"$.passwords.{entry_id}",
                [request.json[key] for key in ["website", "username", "password"]],
            )
            redis.json().numincrby(username, "$.next_id", 1)

    return ""


@app.route("/remove_from_database", methods=["post"])
def remove_from_database():
    if request.authorization:
        if check_credentials():
            username = request.authorization["username"]
            entry_id = request.json["id"]
            entry = redis.json().get(username, f"$.passwords.{entry_id}")
            if entry:
                redis.json().set(username, f"$.passwords._{entry_id}", entry[0])
                redis.json().delete(username, f"$.passwords.{entry_id}")

    return ""


@app.route("/get_entry_ids", methods=["post"])
def get_entry_ids():
    if request.authorization:
        if check_credentials():
            username = request.authorization["username"]
            objkeys = redis.json().objkeys(username, "$.passwords")[0]
            entry_ids = [key for key in filter(lambda x: x.isdigit(), objkeys)]
            return entry_ids

    return ""


@app.route("/get_entry", methods=["post"])
def get_entry():
    if request.authorization:
        if check_credentials():
            username = request.authorization["username"]
            entry_id = request.json["id"]
            entry = redis.json().get(username, f"$.passwords.{entry_id}")[0]
            return entry

    return ""


@app.route("/get_all", methods=["post"])
def get_all():
    if request.authorization:
        if check_credentials():
            username = request.authorization["username"]
            objkeys = redis.json().objkeys(username, "$.passwords")[0]
            entry_ids = [key for key in filter(lambda x: x.isdigit(), objkeys)]
            print(entry_ids)
            entries = []
            for entry_id in entry_ids:
                entries.append(redis.json().get(username, f"$.passwords.{entry_id}")[0])

            return entries

    return ""


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
