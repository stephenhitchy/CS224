# If you are getting error messages, you need to go to
# the config file and put your spotify User ID and
# User Secret in the two dedicated areas!

import spotipy  # Documentation for spotipy: https://spotipy.readthedocs.io/en/2.9.0/
import config  # Spotify API id's
import os

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
#  Seeing if its a valid user

if __AUTH_TOKEN__:
    # Getting the info of the Users Account
    sp = spotipy.Spotify(auth=__AUTH_TOKEN__)
    print("Connected to Spotify")
else:
    print("Error with AUTH_TOKEN")
    exit()


# Get the top tracks of the Current User, not a user that isn't logged in.
# limit is number of artists we want returned, and time range is how far back we want to go
# in the accounts history, ex 10 weeks vs 10 months
# Returns a list of dictionaries
def get_top_tracks(limit=10, time_range="long_term"):
    tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range)
    top_list = []  # list of dictionaries
    for x in tracks["items"]:
        top_list.append({"name": x["name"], "id": x["id"], "artist": x["artists"][0]["name"],
                         "type": x["type"], "popularity": x["popularity"]})
    return top_list


# Get the top Artists of the Current User, not a user that isn't logged in.
# limit is number of artists we want returned, and time range is how far back we want to go
# in the accounts history, ex 10 weeks vs 10 months
# Returns a list of dictionaries
def get_top_artists(limit=10, time_range="long_term"):
    tracks = sp.current_user_top_artists(limit=limit, time_range=time_range)
    top_list = []  # list of dictionaries
    for x in tracks["items"]:
        top_list.append({"name": x["name"], "id": x["id"], "type": x["type"],
                         "popularity": x["popularity"]})
    return top_list


# Creates a playlist on the actual spotify account
# tracks is a list of track id's, name is the name of the playlist being created, and
# public_playlist is if anyone else will be able to view the playlist.
def create_playlist(tracks, name="Custom Playlist", public_playlist=False,
                    description="Custom Playlist built by song-alyze"):
    print("Current user is: " + sp.current_user()["id"])
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
        s = s[s.find(">") + 1:]
        a = s[s.find("<") + 1:s.find(">")]
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


# Write the information about a user's top tracks and top artists to a file
# users is an array of users that we will be combining their tracks together
def get_user_info(users=[]):
    # Checks to see if the file exists or if the file exists and is empty
    if not (os.path.exists("user_playlist.txt")) or os.stat("user_playlist.txt").st_size == 0:
        # Creates the file if it doesn't exist/Prepare to write to the file
        f = open("user_playlist.txt", "w")

        artists_seeds = get_top_artists()  # Gets top artists from current user
        artist_id_list = []  # list to store ids from artists
        for artist in artists_seeds:
            artist_id_list.append(artist['id'])  # Store ids into the list

        track_seeds = get_top_tracks()  # Get top tracks from current user
        track_id_list = []  # List to store ids from tracks
        for track in track_seeds:
            track_id_list.append(track['id'])  # Store ids into the list

        # Each user's info will take up two lines
        f.write("{}\n".format(artist_id_list))  # Write the list of top artist ids to the file
        f.write("{}\n".format(track_id_list))  # Write the list of top track ids to the file

    else:  # Just append the next set of data
        f = open("user_playlist.txt", "a")  # Creates the file if it doesn't exist/Prepare to write to the file

        artists_seeds = get_top_artists()  # Gets top artists from current user
        artist_id_list = []  # list to store ids from artists
        for artist in artists_seeds:
            artist_id_list.append(artist['id'])  # Store ids into the list

        track_seeds = get_top_tracks()  # Get top tracks from current user
        track_id_list = []  # List to store ids from tracks
        for track in track_seeds:
            track_id_list.append(track['id'])  # Store ids into the list

        # Each user's info will take up 2 lines
        f.write("{}\n".format(artist_id_list))  # Write the list of top artist ids to the file
        f.write("{}\n".format(track_id_list))  # Write teh list of top track ids to the file


