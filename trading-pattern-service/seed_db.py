# seed_db.py - use inside the service container to seed the knowledge base entries
from app import db, models
from sqlalchemy import text
from sqlalchemy.orm import Session
import uuid
session = Session(bind=db.engine)
# Insert atoms - if exist, skip
kb_names = {
    "head_and_shoulders": """**Head and Shoulders**
A pattern characterized by 7 alternating low, high, low, etc. points.
**THIS PATTERN ALWAYS HAS EXACTLY 7 POINTS (pattern_size = 7)**.
Where:
 left shoulder: extrema_inds[[0, 1, 2]], shoulder peak at 1
 head: extrema_inds[[2, 3, 4]], head peak at 3
 right shoulder: extrema_inds[[4, 5, 6]], shoulder peak at 5

 the neckline is formed by the bottom line going through points 2 and 4

The pattern is defined by the following *MUST HAVE* conditions:
 * the extremas start on a low, go through a series of high, low points and end on a low
 * the head peak is higher than both shoulders
 * measure the height of shoulders from the neckline, ensure the height is ALWAYS positive

Consult the following diagram:

            o
           /\
    o     /  \      o
  ///\   //   \   //\\
  /   \ /     \  /   \
///     o====  \///   \\\
o           ====o       o


0   1   2   3   4   5   6
    ^       ^       ^
    LS      HEAD    RS

o = extrema
= = neckline through points 2 and 4
Peaks at 1 (left shoulder), 3 (head, highest), 5 (right shoulder)
Lows at 0, 2, 4, 6 (start and end on a low)
""",
    "strong_uptrend": """**Strong Uptrend**
A pattern characterized by *6* alterating low, high, low, etc. points (indices 0-6).
**THIS PATTERN USES 6 ARRAY ELEMENTS**.
Starts at extrema_inds[0] and ends at extrema_inds[5].
A strong trend makes higher lows and higher highs
Where:
  lows: extrema_inds[[0, 2, 4]]
  highs: extrema_inds[[1, 3, 5]]

The pattern **MUST** satisfy the following conditions:
  * the extrema go through an alterating series of lows and highs
  * each low is higher than the previous low
  * each high is higher than the previous high

Consult the following diagram:

               o
         o    /
   o    / \  /
  / \  /   \o
 /   \o
o
0   1   2   3   4   5
^   ^   ^   ^   ^   ^
L   H   L   H   L   H

o = extrema
"""
}
for name, spec in kb_names.items():
    exists = session.execute(text("select id from knowledge_base where name=:name"), {"name":name}).first()
    if not exists:
        session.execute(text("insert into knowledge_base (id, name, spec) values (uuid_generate_v4(), :name, :spec)"), {"name":name, "spec": spec})
session.commit()
print("Seeded knowledge base (if missing)")
