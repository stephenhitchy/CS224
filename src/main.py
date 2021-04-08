import tkinter  # GUI  Reference: https://www.tutorialspoint.com/python/python_gui_programming.htm
from tkinter import *
from tkinter import messagebox  # tkinter message box
import spotify  # Local import of spotify.py
from PIL import Image, ImageTk
from cache import cache  # Used to cache API calls
from spotipy.exceptions import SpotifyException

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

    # create a user login window
    gen_popup(root)

    # add elements for the main application
    btn_dim = {"w": 15, "h": 2}
    btn_pad = {"x": 10, "y": 10}

    photo = ImageTk.PhotoImage(Image.open("spotify_bg.png").resize((1600, 1600)))
    label = Label(base_frame, image=photo, bg="black")
    label.place(x=0, y=0, relwidth=1, relheight=1)

    center_frame1 = Frame(base_frame, borderwidth=2, bg="#1ed760", width=btn_dim["w"],
                          height=btn_dim["h"])
    center_frame1.place(relx=0.6, rely=.9, anchor=SW)
    center_frame2 = Frame(base_frame, borderwidth=2, bg="#1ed760", width=btn_dim["w"],
                          height=btn_dim["h"])
    center_frame2.place(relx=0.4, rely=.9, anchor=SE)

    width = 100
    height = 100
    img = Image.open("spotify_bg.png")
    img = img.resize((width, height), Image.ANTIALIAS)
    button_img = ImageTk.PhotoImage(img)

    # Rec Tracks & Artists button
    rec_btn = tkinter.Button(center_frame2, text="     Add User", width=400,
                             height=150, command=lambda: show_dual_list_dialog("Rec"),
                             image=button_img, compound="left")
    # Top Tracks & Artists button
    top_btn = tkinter.Button(center_frame1, text="  Generate Playlist", width=400,
                             height=150, command=lambda: show_dual_list_dialog("Top"),
                             image=button_img, compound="left")
    top_btn.config(image=button_img)

    top_btn.grid(row=0, column=0, padx=btn_pad["x"], pady=btn_pad["y"])
    rec_btn.grid(row=0, column=1, padx=btn_pad["x"], pady=btn_pad["y"])
    root.mainloop()


# Function to create a new user login popup window
def gen_popup(root):
    login_window = Toplevel()

    # function that is called when the user closes the popup
    def on_closing():
        popup_close(login_window, root)

    login_window.protocol("WM_DELETE_WINDOW", on_closing)
    label = Label(login_window, text="Enter User Login Info:")
    label.pack(fill='x', padx=50, pady=5)
    username = Text(login_window, bg="#1ed760", fg="black", height=1, width=20)
    username.pack()
    password = Text(login_window, bg="#1ed760", fg="black", height=1, width=20)
    password.pack()
    button_close = Button(login_window, text="Login", command=lambda: add_user(username.get("1.0", "end-1c"),
                                                                               password.get("1.0", "end-1c"),
                                                                               login_window, root))
    button_close.pack(fill='x')


# Function to take user login info and validate it. If
# the login information is correct, add top songs to the
# list used for comparison and close the window
def add_user(username, password, window, root):
    global users
    print(username + "\n" + password)
    # if the login is valid, increment users and close
    if True:
        users += 1
    popup_close(window, root)


# Function to close the user login popup window and
# make the root window visible
def popup_close(window, root):
    global users
    if users == 0:
        messagebox.showerror("Cannot Exit", "You must supply at least one user to the program.")
        return
    window.destroy()
    root.deiconify()


