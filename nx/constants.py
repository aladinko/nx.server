########################################################################
## Constants

# content_type
TEXT  = 0
VIDEO = 1
AUDIO = 2
IMAGE = 3


# media_type
FILE      = 0  # There is (or should be) physical file specified by 'storage' and 'path' metadata
VIRTUAL   = 1  # Asset exists only as DB record (macro, text...)

# asset status
OFFLINE  = 0   # Associated file does not exist
ONLINE   = 1   # File exists and is ready to use
CREATING = 2   # File exists, but was changed recently. It is no safe (or possible) to use it yet
TRASHED  = 3   # File has been moved to trash location.
RESET    = 4   # Reset metadata action has been invoked. Meta service will update/refresh auto-generated asset information.

# meta_classes

TEXT     = 0   # Single-line plain text (default)
INTEGER  = 1   # Integer only value (for db keys etc)
NUMERIC  = 2   # Any integer of float number. 'min', 'max' and 'step' values can be provided in config
BLOB     = 3   # Multiline text. 'syntax' can be provided in config
DATE     = 4   # Date information. Stored as timestamp, presented as YYYY-MM-DD or calendar
TIME     = 5   # Clock information Stored as timestamp, presened as HH:MM #TBD
DATETIME = 6   # Date and time information. Stored as timestamp
TIMECODE = 7   # Timecode information, stored as float(seconds), presented as HH:MM:SS.CS (centiseconds)
DURATION = 8   # Similar to TIMECODE, Marks and subclips are visualised 
REGION   = 9   # Single time region stored as ///// TBD
REGIONS  = 10  # Multiple time regions stored as json {"region_name":(float(start_second),float(end_second), "second_region_name":(float(start_second),float(end_second)}
SELECT   = 11  # Select box
COMBO    = 12  # Similar to SELECT. Free text can be also provided instead of predefined options
FOLDER   = 13  # Folder selector. Stored as int(id_folder), Represented as text / select. including color etc.
STATUS   = 14  # Asset status representation (with colors or icons). stored as int
STATE    = 15  # Asset approval state representation. stored as int

## Constants
########################################################################