import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug import generate_password_hash, check_password_hash
import csv

app = Flask(__name__)

# Check for environment variable
#if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
#Should set osvariable

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


engine = create_engine('postgres://tqlhgegrokhslz:c73b2e7dcd585e0987add967285d7eaeff44d558240bb4565a0c742e5ca78f1c@ec2-54-75-230-253.eu-west-1.compute.amazonaws.com:5432/d20flhqtdd9qi1')
db = scoped_session(sessionmaker(bind=engine))

def CreateTable_Users():
    db.execute("CREATE TABLE Users (Id Serial PRIMARY KEY, Name varchar(255), Email varchar(255), UserName varchar(255) UNIQUE, Password varchar(128), RegisterDate TIMESTAMP default current_timestamp);")

def CreateTable_Books():
    db.execute("CREATE TABLE Books (ISBN varchar(20) PRIMARY KEY, title varchar(255), Author varchar(255), Date varchar );")
    db.commit()

def Import_csv_to_DB():
    f = open('books.csv')
    data = csv.reader(f)

    for isbn, title, author, year in data:
        db.execute("INSERT INTO Books (ISBN, TItle, Author, Date) VALUES (:ISBN, :TItle, :Author, :Date)",
                                {"ISBN" : isbn, "TItle" : title, "Author" : author, "Date" : year})
    db.commit()


def PrintTable():
    user = db.execute("select * from Users;").fetchall()
    print(user)

#@app.route("/login", methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('login')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        db.execute("INSERT INTO Users (UserName, Password_hash) VALUES (:UserName, :Password_hash)",
            {"UserName":name, "Password_hash":hashed_password})
        db.commit()
        return render_template('login.html', UserName = name, password = hashed_password)
    return  render_template('login.html')

 #def testdf():
#    if db.execute("SELECT * From Books Where author like (:author)", {'author':name}).fetchone() is not None:
#        result = db.execute("SELECT * From Books Where author like (:author)", {'author':name}).fetchall()
#        for record in result:
#            print(record)
##        for record in result:
#            print(record)
#    elif db.execute("SELECT * From Books Where title like (:title)", {'title':name}).fetchone() is not None:
#        result = db.execute("SELECT * From Books Where title like (:title)", {'title':name}).fetchall()
#        for record in result:
#            print(record)
#    else:
#        print('No records')

if __name__ == "__main__":
    #Insert all data to database
    #db.execute("INSERT INTO Users (Name, Email, Username, Password) VALUES (:Name, :Email, :Username, :Password)",
    #    {"Name":name, "Email":email, "Username":username, "Password":password})
    #db.commit()
    #db.execute('CREATE TABLE Reviews (id Serial PRIMARY KEY, title varchar(20), body varchar(255), user_id integer REFERENCES Users,  book_isbn varchar(20) REFERENCES Books, rate INTEGER);')
    #db.commit()

    #db.execute("INSERT INTO Library (user_id , books_isbn) VALUES (:user_id , :books_isbn);", {'user_id':2 , 'books_isbn':'1416949658'})
    #db.commit()
    isbn = '7653175'
    #existing_reviews =  db.execute("SELECT * From Reviews Where book_isbn = (:book_isbn)", {'book_isbn':isbn}).fetchall()
    #print(len(existing_reviews))
    #rating = db.execute("SELECT * FROM Reviews ").fetchall()
    #print(rating)
    #avarage_rating = db.execute("SELECT AVG(rate) FROM Reviews where book_isbn =(:book_isbn)", {'book_isbn': book_isbn}).fetchone()
    #print(avarage_rating[0] is None)
    book = db.execute("Select Books.title, ISBN, Author, CAST(AVG(Rate) AS varchar(4)) AS rate, Date FROM Books left JOIN Reviews On ISBN=book_isbn WHERE ISBN=(:ISBN) GROUP BY ISBN", {"ISBN" :isbn}).fetchone()
    print(book is None)
    #result = db.execute('SELECT name, title, author FROM library JOIN users ON users.id=library.user_id JOIN books ON books.isbn=library.books_isbn').fetchall()
    #print(result)
    #db.execute("SELECT * FRom Reviews")
    #db.commit()
    #mynick = db.execute('select Password_hash from Users where UserName = (:UserName)',{'UserName': p}).fetchone()
