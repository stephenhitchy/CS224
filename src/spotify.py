# If you are getting error messages, you need to go to
# the config file and put your spotify User ID and
# User Secret in the two dedicated areas!

import spotipy  # Documentation for spotipy: https://spotipy.readthedocs.io/en/2.9.0/
import config  # Spotify API id's

global sp

# Various scopes to get access to. View scopes here: https://developer.spotify.com/documentation/general/guides/scopes/
__SPOTIFY_SCOPES__ = "user-top-read playlist-read-private user-read-recently-played " \
                     "playlist-modify-private playlist-modify-public user-library-read " \
                     "user-modify-playback-state"  # Should not be changed after this line
# Authorization token specific to the users account
__AUTH_TOKEN__ = spotipy.prompt_for_user_token(username="", scope=__SPOTIFY_SCOPES__,
                                               client_id="33b20c9a6bd14aa49a6c932aec63e4ac",
                                               client_secret="f8c80aaad212464c901e38d791c81431",
                                               redirect_uri="http://localhost:8080/",
                                               show_dialog=True)
print("Attempting Authentication with Spotify...")
#  If AUTH_TOKEN is legit...

if __AUTH_TOKEN__:
    # Use sp to call Spotify API functions. List of API endpoints:
    # https://developer.spotify.com/documentation/web-api/reference/
    sp = spotipy.Spotify(auth=__AUTH_TOKEN__)
    print("Connected to Spotify")
else:
    print("Error with AUTH_TOKEN")
    exit()


# Function to get the users top tracks. Limit is the number of tracks to get,
# time_range is what period of time to use: short_term, medium_term, or long_term
# Returns a list of dictionaries
def get_top_tracks(limit=10, time_range="long_term"):
    tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range)
    top_list = []  # list of dictionaries
    for x in tracks["items"]:
        top_list.append({"name": x["name"], "id": x["id"], "artist": x["artists"][0]["name"],
                         "type": x["type"], "popularity": x["popularity"]})
    return top_list


# Function to get the users top artists. Limit is the number of tracks to get,
# # time_range is what period of time to use: short_term, medium_term, or long_term
# Returns a list of dictionaries
def get_top_artists(limit=10, time_range="long_term"):
    tracks = sp.current_user_top_artists(limit=limit, time_range=time_range)
    top_list = []  # list of dictionaries
    for x in tracks["items"]:
        top_list.append({"name": x["name"], "id": x["id"], "type": x["type"],
                         "popularity": x["popularity"]})
    return top_list


# Function to create a playlist based on a list of songs
# tracks is a list of track id's
def create_playlist(tracks, name="Custom Playlist", public_playlist=False,
                    description="Custom Playlist built by song-alyze"):
    playlist = sp.user_playlist_create(user=sp.current_user()["id"], name=name, public=public_playlist,
                                       description=description)
    sp.user_playlist_add_tracks(user=sp.current_user()["id"], playlist_id=playlist["id"], tracks=tracks)


# Function to create a playlist based on your top artists and songs
# name - the name of the playlist
# description - description of playlist
# public_playlist - boolean, true if public
# time_frame - the time frame (short_term, medium_term, long_term) to determine your top artists and
# tracks from
# limit - number of songs
# strictly_new - boolean, true if you want this playlist to contain songs that are NOT in your current
# library (playlists or user library)
# Note: if you use strictly_new, function will be slower since it needs to scan through user's library
def create_recommended_playlist(name="song-alyze Recommendations", description="Here's some tracks you might like!",
                                public_playlist=False, time_frame="long_term", songs=[], limit=50, strictly_new=False):
    if len(songs) == 0:
        # seeds used for get_top_artists function
        artist_seeds = [artist["id"] for artist in get_top_artists(3, time_frame)]
        # seeds used for get_top_tracks function
        track_seeds = [track["id"] for track in get_top_tracks(2, time_frame)]
        tracks = get_recommended_tracks(artists_seeds=artist_seeds, track_seeds=track_seeds, limit=limit)
    else:
        artist_seeds = []
        track_seeds = [x["id"] for x in songs]
        tracks = get_recommended_tracks(track_seeds=[x["id"] for x in songs], limit=limit)

    if strictly_new:  # if tracks saved in user library shouldn't be in this created playlist
        # two sets, one of song id's, the other of strings in for the from "<title of song> <artist>"
        # the latter is used when there may be the same song more than once on spotify
        #  for example an explicit and non-explicit version of the same song
        master_track_ids, master_track_atts = get_master_track_list()
        # duplicates to remove
        to_remove = []
        for track in tracks:
            # if the song is in the user's library already...remove it
            if track["id"] in master_track_ids or "<{}><{}>".format(track["name"], track["artist"]) \
                    in master_track_atts:
                to_remove.append(track)
        # remove duplicates
        for track_rem in to_remove:
            tracks.remove(track_rem)
        # add more new unique songs until the playlist is of the requested size
        while len(tracks) < limit:
            new_tracks = get_recommended_tracks(artists_seeds=artist_seeds, track_seeds=track_seeds, limit=limit)
            for new_track in new_tracks:
                # if the track is not already in user's library...add it to the playlist
                if (new_track["id"] not in master_track_ids) and (new_track not in tracks) and \
                        (len(tracks) < limit) and "<{}><{}>".format(new_track["name"], new_track["artist"]) \
                        not in master_track_atts:
                    tracks.append(new_track)
    create_playlist([track["id"] for track in tracks], name=name, description=description,
                    public_playlist=public_playlist)


