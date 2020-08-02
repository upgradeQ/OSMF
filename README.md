# OSU-STREAM-DETECTOR
- An osu tool for finding stream maps in your map library
- Try online : https://osufiles.github.io/stream-map/ 

# Install 
- python - Python 3.6+
- download is_it_stream.py or `pip install osustreams`

# Usage
As a single is_it_stream.py file
- run from console , `python is_it_stream.py`  with optional arguments
- check output file with name `Stream maps[{min_bpm}-{max_bpm}] {timestamp}.txt`

As a pip package 
```
usage: osustreams [-h] [--collection] [-a A] [-b B]
optional arguments:
  -h, --help        show this help message and exit
  --collection, -c  export to in-game collection
  -a A              Min bpm
  -b B              Max bpm
  --ignore, -i      ignore bad unicode
```
- example :`osustreams -a 110 -b 170 -c` 
- this will create in-game collection with beatmaps where a = min BPM , b = max BPM

stream_detector.ini - should be located in Lib/site-packages (if you wish to edit path to osu/songs) 
Note: As of current, this tool can only scan maps from around 2016-present due to differences in file formatting

# This is a fork
https://github.com/iMeisa/OSMF
