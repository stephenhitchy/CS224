import tkinter
from tkinter import *
from tkinter import messagebox  # tkinter message box
# this import will immediately run code to get a user
import spotify  # Local import of spotify.py
from PIL import Image, ImageTk
from cache import cache  # Used to cache API calls
from spotipy.exceptions import SpotifyException
import os

users: int = 0  # number of users who are being compared


# Main function
# Builds and sets up GUI
def main():
    global users
    root = Tk()
    root.title("Song-alyze")
    root["bg"] = "black"
    root.geometry('1600x1600')
    root.minsize(1600, 1600)  # minimum size of the gui
    base_frame = Frame(root, width=2200, height=2200, borderwidth=2, bg="black")
    base_frame.pack(fill=BOTH, expand=YES)
    base_frame.pack_propagate(False)
    root.withdraw()  # make root invisible during popup lifetime

    # add elements for the main application
    btn_dim = {"w": 15, "h": 2}
    btn_pad = {"x": 10, "y": 10}

    # background image setup
    photo = ImageTk.PhotoImage(Image.open("spotify_bg.png").resize((1600, 1600)))
    label = Label(base_frame, image=photo, bg="black")
    label.place(x=0, y=0, relwidth=1, relheight=1)

    # frames for main buttons
    center_frame1 = Frame(base_frame, borderwidth=2, bg="#1ed760", width=btn_dim["w"],
                          height=btn_dim["h"])
    center_frame1.place(relx=0.1, rely=0.9, anchor=SW)
    center_frame2 = Frame(base_frame, borderwidth=2, bg="#1ed760", width=btn_dim["w"],
                          height=btn_dim["h"])
    center_frame2.place(relx=0.9, rely=.9, anchor=SE)
    center_frame3 = Frame(base_frame, borderwidth=2, bg="#1ed760", width=btn_dim["w"],
                          height=btn_dim["h"])
    center_frame3.place(relx=0.5, rely=.9, anchor=S)

    # image for buttons
    width = 100
    height = 100
    img = Image.open("spotify_bg.png")
    img = img.resize((width, height), Image.ANTIALIAS)
    button_img = ImageTk.PhotoImage(img)

    # Add User button
    add_btn = tkinter.Button(center_frame2, text="Add User", width=400,
                             height=150, command=lambda: show_dual_list_dialog("Add", button_img),
                             image=button_img, compound="left", bg="black", fg="#1ed760")

    # Get Your Top Tracks button
    gen_btn = tkinter.Button(center_frame1, text="Get Your Top Tracks", width=400,
                             height=150, command=lambda: show_dual_list_dialog("Top", button_img),
                             image=button_img, compound="left", bg="black", fg="#1ed760")
    # Get your recommended tracks, based off the songs you like
    rec_btn = tkinter.Button(center_frame3, text="Your Recommended Tracks", width=400,
                             height=150, command=lambda: show_dual_list_dialog("Rec", button_img),
                             image=button_img, compound="left", bg="black", fg="#1ed760")

    gen_btn.grid(row=0, column=0, padx=btn_pad["x"], pady=btn_pad["y"])
    add_btn.grid(row=0, column=2, padx=btn_pad["x"], pady=btn_pad["y"])
    rec_btn.grid(row=0, column=1, padx=btn_pad["x"], pady=btn_pad["y"])

    # create a user login window
    gen_popup(root, button_img)

    root.mainloop()


# Function to create a new user login popup window
def gen_popup(root, button_img):
    login_window = Toplevel(root)
    login_window["bg"] = "black"
    login_window.geometry('800x400')
    login_window.resizable(False, False)
    base_frame = Frame(login_window, width=600, height=400, borderwidth=2, bg="black")
    base_frame.pack(expand=NO)
    base_frame.pack_propagate(False)

    # function that is called when the user closes the popup
    def on_closing():
        popup_close(login_window, root)

    login_window.protocol("WM_DELETE_WINDOW", on_closing)
    label = Label(base_frame, text="Enter Your Spotify Username:", bg="black", fg="#1ed760")
    label.grid(row=0, column=0, padx=50, pady=5)
    username = Text(base_frame, bg="#1ed760", fg="black", height=1, width=20, padx=50, pady=5)
    username.grid(row=1, column=0)
    button_close = tkinter.Button(base_frame, width=400, height=150, text="Login", command=lambda:
                                  add_user(username.get("1.0", "end-1c"), login_window, root),
                                  image=button_img, bg="black", fg="#1ed760", compound="left",
                                  relief=RIDGE)

    button_close.grid(row=2, column=0, padx=10, pady=10)


