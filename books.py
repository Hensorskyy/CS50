import csv
def Books():
    f = open('books.csv')
    data = csv.reader(f)
    books = []

    for isbn, title, author, year in data:
        book = {}
        book['isbn'] = isbn
        book['title'] = title
        book['author'] = author
        book['year'] = int(year)
        books.append(book)
    return books

if __name__=="__main__":
    i = Books()
    print(i[:5])