# A function that can get recommended artists, tracks, or genres
# Provide either a list of artists, tracks, or genres (id's)
# (NO MORE THAN 5 i.e. Up to 5 seed values may be provided in any combination of seed_artists,
# seed_tracks and seed_genres)
# Returns a list of dictionaries
def get_recommended_tracks(artists_seeds=[], track_seeds=[], genre_seeds=[], limit=10, country=None):
    rec = sp.recommendations(seed_artists=artists_seeds, seed_tracks=track_seeds, seed_genres=genre_seeds,
                             limit=limit, country=country)
    rec_list = []
    for track in rec["tracks"]:
        rec_list.append({"name": track["name"], "artist": track["artists"][0]["name"], "id": track["id"]})
    return rec_list


# Function to get recommended artists based on user's top artist.
# time_range is the period to get the top artist from--short_term, medium_term, or long_term
# Returns a list of dictionaries
def get_recommended_artists(time_range="long_term", limit=10):
    top = get_top_artists(limit=1, time_range=time_range)[0]["id"]
    recommend = sp.artist_related_artists(top)
    new_artists = []
    for r in recommend['artists']:
        new_artists.append({"name": r["name"], "id": r["id"], "type": r["type"], "popularity": r["popularity"]})
    return new_artists[:limit]


# Function to get a set of all saved song id's in the user's library
# This includes songs from saved playlists and songs in library
# Returns a set! Not a list!
def get_master_track_list():
    master_track_ids = set()  # set of track id's in users library
    master_track_atts = set()  # set of strings in the form "<title><artist>" in users library
    # use set since we only want to know if a song is in the set. Gets the benefit of hashing.
    # O(1) time complexity and no duplicates
    playlist_ids = [p["id"] for p in sp.current_user_playlists()["items"]]
    # loop through users playlists
    for p in playlist_ids:
        p_len = sp.playlist(p)["tracks"]["total"]  # num of songs in playlist
        current_offset = 0  # index in playlist of song to grab first
        while current_offset <= p_len:
            # for each track in current playlist
            for s in sp.playlist_tracks(p, limit=100, offset=current_offset)["items"]:
                master_track_ids.add(s["track"]["id"])
                master_track_atts.add("<{}><{}>".format(s["track"]["name"], s["track"]["artists"][0]["name"]))
            current_offset += 100
    # loop through users saved tracks
    for item in sp.current_user_saved_tracks()["items"]:
        master_track_ids.add(item["track"]["id"])
        master_track_atts.add("<{}><{}>".format(item["track"]["name"], item["track"]["artists"][0]["name"]))
    print(master_track_atts)
    return master_track_ids, master_track_atts


# Function to check if a song is already saved in the currently user's library,
# useful for checking to see if a user likes/has heard a song before
# songs is a list of one or more song ids
# Returns list of dictionary's with song name, id, and boolean true or false indicating if the song
# is saved in the user's library
def in_library(songs):
    saved_or_not = sp.current_user_saved_tracks_contains(songs)
    out = []
    for i in range(len(songs)):
        out.append({"name": sp.track(songs[i])["name"], "id": songs[i], "in_lib": saved_or_not[i]})
    return out


# Function to check if a single song is in a users saved library
# Returns a boolean
def song_in_library(song):
    return in_library(song)[0]["in_lib"]


# Gets a track search result from Spotify
# Returns a dictionary to represent the first search result
def get_search_result(query):
    res = sp.search(query, type="track", limit=1)["tracks"]["items"][0]
    return {"name": res["name"], "type": res["type"], "id": res["id"], "artist": res["artists"][0]["name"],
            "artist_id": res["artists"][0]["id"]}


# Returns a sorted tuple (Artist, Frequency) of the most seen artists in a users library
def artist_count():
    songs = get_master_track_list()[1]
    print(len(songs))
    dictionary = {}
    for s in songs:
        s = s[s.find(">")+1:]
        a = s[s.find("<")+1:s.find(">")]
        dict[a] = dictionary[a] + 1 if a in dict else 1
    sort = sorted(dictionary.items(), reverse=True, key=lambda e: e[1])
    return sort


# Given a list of song ids, starts playing those songs on the device you were last listening on
def play_songs(id_list):
    uri_list = []
    for i in id_list:
        uri = "spotify:track:" + i
        uri_list.append(uri)
    sp.start_playback(uris=uri_list)
