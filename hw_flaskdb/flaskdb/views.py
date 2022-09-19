"""
A Sample Web-DB Application for DB-DESIGN lecture
Copyright (C) 2022 Yasuhiro Hayashi
"""
from flask import Blueprint, request, session, render_template, redirect, flash, url_for, jsonify
import datetime
import pickle

from flaskdb import apps, db, da
from flaskdb.models import User, Item, Order, Lec
from flaskdb.forms import LoginForm, AddItemForm, SearchItemForm, CheckOutForm

app = Blueprint("app", __name__)

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("/index.html")

@app.route("/now", methods=["GET", "POST"])
def now():
    return str(datetime.datetime.now())

# This is a very danger method
@app.route("/receive", methods=["GET", "POST"])
def receive():
    if request.method == "GET":
        username = request.args.get("username")
        password = request.args.get("password")
    else:
        username = request.form["username"]
        password = request.form["password"]

    return render_template("receive.html", username=username, password=password)

@app.route("/initdb", methods=["GET", "POST"])
def initdb():
    db.drop_all()
    db.create_all()
    
    admin = User(username="admin", password="password")
    user = User(username="user", password="password")
    db.session.add(admin)
    db.session.add(user)
    db.session.commit()
    return "initidb() method was executed. "

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, password=form.password.data).first()

        if user is None or user.password != form.password.data:
            flash("Username or Password is incorrect.", "danger")
            return redirect(url_for("app.login"))

        session["username"] = user.username
        session["cart"] = []
        return redirect(url_for("app.index"))

    return render_template("login.html", form=form)

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("username", None)
    session.pop("cart", None)
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("app.index"))

@app.route("/additem", methods=["GET", "POST"])
def additem():
    if not "username" in session:
        flash("Log in is required.", "danger")
        return redirect(url_for("app.login"))

    form = AddItemForm()

    if form.validate_on_submit():
        # item = Item()
        item = Lec()
        form.copy_to(item)
        user = User.query.filter_by(username=session["username"]).first()
        item.owner_id = user.id
        db.session.add(item)
        db.session.commit()

        flash("An item was added.", "info")
        return redirect(url_for("app.additem"))

    # itemlist = Item.query.all()
    itemlist = Lec.query.all()
    return render_template("additem.html", form=form, itemlist=itemlist)

@app.route("/searchitem", methods=["GET", "POST"])
def searchitem():
    if not "username" in session:
        flash("Log in is required.", "danger")
        return redirect(url_for("app.login"))

    form = SearchItemForm()

    if form.validate_on_submit():
        itemlist = Item.query.filter(Item.itemname.like("%" + form.itemname.data + "%")).all()
        itemlist = pickle.dumps(itemlist)
        session["itemlist"] = itemlist
        return redirect(url_for("app.searchitem"))

    if "itemlist" in session:
        itemlist = session["itemlist"]
        itemlist = pickle.loads(itemlist)
        session.pop("itemlist", None)
    else:
        # itemlist = Item.query.all()
        itemlist = Lec.query.all()
    
    return render_template("search.html", form=form, itemlist=itemlist)

@app.route("/addtocart", methods=["GET", "POST"])
def addtocart():
    if not "username" in session:
        flash("Log in is required.", "danger")
        return redirect(url_for("app.login"))

    form = CheckOutForm()

    if request.args.get("item_id") is not None:
        item_id = request.args.get("item_id")
        item = Item.query.filter_by(id = item_id).first()
        if item is not None:
            session["cart"].append(item.to_dict())
            session.modified = True

            item2 = Item()
            item2.from_dict(item.to_dict())

            return redirect(url_for("app.addtocart")) # comment out and reload the page

    return render_template("cart.html", form=form)

@app.route("/removefromcart", methods=["GET", "POST"])
def removefromcart():
    if not "username" in session:
        flash("Log in is required.", "danger")
        return redirect(url_for("app.login"))

    form = CheckOutForm()

    if request.args.get("index") is not None:
        index = int(request.args.get("index"))
        index -= 1
        session["cart"].pop(index)
        session.modified = True

        return redirect(url_for("app.removefromcart")) # comment out and reload the page

    return render_template("cart.html", form=form)

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if not "username" in session:
        flash("Log in is required.", "danger")
        return redirect(url_for("app.login"))

    if "cart" in session:
        cart = session["cart"]
        username = session["username"]

        order_code = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        for item in cart:
            user = User.query.filter_by(username=username).first()
            order = Order(order_code=order_code, user_id=user.id, item_id=item["id"], price=item["price"])
            db.session.add(order)

        if len(cart) > 0:
            db.session.commit()

        session["cart"] = []
        session.modified = True

    return render_template("checkout.html", cart=cart)

@app.route("/nativesql", methods=["GET", "POST"])
def nativesql():
    if not "username" in session:
        flash("Log in is required.", "danger")
        return redirect(url_for("app.login"))

    form = AddItemForm()

    if form.validate_on_submit():
        item = Item()
        form.copy_to(item)
        user = User.query.filter_by(username=session["username"]).first()
        item.user_id = user.id
        da.add_item(item)

        flash("An item was added.", "info")
        return redirect(url_for("app.additem"))

    itemlist = da.search_items()
    return render_template("additem.html", form=form, itemlist=itemlist)
