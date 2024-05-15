db.define_table("url", Field("url", "list:string"))
db.define_table("search_term", Field("term", "list:string"))
db.define_table("log_filter", Field("log_filter", "string"))

# insert all the default filters in the log_filter table
if db(db.log_filter).isempty():
    print("Inserting default filters")
    db.log_filter.insert(log_filter="debug")
    db.log_filter.insert(log_filter="info")
    db.log_filter.insert(log_filter="warn")
    db.log_filter.insert(log_filter="error")
    db.log_filter.insert(log_filter="fatal")
    db.commit()


def model_submit_item(term, url, name):
    if term:
        print("Inserting search term:", term, "with the name:", name if name else term)
        db.search_term.insert(term=[term, name])
    if url:
        print("Inserting url:", url, "with the name:", name if name else url)
        db.url.insert(url=[url, name])
    db.commit()


def model_delete_item(term, url, name):
    if term:
        print("Deleting search term:", term, "with the name:", name)
        if term == name:
            db(db.search_term.term.contains(term)).delete()
        else:
            db(db.search_term.term == [term, name]).delete()
    if url:
        print("Deleting url:", url, "with the name:", name)
        if url == name:
            db(db.url.url.contains(url)).delete()
        else:
            db(db.url.url == [url, name]).delete()
    db.commit()