# Function to take user login info and add top
# songs to the list used for comparison. After,
# close the window
def add_user(username, window, root):
    global users
    users += 1
    # -------------------------------------------------------------------------------------------------------------------------------
    # # Test calling code after show_dual_list_dialog
    if username == 'stephen' or 'john' or 'ying':
        spotify.validate_user(username)
        print(username)
        popup_close(window, root)
    # -------------------------------------------------------------------------------------------------------------------------------
    else:
        print("invalid username")


# Function to close the user login popup window and
# make the root window visible
def popup_close(window, root):
    global users
    if users == 0:
        messagebox.showerror("Cannot Exit", "You must supply at least one user to the program.")
        return
    window.destroy()
    root.deiconify()
    os.remove('.cache')


# Function that creates a new window with 2 list boxes that
# display the generated playlist and the top artists
# Called by Top and Rec buttons
def show_dual_list_dialog(name, button_img):
    # Used as a pointer to point to the current list in this dialog
    # so that the create a playlist buttons knows which list to use
    cur_list = []

    # Function to handle the create playlist button
    def create_playlist_btn_click(id_list):
        spotify.create_playlist([id_list[i]["id"] for i in range(int(default_num_option.get()))],
                                name="Your {} Tracks".format(name))
        # duplicate current view with slight modifications
        show_dual_list_dialog("Gen", button_img)

    def play_playlist_btn_click(id_source):
        ids = []
        for t in id_source:
            e = t["id"]
            ids.append(e)
        try:
            spotify.play_songs(ids)
        except SpotifyException:
            messagebox.showinfo("Error", "You must have spotify premium to use playback functionality.")

    def on_dropdown_change(*args):
        tf = default_timeframe_option.get().lower().split(" ")
        tf = "_".join(tf)
        try:
            get_content(time_frame=tf, limit=int(default_num_option.get()))
        except NameError:
            get_content(time_frame=tf)

    def disp_listbox(order, source_list, number, include_artist, limit):
        lb = tkinter.Listbox(listbox_frame, width=50, height=25, selectmode=tkinter.BROWSE,
                             bg="black", fg="#1ed760", borderwidth=0.0)
        index = 1
        for i in range(0, min(len(source_list), limit)):
            if number:
                if include_artist:
                    lb.insert(index, "{}.  {}  -  {}".format(index, source_list[i]["name"],
                                                             source_list[i]["artist"]))
                else:
                    lb.insert(index, "{}.  {}".format(index, source_list[i]["name"]))
            else:
                if include_artist:
                    lb.insert(index, "{}  -  {}".format(source_list[i]["name"], source_list[i]["artist"]))
                else:
                    lb.insert(index, "{}".format(source_list[i]["name"]))
            index += 1
        lb.grid(row=0, column=order, padx=5, pady=5)

    def get_content(time_frame="long_term", limit=50):
        if name == "Top":
            # Top Tracks stuff, checks to see if the playlist is in the cache
            # (will only be in the cache if we already found the song)
            # if it isn't in the cache we store it in there so we can get it
            # when we are making a new playlist on the persons account.
            top_tracks = spotify.get_top_tracks(limit=50, time_range=time_frame) \
                if not "tt-" + time_frame in cache else cache["tt-" + time_frame]
            cache["tt-" + time_frame] = top_tracks
            cache["cur"] = cache["tt-" + time_frame]
            disp_listbox(0, top_tracks, True, True, limit)
            # Top Artists stuff, checks to see if the playlist is in the cache
            # (will only be in the cache if we already found the song)
            # if it isn't in the cache we store it in there so we can get it
            # when we are making a new playlist on the persons account.
            top_artists = spotify.get_top_artists(limit=50, time_range=time_frame) \
                if not "ta-" + time_frame in cache \
                else cache["ta-" + time_frame]
            cache["ta-" + time_frame] = top_artists
            disp_listbox(1, top_artists, True, False, limit)
        elif name == "Gen":
            # Generated playlist view
            top_tracks = spotify.get_combo_playlist() \
                if not "tt-" + time_frame in cache \
                else cache["tt-" + time_frame]
            rec_tracks = spotify.get_recommended_tracks(limit=50, track_seeds=[x["id"] for x in top_tracks[:5]]) \
                if not "rt-" + time_frame in cache \
                else cache["rt-" + time_frame]
            cache["rt-" + time_frame] = rec_tracks
            cache["cur"] = cache["rt-" + time_frame]
            disp_listbox(0, rec_tracks, False, True, limit)
            # Rec Artists stuff
            rec_artists = spotify.get_recommended_artists(time_range=time_frame, limit=50) \
                if not "ra-" + time_frame in cache \
                else cache["ra-" + time_frame]
            cache["ra-" + time_frame] = rec_artists
            disp_listbox(1, rec_artists, False, False, limit)
        elif name == "Rec":
            # Rec Tracks stuff, same as the Top Artists Stuff above.
            top_tracks = spotify.get_top_tracks(limit=50, time_range=time_frame) \
                if not "tt-" + time_frame in cache \
                else cache["tt-" + time_frame]
            rec_tracks = spotify.get_recommended_tracks(limit=50, track_seeds=[x["id"] for x in top_tracks[:5]]) \
                if not "rt-" + time_frame in cache \
                else cache["rt-" + time_frame]
            cache["rt-" + time_frame] = rec_tracks
            cache["cur"] = cache["rt-" + time_frame]
            disp_listbox(0, rec_tracks, False, True, limit)
            # Rec Artists stuff
            rec_artists = spotify.get_recommended_artists(time_range=time_frame, limit=50) \
                if not "ra-" + time_frame in cache \
                else cache["ra-" + time_frame]
            cache["ra-" + time_frame] = rec_artists
            disp_listbox(1, rec_artists, False, False, limit)
        elif name == "Add":
            spotify.get_user_info()
            combo_list = spotify.get_combo_playlist()
            rec_tracks = combo_list['rec_tracks']
            rec_artists = combo_list['rec_artists']
            disp_listbox(0, rec_tracks, False, True, limit)
            disp_listbox(1, rec_artists, False, False, limit)
            print(combo_list)
        else:
            print("Unsupported option passed into the show_list function.")
            exit()

    # Making the gui look nicer
    top = tkinter.Toplevel()
    top.grab_set()
    top["bg"] = "black"
    option_frame = tkinter.Frame(top)
    option_frame["bg"] = "black"
    option_frame.grid(row=0)
    label_frame = tkinter.Frame(top)
    label_frame["bg"] = "black"
    label_frame.grid(row=1, pady=5)
    listbox_frame = tkinter.Frame(top)
    listbox_frame["bg"] = "#1ed760"
    listbox_frame.grid(row=2)
    top.title(name + " Artists & Tracks")
    top.resizable(False, False)

    # Buttons after you click into the playlist, where you see the dropdown list
    # and the buttons at the top.
    if name != "Gen":
        gen_playlist_btn = tkinter.Button(option_frame, text="Create Playlist", width=400, height=150,
                                          command=lambda: create_playlist_btn_click(cache["cur"]),
                                          image=button_img, bg="black", fg="#1ed760", compound="left",
                                          relief=RIDGE)
        gen_playlist_btn.grid(row=0, column=0, padx=5, pady=5)
    time_frame_options = ["Short Term", "Medium Term", "Long Term"]
    default_timeframe_option = tkinter.StringVar(option_frame)
    default_timeframe_option.trace("w", on_dropdown_change)
    default_timeframe_option.set(time_frame_options[1])
    time_frame_menu = tkinter.OptionMenu(option_frame, default_timeframe_option, *time_frame_options)
    time_frame_menu["bg"] = "black"
    time_frame_menu["fg"] = "#1ed760"
    time_frame_menu["highlightthickness"] = 0.1
    time_frame_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tkinter.NSEW)
    number_options = [10, 25, 50]
    default_num_option = tkinter.StringVar(option_frame)
    default_num_option.trace("w", on_dropdown_change)
    default_num_option.set(number_options[2])
    number_menu = tkinter.OptionMenu(option_frame, default_num_option, *number_options)
    number_menu["bg"] = "black"
    number_menu["fg"] = "#1ed760"
    number_menu["highlightthickness"] = 0.1
    number_menu.grid(row=0, column=2, padx=5, pady=5, sticky=tkinter.NSEW)
    play_playlist_btn = tkinter.Button(option_frame, text="Play Playlist", width=400, height=150,
                                      command=lambda: play_playlist_btn_click(cache["cur"]),
                                      image=button_img, bg="black", fg="#1ed760", compound="left",
                                      relief=RIDGE)
    play_playlist_btn.grid(row=0, column=3, padx=5, pady=5)

    songs_label = tkinter.Label(label_frame, text="Songs", bg="black", fg="#1ed760", font=("Arial", 12))
    songs_label.grid(row=0, column=0, padx=425)
    artists_label = tkinter.Label(label_frame, text="Artists", bg="black", fg="#1ed760", font=("Arial", 12))
    artists_label.grid(row=0, column=1, padx=425)

    center_in_screen(top)
    top.mainloop()



def center_in_screen(window):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width / 2) - 375
    y = (screen_height / 2) - 300
    window.geometry("+%d+%d" % (x, y))


if __name__ == "__main__":
    # Helps with the graphical issues
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    main()