# Function that creates a new window with 2 list boxes that
# display the generated playlist and the top artists
# Called by Top and Rec buttons
def show_dual_list_dialog(type):
    # Used as a pointer to point to the current list in this dialog
    # so that the create a playlist buttons knows which list to use
    cur_list = []

    # Function to handle the create playlist button
    def create_playlist_btn_click(list):
        spotify.create_playlist([list[i]["id"] for i in range(int(default_num_option.get()))],
                                name="Your {} Tracks".format(type))
        messagebox.showinfo("Success", "Playlist Created!")

    def play_playlist_btn_click(list):
        ids = []
        for t in list:
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

    def disp_listbox(order, list, number, include_artist, limit):
        lb = tkinter.Listbox(listbox_frame, width=50, height=25, selectmode=tkinter.BROWSE)
        index = 1
        for i in range(0, min(len(list), limit)):
            if number:
                if include_artist:
                    lb.insert(index, "{}.  {}  -  {}".format(index, list[i]["name"], list[i]["artist"]))
                else:
                    lb.insert(index, "{}.  {}".format(index, list[i]["name"]))
            else:
                if include_artist:
                    lb.insert(index, "{}  -  {}".format(list[i]["name"], list[i]["artist"]))
                else:
                    lb.insert(index, "{}".format(list[i]["name"]))
            index += 1
        lb.grid(row=0, column=order, padx=5, pady=5)

    def get_content(time_frame="long_term", limit=50):
        if type == "Top":
            # Top Tracks stuff
            top_tracks = spotify.get_top_tracks(limit=50, time_range=time_frame) if not "tt-" + time_frame in cache else \
            cache["tt-" + time_frame]
            cache["tt-" + time_frame] = top_tracks
            cache["cur"] = cache["tt-" + time_frame]
            disp_listbox(0, top_tracks, True, True, limit)
            # Top Artists stuff
            top_artists = spotify.get_top_artists(limit=50,
                                                  time_range=time_frame) if not "ta-" + time_frame in cache else cache[
                "ta-" + time_frame]
            cache["ta-" + time_frame] = top_artists
            disp_listbox(1, top_artists, True, False, limit)
        elif type == "Rec":
            # Rec Tracks stuff
            top_tracks = spotify.get_top_tracks(limit=50, time_range=time_frame) if not "tt-" + time_frame in cache else \
                cache["tt-" + time_frame]
            rec_tracks = spotify.get_recommended_tracks(limit=50, track_seeds=[x["id"] for x in top_tracks[
                                                                                                :5]]) if not "rt-" + time_frame in cache else \
            cache["rt-" + time_frame]
            cache["rt-" + time_frame] = rec_tracks
            cache["cur"] = cache["rt-" + time_frame]
            disp_listbox(0, rec_tracks, False, True, limit)
            # Rec Artists stuff
            rec_artists = spotify.get_recommended_artists(time_range=time_frame,
                                                          limit=50) if not "ra-" + time_frame in cache else \
                cache["ra-" + time_frame]
            cache["ra-" + time_frame] = rec_artists
            disp_listbox(1, rec_artists, False, False, limit)
        else:
            print("Unsupported option passed into the show_list function.")
            exit()

    top = tkinter.Toplevel()
    top.grab_set()
    option_frame = tkinter.Frame(top)
    option_frame.grid(row=0)
    listbox_frame = tkinter.Frame(top)
    listbox_frame.grid(row=1)
    top.title(type + " Artists & Tracks")
    top.resizable(False, False)

    # option frame widgets
    gen_playlist_btn = tkinter.Button(option_frame, text="Create Playlist", width=15, height=1,
                                      command=lambda: create_playlist_btn_click(cache["cur"]))
    gen_playlist_btn.grid(row=0, column=0, padx=5, pady=5)
    time_frame_options = ["Short Term", "Medium Term", "Long Term"]
    default_timeframe_option = tkinter.StringVar(option_frame)
    default_timeframe_option.trace("w", on_dropdown_change)
    default_timeframe_option.set(time_frame_options[2])
    time_frame_menu = tkinter.OptionMenu(option_frame, default_timeframe_option, *time_frame_options)
    time_frame_menu.grid(row=0, column=1, padx=5, pady=5)
    number_options = [10, 25, 50]
    default_num_option = tkinter.StringVar(option_frame)
    default_num_option.trace("w", on_dropdown_change)
    default_num_option.set(number_options[2])
    number_menu = tkinter.OptionMenu(option_frame, default_num_option, *number_options)
    number_menu.grid(row=0, column=2, padx=5, pady=5)
    gen_playlist_btn = tkinter.Button(option_frame, text="Play Playlist", width=15, height=1,
                                      command=lambda: play_playlist_btn_click(cache["cur"]))
    gen_playlist_btn.grid(row=0, column=3, padx=5, pady=5)

    center_in_screen(top)
    top.mainloop()


def center_in_screen(window):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width / 2) - 375  # can't figure out how to get current windows size
    y = (screen_height / 2) - 300
    window.geometry("+%d+%d" % (x, y))


if __name__ == "__main__":
    import ctypes

    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # solves blurry tkinter widgets...thanks stack overflow
    main()
