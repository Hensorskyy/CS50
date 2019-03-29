from flask import Flask, session, render_template, request, flash, redirect, url_for, session, logging, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug import generate_password_hash, check_password_hash
from books import Books
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from functools import wraps
import requests


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'super secret key'

#config database
engine = create_engine('postgres://tqlhgegrokhslz:c73b2e7dcd585e0987add967285d7eaeff44d558240bb4565a0c742e5ca78f1c@ec2-54-75-230-253.eu-west-1.compute.amazonaws.com:5432/d20flhqtdd9qi1')
db = scoped_session(sessionmaker(bind=engine))

def goodreads(isbn):
    dev_key = 'XxzONx2XbiV8xMwYhcenA'
    book_info = {}
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                params={"key": dev_key, "isbns": isbn})
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")
    data = res.json()

    book_info['average_rating'] = data['books'][0]['average_rating']
    book_info['ratings_count'] = data['books'][0]['ratings_count']
    return book_info

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/book')
def library():
    result = db.execute("SELECT * FROM Books").fetchall()
    return render_template('library.html', library = result)



class RegisterFrom(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=4, max=25)])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message = 'Password do not mach')])
    confirm = PasswordField('Confirm Password')

    @app.route('/register', methods = ['POST', 'GET'])
    def register():
        form = RegisterFrom(request.form)
        if request.method == 'POST' and form.validate():
            name = form.name.data
            email = form.email.data
            username = form.username.data
            password = generate_password_hash(form.password.data)
            #Insert all data to database
            db.execute("INSERT INTO Users (Name, Email, Username, Password) VALUES (:Name, :Email, :Username, :Password)",
                {"Name":name, "Email":email, "Username":username, "Password":password})
            db.commit()
            flash("You are registered and can log in", 'success')
            return redirect(url_for('home'))

        return render_template('register.html', form = form)

