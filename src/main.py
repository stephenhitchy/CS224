
import spotify  # Local import of spotify.py
import tkinter  # GUI  Reference: https://www.tutorialspoint.com/python/python_gui_programming.htm
from tkinter import font as tkFont  # tkinter fonts
from tkinter import messagebox  # tkinter message box
import ttkthemes  # tkinter themes
from tkinter import filedialog as fd  # tkinter file dialog
import os
from cache import cache  # Used to cache API calls


# Main function
# Builds and sets up GUI
def main():
    # Beginning of GUI
    print("Building GUI...")
    main_window = tkinter.Tk(screenName="song-alyze")
    main_window.title("song-alyze")
    main_window.resizable(False, False)
    theme = ttkthemes.ThemedStyle(main_window)
    theme.theme_use("arc")  # Never got this to work. Not sure why
    info_frame = tkinter.Frame(main_window)
    content_frame = tkinter.Frame(main_window)
    info_frame.grid(row=0, column=0)
    content_frame.grid(row=1, column=0)
    center_in_screen(main_window)
    font = tkFont.Font(family="Segoe UI", size=11)
    main_window.option_add("*Font", font)
    btn_dim = {"w": 30, "h": 5}
    btn_pad = {"x": 10, "y": 10}

    # Welcome label
    wel_lbl_txt = tkinter.StringVar()
    wel_lbl_txt.set("Welcome {}".format(spotify.sp.current_user()["display_name"]))
    wel_lbl = tkinter.Label(info_frame, textvariable=wel_lbl_txt)
    tit_lbl_txt = tkinter.StringVar()
    tit_lbl_txt.set("song-alyze")
    title_lbl = tkinter.Label(info_frame, textvariable=tit_lbl_txt, font=("Segoe UI Bold", 14))
    # Top Tracks & Artists button
    top_btn = tkinter.Button(content_frame, text="Top Tracks & Artists", width=btn_dim["w"], height=btn_dim["h"],
                                    command=lambda: show_dual_list_dialog("Top"))
    # Rec Tracks & Artists button
    rec_btn = tkinter.Button(content_frame, text="Recommended Tracks & Artists", width=btn_dim["w"], height=btn_dim["h"],
                                 command=lambda: show_dual_list_dialog("Rec"))
    title_lbl.grid(row=0, column=0)
    wel_lbl.grid(row=1, column=0)
    top_btn.grid(row=0, column=0, padx=btn_pad["x"], pady=btn_pad["y"])
    rec_btn.grid(row=0, column=1, padx=btn_pad["x"], pady=btn_pad["y"])
    main_window.mainloop()


# Function that creates a new window with 2 list boxes
# Called by Top and Rec buttons
def show_dual_list_dialog(type):
    # Used as a pointer to point to the current list in this dialog
    # so that the create a playlist buttons knows which list to use
    cur_list = []

    # Function to handle the create playlist button
    def create_playlist_btn_click(list):
        spotify.create_playlist([list[i]["id"] for i in range(int(default_num_option.get()))], name="Your {} Tracks".format(type))
        messagebox.showinfo("Success", "Playlist Created!")

    def play_playlist_btn_click(list):
        ids = []
        for t in list:
            id = t["id"]
            ids.append(id)
        spotify.play_songs(ids)


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
            top_tracks = spotify.get_top_tracks(limit=50, time_range=time_frame) if not "tt-" + time_frame in cache else cache["tt-" + time_frame]
            cache["tt-" + time_frame] = top_tracks
            cache["cur"] = cache["tt-" + time_frame]
            disp_listbox(0, top_tracks, True, True, limit)
            # Top Artists stuff
            top_artists = spotify.get_top_artists(limit=50, time_range=time_frame) if not "ta-" + time_frame in cache else cache[
                "ta-" + time_frame]
            cache["ta-" + time_frame] = top_artists
            disp_listbox(1, top_artists, True, False, limit)
        elif type == "Rec":
            # Rec Tracks stuff
            top_tracks = spotify.get_top_tracks(limit=50, time_range=time_frame) if not "tt-" + time_frame in cache else \
            cache["tt-" + time_frame]
            rec_tracks = spotify.get_recommended_tracks(limit=50, track_seeds=[x["id"] for x in top_tracks[:5]]) if not "rt-" + time_frame in cache else cache["rt-" + time_frame]
            cache["rt-" + time_frame] = rec_tracks
            cache["cur"] = cache["rt-" + time_frame]
            disp_listbox(0, rec_tracks, False, True, limit)
            # Rec Artists stuff
            rec_artists = spotify.get_recommended_artists(time_range=time_frame, limit=50) if not "ra-" + time_frame in cache else \
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
