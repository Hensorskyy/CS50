import requests

def main():
    #base = input("First Currency: ")
    base = "USD"
    date = input("Date: ")
    res = requests.get("https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange",
                params={"valcode": base, "date": date, "json":"json"})
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")
    data = res.json()

    print(f"1 {base} was equal to {data[0]['rate']} on {date}")


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

if __name__ == "__main__":
    res = goodreads('1857231082')
    print(res['average_rating'])
#st = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={base}&date={date}&json"
#res = requests.get(st)