@app.route('/login', methods = ['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        name = request.form['username']
        user = db.execute("SELECT * FROM Users WHERE Username = :Username", {"Username": name}).fetchone()
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user[4],
                                     request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['logged_in'] = True
            session['username'] = name

            return redirect(url_for('dashboard'))

    return render_template('login.html', error = error)

def is_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You are logged out, Please log in', 'danger')
            return redirect(url_for('login'))
    return decorated_function


@app.route('/logout')
def logout():
    session.clear()
    flash('You were logout', 'success')
    return redirect(url_for('home'))


@app.route('/dashboard', methods = ['POST', 'GET'])
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

class SearchFrom(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])

@app.route('/search', methods = ['POST', 'GET'])
def search():

    form = SearchFrom(request.form)

    if request.method == 'POST' and form.validate():
        name = form.name.data
        if db.execute("SELECT * From Books Where author like (:author)", {'author':name}).fetchone() is not None:
            result = db.execute("SELECT * From Books Where author like (:author)", {'author':name}).fetchall()

        elif db.execute("SELECT * From Books Where isbn like (:isbn)", {'isbn':name}).fetchone() is not None:
            result = db.execute("SELECT * From Books Where isbn like (:isbn)", {'isbn':name}).fetchall()

        elif db.execute("SELECT * From Books Where title like (:title)", {'title':name}).fetchone() is not None:
            result = db.execute("SELECT * From Books Where title like (:title)", {'title':name}).fetchall()
        else:
            flash('No records')
            return redirect(url_for('search'))

        return render_template('library.html', library = result)
    return(render_template('search.html'))


##--------------------------REVIEW Books-------------
class ReviewForm(Form):
    title = StringField('title', [validators.Length(min=1, max=50)])
    body = TextAreaField('body', [validators.Length(min=30)])
    rate = SelectField('rate this book',
                    choices=[(1, '1'),
                             (2, '2'),
                             (3, '3'),
                             (4, '4'),
                             (5, '5')],
                    coerce=int,
                    validators=[validators.optional()])


@app.route('/book/<string:isbn>', methods = ['POST', 'GET'])
@is_logged_in
def book_manager(isbn):
    form = ReviewForm(request.form)
    user_id = db.execute("SELECT id From Users Where Name = (:Name)", {'Name':session['username']}).fetchone()
    book_isbn = isbn
    avarage_rating = db.execute("SELECT AVG(rate) FROM Reviews where book_isbn =(:book_isbn)", {'book_isbn': book_isbn})
    left_post = db.execute("SELECT * From Reviews Where user_id = (:user_id) And book_isbn=(:book_isbn) ", {'user_id':user_id[0], 'book_isbn':book_isbn}).rowcount == 0
    avarage_rating = db.execute("SELECT AVG(rate) FROM Reviews where book_isbn =(:book_isbn)", {'book_isbn': book_isbn}).fetchone()
    if avarage_rating[0] is None:
        avarage_rating = 0
    else:
        avarage_rating = round(avarage_rating[0],2)

    if request.method == 'POST' and form.validate:
        title = form.title.data
        body = form.body.data
        rate = form.rate.data
        user_id = db.execute("SELECT id From Users Where Name = (:Name)", {'Name':session['username']}).fetchone()
        book_isbn = isbn
        db.execute("INSERT INTO Reviews (title, body, user_id, book_isbn, rate) VALUES (:title, :body, :user_id, :book_isbn, :rate)",
                                {"title" : title, "body" : body, "user_id" : user_id[0], "book_isbn" : book_isbn, "rate": rate})
        db.commit()

        flash("You left comment", 'success')
        #existing_reviews =  db.execute("SELECT * From Reviews Where book_isbn = (:book_isbn)", {'book_isbn':isbn}).fetchall()
        #result = db.execute("SELECT * From Books Where isbn = (:isbn)", {'isbn':isbn}).fetchone()
        #return render_template('book_item.html', info = result, form= form, existing_reviews = existing_reviews)
        return redirect(url_for('book_manager', isbn = isbn))

    existing_reviews =  db.execute("SELECT * From Reviews Where book_isbn = (:book_isbn)", {'book_isbn':isbn}).fetchall()
    result = db.execute("SELECT * From Books Where isbn = (:isbn)", {'isbn':isbn}).fetchone()
    return render_template('book_item.html',goodreads_info = goodreads(isbn), info = result, form= form, existing_reviews = existing_reviews, left_post = left_post, avarage_rating = avarage_rating)
books = [
    {'id': 0,
     'title': 'A Fire Upon the Deep',
     'author': 'Vernor Vinge',
     'first_sentence': 'The coldsleep itself was dreamless.',
     'year_published': '1992'},
    {'id': 1,
     'title': 'The Ones Who Walk Away From Omelas',
     'author': 'Ursula K. Le Guin',
     'first_sentence': 'With a clamor of bells that set the swallows soaring, the Festival of Summer came to the city Omelas, bright-towered by the sea.',
     'published': '1973'},
    {'id': 2,
     'title': 'Dhalgren',
     'author': 'Samuel R. Delany',
     'first_sentence': 'to wound the autumnal city.',
     'published': '1975'}
]


@app.route('/api/v1/resources/books/all', methods=['GET'])
def api_all():

    all_books = db.execute("Select Books.title, ISBN, Author, CAST(AVG(Rate) AS varchar(4)) AS rate, Date FROM Books left JOIN Reviews On ISBN=book_isbn GROUP BY ISBN").fetchall()

    return jsonify({'result': [dict(row) for row in all_books]})

@app.route('/api/v1/resources/books', methods=['GET'])
def api_isbn():
    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no ID is provided, display an error in the browser.
    if 'isbn' in request.args:
        isbn = str(request.args['isbn'])
    else:
        return "Error: No id field provided. Please specify an id."

    book = db.execute("Select Books.title, ISBN, Author, CAST(AVG(Rate) AS varchar(4)) AS rate, Date FROM Books left JOIN Reviews On ISBN=book_isbn WHERE ISBN=(:ISBN) GROUP BY ISBN", {"ISBN" :isbn}).fetchone()
    if book is None:
        flash("The book does not exist")
        return abort(404)
    return jsonify(dict(book))

    # Use the jsonify function from Flask to convert our list of
    # Python dictionaries to the JSON format.




@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


if __name__=="__main__":
    app.run()
