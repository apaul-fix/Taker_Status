import os #this is to get icons Remember later pls
import sys #this too i guess
import requests #resinstalled was missing
import tkinter as tk #Ez UI
from tkinter import ttk, messagebox #widgets for UI tkinter thingy idk
from datetime import datetime #time thing for later

def resource_path(relative_path):
    """Get absolute path to resource, works for development and PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

LOGIN_URL = "https://demo.centroidsol.com/v2/api/login"
TAKERS_URL = "https://demo.centroidsol.com/v1/api/takers"
REFRESH_MS = 60000

session_data = {
    "token": None,
    "api_username": None,
    "client_code": None,
}


def login(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(LOGIN_URL, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def get_takers(token, username, client_code):
    headers = {
        "Authorization": f"Bearer {token}",
        "x-forward-client": client_code,
        "x-forward-user": username,
        "Accept": "application/json",
    }

    cookies = {"jwt": token}

    response = requests.get(
        TAKERS_URL,
        headers=headers,
        cookies=cookies,
        timeout=15,
    )

    response.raise_for_status()
    return response.json()


def authenticate():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if not username or not password:
        messagebox.showwarning("Missing details", "Please enter username and password.")
        return False

    login_data = login(username, password)

    session_data["token"] = login_data["token"]
    session_data["api_username"] = login_data["user"]["username"]
    session_data["client_code"] = login_data["user"]["client_code"]

    return True


def load_takers(show_errors=True):
    try:
        if not session_data["token"]:
            if not authenticate():
                return

        takers = get_takers(
            session_data["token"],
            session_data["api_username"],
            session_data["client_code"],
        )

        for row in table.get_children():
            table.delete(row)

        connected_count = 0
        disconnected_count = 0

        for taker in takers:
            name = taker.get("name", "Unknown")
            state_value = taker.get("state", 0)

            if state_value == 1:
                state_text = "🟢 Connected"
                row_tag = "connected"
                connected_count += 1
            else:
                state_text = "🔴 Disconnected"
                row_tag = "disconnected"
                disconnected_count += 1

            table.insert("", tk.END, values=(name, state_text), tags=(row_tag,))

        now = datetime.now().strftime("%H:%M:%S")

        summary_label.config(
            text=f"Connected: {connected_count}    Disconnected: {disconnected_count}"
        )

        status_label.config(
            text=f"Last updated: {now}    |    Total takers: {len(takers)}"
        )

    except requests.exceptions.HTTPError as error:
        session_data["token"] = None
        status_label.config(text="Login/session failed. Please refresh again.")
        if show_errors:
            messagebox.showerror("HTTP Error", f"{error}\n\n{error.response.text}")

    except Exception as error:
        status_label.config(text="Failed to refresh taker status.")
        if show_errors:
            messagebox.showerror("Error", str(error))


def manual_refresh():
    session_data["token"] = None
    load_takers(show_errors=True)


def auto_refresh():
    if session_data["token"]:
        load_takers(show_errors=False)

    app.after(REFRESH_MS, auto_refresh)


app = tk.Tk()
app.title("Taker Status Monitor v1_3")
app.iconbitmap(resource_path("assets/CS360.ico"))
app.geometry("650x520")

style = ttk.Style()
style.configure("Treeview", rowheight=28)
style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

login_frame = ttk.Frame(app, padding=10)
login_frame.pack(fill="x")

ttk.Label(login_frame, text="Username").grid(row=0, column=0, sticky="w")
username_entry = ttk.Entry(login_frame, width=45)
username_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(login_frame, text="Password").grid(row=1, column=0, sticky="w")
password_entry = ttk.Entry(login_frame, width=45, show="*")
password_entry.grid(row=1, column=1, padx=5, pady=5)

refresh_button = ttk.Button(login_frame, text="Refresh Now", command=manual_refresh)
refresh_button.grid(row=2, column=1, sticky="e", pady=10)

summary_label = ttk.Label(
    app,
    text="Connected: 0    Disconnected: 0",
    font=("Segoe UI", 11, "bold"),
    padding=10,
)
summary_label.pack(fill="x")

table = ttk.Treeview(app, columns=("name", "state"), show="headings")
table.heading("name", text="Taker Name")
table.heading("state", text="State")

table.column("name", width=430)
table.column("state", width=170)

table.tag_configure("connected", foreground="green")
table.tag_configure("disconnected", foreground="red")

table.pack(fill="both", expand=True, padx=10, pady=10)

status_label = ttk.Label(app, text="Not loaded", padding=10)
status_label.pack(fill="x")

app.after(REFRESH_MS, auto_refresh)
app.mainloop()