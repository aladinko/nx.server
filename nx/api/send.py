from nx import *

def api_send(**kwargs):
    ids = kwargs.get("ids", [])
    db = kwargs.get("db", DB())
    return {"response" : 501, "message" : "Not implemented"}