# Combine the top tracks and top artists from all users to find recommended artists and tracks
# and returns the result as a dictionary with artist list and track list
def get_combo_playlist():
    print(sp.current_user())

    f = open("user_playlist.txt", "r")  # Opens up file in read mode
    file = f.readlines()  # Reads in all the lines and puts lines into a list
    user_dict = {}  # holds dictionary representation of artist list and track list for each user
    user_num = 1  # Tracks the amount of users starting with 1

    # We will loop through the list and create dictionaries for each user's data
    for row in range(0, len(file), 2):
        # Get rid of details so that it is a coma separated list
        str_artists_list = file[row].strip("\n").strip(']').strip('[').replace("'", "")
        # Get rid of details so that it is a coma separated list
        str_tracks_list = file[row + 1].strip("\n").strip(']').strip('[').replace("'", "")

        artist_list = str_artists_list.split(", ")  # Make the list of artists
        track_list = str_tracks_list.split(", ")  # Make the list of tracks

        user_dict["user{}_artist_list".format(user_num)] = artist_list  # Inserts artist list into dictionary
        user_dict["user{}_track_list".format(user_num)] = track_list  # Inserts track list into dictionary
        user_num += 1

    counter = 1  # Counter keeps track of which users we are currently working with
    # While there are more than 2 keys in the dictionary(2 keys being the userN's artist list
    # and the userN's track list)
    while len(user_dict) > 2:
        # creates a string that looks like a key in dictionary(i.e. {key : value}
        first_user_artist = "user{}_artist_list".format(counter)
        # creates a string that looks like a key in dictionary(i.e. {key : value}
        first_user_track = "user{}_track_list".format(counter)
        counter += 1
        # creates a string that looks like a key in dictionary(i.e. {key : value}
        second_user_artist = "user{}_artist_list".format(counter)
        # creates a string that looks like a key in dictionary(i.e. {key : value}
        second_user_track = "user{}_track_list".format(counter)
        counter += 1

        first_user_artist = user_dict.pop(first_user_artist)  # Remove the first user's artist list
        first_user_track = user_dict.pop(first_user_track)  # Remove the first user's track list

        second_user_artist = user_dict.pop(second_user_artist)  # Remove the second user's artist list
        second_user_track = user_dict.pop(second_user_track)  # Remove the second user's track list

        new_list_artist = []  # New list will hold artists that will be used to find recommendations
        new_list_track = []  # New list will hold tracks that will be used to find recommendations

        for i in first_user_artist:  # First we will find artists that are in both lists
            # if an artist from the first user is found in the second user then we add it to the list
            if i in second_user_artist:
                new_list_artist.append(i)

        for i in first_user_track:  # Find tracks that are in both lists
            if i in second_user_track:  # if a track is in both lists add it to the new list
                new_list_track.append(i)

        first_counter = 0
        second_counter = 0
        # We want 5 search items to pass into recommendation and check to see if we can add more artists
        if len(new_list_artist) != 5 and (len(first_user_artist) > len(new_list_artist)
                                          or len(second_user_artist) > len(new_list_artist)):
            for i in range(5 - len(new_list_artist)):  # Populate the list until we have 5 artists
                if i % 2 == 0:  # We will add an artist from the first list to the new list
                    for j in range(len(first_user_artist)):  # We want to find a new artist to add to the list
                        if first_user_artist[j] not in new_list_artist:
                            new_list_artist.append(first_user_artist[j])
                            break
                        # We reached the end and there are no new artists
                        elif j == len(first_user_artist) and first_counter <= len(first_user_artist) - 1:
                            # We will add the artists located at first_counter
                            new_list_artist.append(first_user_artist[first_counter])
                            first_counter += 1
                            break
                else:  # We will add an artist from teh second list to the new list
                    # We want to find a new artist to add to the list
                    for j in range(len(second_user_artist)):
                        if second_user_artist[j] not in new_list_artist:
                            new_list_artist.append(second_user_artist[j])
                            break
                        # We reached the end and there are no new artists
                        elif j == len(second_user_artist) and second_counter <= len(second_user_track) - 1:
                            # We will add the artists located at first_counter
                            new_list_artist.append(second_user_artist[second_counter])
                            second_counter += 1
                            break

        first_counter = 0
        second_counter = 0
        # We want 5 search items to pass into recommendation and check to see if we can add more tracks
        if len(new_list_track) != 5 and (len(first_user_track) > len(new_list_track)
                                         or len(second_user_track) > len(new_list_track)):
            for i in range(5 - len(new_list_track)):  # Populate the list until we have 5 tracks
                if i % 2 == 0:  # We will add a track from the first list to the new list
                    for j in range(len(first_user_track)):  # We want to find a new track to add to the list
                        if first_user_track[j] not in new_list_track:
                            new_list_track.append(first_user_track[j])
                        # We reached the end and there are no new tracks
                        elif j == len(first_user_track) and first_counter <= len(first_user_track) - 1:
                            # We will add the tracks located at first_counter
                            new_list_track = first_user_track[first_counter]
                            first_counter += 1
                else:  # We will add an track from the second list to the new list
                    for j in range(len(second_user_track)):  # We want to find a new track to add to the list
                        if second_user_track[j] not in new_list_track:
                            new_list_track.append(second_user_track[j])
                        # We reached the end and there are no new tracks
                        elif j == len(second_user_track) and second_counter <= len(second_user_track) - 1:
                            # We will add the tracks located at first_counter
                            new_list_track = second_user_track[second_counter]
                            second_counter += 1

        # new_list_artist = first_user_artist + second_user_artist # Combine both lists to become one list
        # new_list_track = first_user_track + second_user_track # Combine both lists to become one list

        # create a new key so we can compare it in the future and value such that it is the combine list
        user_dict["user{}_artist_list".format(user_num)] = new_list_artist
        # create a new key so we can compare it in the future and value such that it is the combine list
        user_dict["user{}_track_list".format(user_num)] = new_list_track
        user_num += 1

    key_names = user_dict.keys()  # gets all the keys from the dictionary
    rec_artists = []  # the recommended list of artists
    rec_tracks = []  # the recommended list of tracks
    for k in key_names:  # We will find recommendations based off keys
        print("Finding tracks based off: " + k)
        if "artist" in k:
            # Looks for recommended artists
            rec_artists = get_recommended_tracks(artists_seeds=user_dict[k][0:5])
        else:
            # Looks for recommended tracks
            rec_tracks = get_recommended_tracks(track_seeds=user_dict[k][0:5])

    return {"rec_tracks": rec_tracks, "rec_artists": rec_artists}
