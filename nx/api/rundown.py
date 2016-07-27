from nx import *

def api_rundown(**kwargs):
    id_channel = int(kwargs["id_channel"])
    start_time = kwargs.get("start_time", 0)
    end_time = start_time + (3600 * 24)

    process_start_time = time.time()
    if not id_channel:
        return {"response" : 400, message : "Request params error"}
    if not id_channel in config["playout_channels"]:
        return {"response" : 400, message : "No such playout channel"}

    channel_config = config["playout_channels"][id_channel]

    # utils

    db = kwargs.get("db", DB())
    item_runs  = get_item_runs(id_channel, start_time, end_time, db=db)
    job_progress = {}
    if channel_config.get("send_action"):
        db.query("SELECT id_object, progress FROM nx_jobs WHERE id_action = %s AND progress >= -1", [channel_config["send_action"]])
        job_progress = {id_object: progress for id_object, progress in db.fetchall()}

    # get rundown

    db.query("""
            SELECT
                e.id_object,
                i.id_object,
                a.id_object,
                e.meta,
                i.meta,
                a.meta
            FROM
                nx_events AS e,
                nx_items AS i
            LEFT JOIN
                nx_assets AS a
            ON
                i.id_asset = a.id_object
            WHERE
                id_channel = %s AND e.start >= %s AND e.start < %s
            AND
                e.id_magic = i.id_bin AND i.id_asset = a.id_object
            ORDER BY
                e.start ASC,
                i.position ASC
            """, (id_channel, start_time, end_time))

    data = []
    current_event_id = None
    event = None
    items = []
    ts_broadcast = 0
    for id_event, id_item, id_asset, emeta, imeta, ameta in db.fetchall():
        if id_event != current_event_id:
            if current_event_id:
                data.append({
                        "event_meta" : event.meta,
                        "bin_meta"   : {},
                        "items"      : items
                    })
                if not items:
                    ts_broadcast = 0

            items = []
            current_event_id = id_event
            if emeta:
                event = Event(meta=emeta, db=db)
            else:
                event = Event(id_event, db=db)

            if event["run_mode"]:
                ts_broadcast = 0
                event.meta["rundown_scheduled"] = ts_scheduled = event["start"]
                event.meta["rundown_broadcast"] = ts_broadcast = ts_broadcast or ts_scheduled

            #print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event["start"])), event["title"]

        if ameta:
            asset = Asset(meta=ameta, db=db)
        else:
            asset = Asset(id_asset, db=db)

        if imeta:
            item = Item(meta=imeta, db=db)
        else:
            item = Item(id_item, db=db)
        item._asset = asset


        #print "--", item["position"], item["title"]

        as_start, as_stop = item_runs.get(item.id, (0, 0))
        if as_start:
            ts_broadcast = as_start

        item.meta["asset_mtime"] = asset["mtime"]
        item.meta["rundown_scheduled"] = ts_scheduled
        item.meta["rundown_broadcast"] = ts_broadcast

        ts_scheduled += item.duration
        ts_broadcast += item.duration

        # ITEM STATUS
        #
        # -1 : AIRED
        # -2 : Partialy aired. Probably still on air or play service was restarted during broadcast
        #  0 : Master asset is offline. Show as "OFFLINE"
        #  1 : Master asset is online, but playout asset does not exist or is offline
        #  2 : Playout asset is online. Show as "READY"

        playout_spec = config["playout_channels"][id_channel]["playout_spec"]
        playout_status_key = playout_spec + "_status"

        if as_start and as_stop:
            item.meta["rundown_status"] = -1 # AIRED
        elif as_start:
            item.meta["rundown_status"] = -2 #  PART AIRED
        elif not item["id_asset"]:
            item.meta["rundown_status"] = 2 # Virtual item or something... show as ready
        elif asset["status"] != ONLINE:
            item.meta["rundown_status"] = 0 # Master asset is not online: Rundown status = OFFLINE
        elif asset[playout_status_key]:
            item.meta["rundown_status"] = asset[playout_status_key]
        else:
            id_playout = item[playout_spec]
            if not id_playout or Asset(id_playout, db=db)["status"] not in [ONLINE, CREATING]: # Master asset exists, but playout asset is not online.... (not scheduled / pending)
                item.meta["rundown_status"] = 1
            else:
                item.meta["rundown_status"] = 2 # Playout asset is ready

        if item["id_asset"] in job_progress:
            item.meta["rundown_transfer_progress"] = job_progress[item["id_asset"]]

        items.append(item.meta)

    process_time = time.time() - process_start_time
    return {"response" : "200", "message" : "Rundown loaded in {:.02f} seconds".format(process_time), "data" : data}
