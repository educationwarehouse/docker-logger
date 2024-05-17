db.define_table("url", Field("url", "string", unique=True), Field("name", "string"))
db.define_table(
    "search_term", Field("term", "string", unique=True), Field("name", "string")
)
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
    """
    Inserts a new search term or URL into the respective database table.

    Parameters:
    term (str): The search term to be inserted into the 'search_term' table.
    url (str): The URL to be inserted into the 'url' table.
    name (str): The name to be associated with the term or URL.
    """
    if term:
        print("Inserting search term:", term, "with the name:", name if name else term)
        db.search_term.insert(term=term, name=name if name else term)
    if url:
        print("Inserting url:", url, "with the name:", name if name else url)
        db.url.insert(url=url, name=name if name else url)
    db.commit()


def model_delete_item(term, url, name):
    """
    Deletes a search term or URL from the respective database table.

    Parameters:
    term (str): The search term to be deleted from the 'search_term' table.
    url (str): The URL to be deleted from the 'url' table.
    name (str): The name associated with the term or URL. This is used for printing purposes only.
    """
    if term:
        print("Deleting search term:", term, "with the name:", name)
        db(db.search_term.term == term).delete()
    if url:
        print("Deleting url:", url, "with the name:", name)
        db(db.url.url == url).delete()
    db.commit()
