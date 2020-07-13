import time as _time
import operator
import hashlib
from struct import unpack
from shutil import copy
from pathlib import Path
from multiprocessing import Pool

# EDIT THIS
song_path = r"F:\ULL\PATH\TO\osu\songs"
min_bpm = 140
max_bpm = 9999


_p = Path(song_path)
collection_db = _p.absolute().parent / "collection.db"
timestamp = int(_time.time())
file_name = f"Stream maps[{min_bpm}-{max_bpm}] {timestamp}.txt"


def adjust_beat_length(beat_length, new_bpm):
    current_bpm = new_bpm
    whole = beat_length
    half = whole / 2
    quarter = half / 2
    return current_bpm, whole, half, quarter


def _check(of, min_bpm=min_bpm, max_bpm=max_bpm):
    raw_map = open(of, "r", encoding="utf8").readlines()
    if raw_map[0] != "osu file format v14\n":
        return False
    timing_points_index = raw_map.index("[TimingPoints]\n")
    objects_index = raw_map.index("[HitObjects]\n")
    metadata_index = raw_map.index("[Metadata]\n")

    beatmap = {
        "bpm": {"default": {"time": 0, "bpm": 0, "beatLength": 0}, "changes": []}
    }

    for i in range(metadata_index + 1, len(raw_map)):
        if raw_map[i] == "\n":
            break

        if raw_map[i].startswith("Title:"):
            beatmap["title"] = raw_map[i][6:-1]
        if raw_map[i].startswith("Artist:"):
            beatmap["artist"] = raw_map[i][7:-1]
        if raw_map[i].startswith("Version:"):
            beatmap["difficulty"] = raw_map[i][8:-1]

    # Determine BPM and BPM changes
    for i in range(timing_points_index + 1, len(raw_map)):
        if raw_map[i] == "\n":
            break

        point = raw_map[i].split(",")
        time = int(float(point[0]))
        beatLength = float(point[1])
        if beatLength > 0:
            default_bpm = beatmap["bpm"]["default"]
            bpm = str(int(60000 // beatLength))
            if default_bpm["bpm"] == 0:
                default_bpm["time"] = time
                default_bpm["bpm"] = bpm
                default_bpm["beatLength"] = beatLength
            else:
                beatmap["bpm"]["changes"].append(
                    {"time": time, "bpm": bpm, "beatLength": beatLength}
                )

    first_object = objects_index + 1
    previous_object = {"time": 0, "x": 0, "y": 0}
    current_bpm = beatmap["bpm"]["default"]["bpm"]
    whole = beatmap["bpm"]["default"]["beatLength"]
    half = whole / 2
    quarter = half / 2
    quarter_note_count = 1
    note_start_time = 0
    burst_count = 0
    stream_count = {}
    total_stream_notes = 0
    longest_stream = 0
    for i in range(first_object, len(raw_map)):
        raw_hit_object = raw_map[i].split(",")
        if i != len(raw_map) - 1:
            next_raw_hit_object = raw_map[i + 1].split(",")
        else:
            next_raw_hit_object = "000"

        hit_object = {
            "time": int(raw_hit_object[2]),
            "x": int(raw_hit_object[0]),
            "y": int(raw_hit_object[1]),
        }

        changes = beatmap["bpm"]["changes"]
        for change in changes:
            time_change = change["time"]
            new_beatlength = change["beatLength"]
            new_bpm = change["bpm"]
            if time_change < previous_object["time"]:
                continue
            elif hit_object["time"] >= time_change:

                current_bpm, whole, half, quarter = adjust_beat_length(
                    new_beatlength, new_bpm
                )
                break

        # Determine if quarter length
        if i != first_object:
            time_difference = hit_object["time"] - previous_object["time"]
            if quarter - 2 < time_difference < quarter + 2:
                quarter_note_count += 1
                if note_start_time == 0:
                    note_start_time = hit_object["time"]

            else:
                # Declare if stream
                if 3 < quarter_note_count < 6:
                    burst_count += 1
                    total_stream_notes += quarter_note_count
                elif quarter_note_count >= 6:
                    if current_bpm in stream_count:
                        stream_count[current_bpm] += 1
                    else:
                        stream_count[current_bpm] = 1
                    total_stream_notes += quarter_note_count

                if quarter_note_count > longest_stream:
                    longest_stream = quarter_note_count
                quarter_note_count = 1
                note_start_time = 0

        previous_object = hit_object

    if len(stream_count) > 0:
        main_bpm = int(max(stream_count.items(), key=operator.itemgetter(1))[0])
    else:
        main_bpm = int(beatmap["bpm"]["default"]["bpm"])

    total_streams = 0
    for bpm in stream_count:
        total_streams += stream_count[bpm]

    total_object_count = len(raw_map) - first_object
    try:
        stream_percentage = total_stream_notes / total_object_count * 100
    except ZeroDivisionError:
        stream_percentage = 0

    if stream_percentage >= 25 and main_bpm >= min_bpm and main_bpm <= max_bpm:
        with open(file_name, "a") as f:
            print(
                beatmap["title"], beatmap["difficulty"], f" {int(stream_percentage)}%"
            )
            f.write(
                f'{beatmap["artist"]} - {beatmap["title"]} [{beatmap["difficulty"]}] | Main BPM: {main_bpm} | Total Streams: {total_streams} ({int(stream_percentage)}% Streams)\n'
            )
            return of
    return False


def get_osu_files(pathlib_object):
    """traverse osu/songs path, find *.osu files,get paths to osufiles"""

    songdirs = []
    for song_dir in pathlib_object.iterdir():
        # is it osu beatmap?
        if str(song_dir.name).split()[0].isdigit():
            # check if there is osu file in directory, this might happen if you deleted all song difs
            if list(song_dir.glob("*.osu")):
                songdirs.append(str(song_dir.name))

    paths = map(pathlib_object.joinpath, songdirs)
    osufiles = []

    for i in paths:
        for osufile in Path(i).glob("*.osu"):
            osufiles.append(osufile)

    return osufiles


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def nextint(f):
    return unpack("<I", f.read(4))[0]


def nextstr(f):
    if f.read(1) == 0x00:
        return
    len = 0
    shift = 0
    while True:
        byte = ord(f.read(1))
        len |= (byte & 0b01111111) << shift
        if (byte & 0b10000000) == 0:
            break
        shift += 7
    return f.read(len).decode("utf-8")


def get_collections():
    """read .db file, return raw collection"""
    col = {}
    f = open(collection_db, "rb")
    version = nextint(f)
    ncol = nextint(f)
    for i in range(ncol):
        colname = nextstr(f)
        col[colname] = []
        for j in range(nextint(f)):
            f.read(2)
            col[colname].append(f.read(32).decode("utf-8"))
    f.close()
    return (col, version)


def write_int(file, integer):
    int_b = integer.to_bytes(4, "little")
    file.write(int_b)


def get_uleb128(integer):
    result = 0
    shift = 0
    while True:
        byte = integer

        result |= (byte & 0x7F) << shift
        # Detect last byte:
        if byte & 0x80 == 0:
            break
        shift += 7
    return result.to_bytes(1, "little")


def write_string(file, string):
    if not string:
        # If the string is empty, the string consists of just this byte
        return bytes([0x00])
    else:
        # Else, it starts with 0x0b
        result = bytes([0x0B])

        # Followed by the length of the string as an ULEB128
        result += get_uleb128(len(string))

        # Followed by the string in UTF-8
        result += string.encode("utf-8")
        file.write(result)


def update_collection(list_of_osu_files):
    """manually add beatmaps to .db file
    create ingame collections https://github.com/osufiles/osuCollectionManager-backup 
    """
    backup_db = collection_db.parents[0] / "OFSbackup_collection.db"
    # read version ,count
    collection_dict, version = get_collections()
    # copy as backup.db , osu client on launch will create .bak also
    if not backup_db.exists():
        copy(collection_db, backup_db)
    hashes = []
    for h in list_of_osu_files:
        difficultly_hash = md5(h)
        hashes.append(difficultly_hash)
    name = file_name
    collection_dict[name] = hashes
    with open(collection_db, "wb") as f:
        # write version int , count int
        write_int(f, version)
        write_int(f, len(collection_dict))
        # for each collection including generated
        for col_name, col_hashes in collection_dict.items():
            # write its name string,maps count len(),write hashes md5s
            write_string(f, col_name)
            write_int(f, len(col_hashes))
            for h in col_hashes:
                write_string(f, h)
    print("Export to db complete,quantity: ", len(list_of_osu_files))


if __name__ == "__main__":

    of = get_osu_files(Path(song_path))
    with Pool() as pool:
        audios = pool.map(_check, of)
    dot_osu_files = list(filter(None, audios))
    print("Found", len(dot_osu_files), "stream maps,check:", '"' + file_name + '"')
    update_collection(dot_osu_files)
