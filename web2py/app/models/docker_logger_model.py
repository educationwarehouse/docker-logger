db.define_table("url_opslag",
                Field("url", "string")
                )
db.define_table("zoekterm",
                Field("zoekterm", "string")
                )
db.define_table("log_filter",
                Field("log_filter", "string")
                )

# insert all the default filters in the log_filter table
if db(db.log_filter).isempty():
    print("Inserting default filters")
    db.log_filter.insert(log_filter="debug")
    db.log_filter.insert(log_filter="info")
    db.log_filter.insert(log_filter="warn")
    db.log_filter.insert(log_filter="error")
    db.log_filter.insert(log_filter="fatal")
    db.commit()

