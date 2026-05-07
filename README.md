# Discord Remote Administration Tool

⚠️ **Educational Use Only** ⚠️

This project is intended strictly for educational purposes.

Do **not** use this software on devices without the users explicit permission.

The author does not condone malicious activity of any kind.

This project does not hide from the client on the target machine it is clearly visible.

---

# Overview

This project is a Discord-based remote administration tool written in Python.

It consists of two separate scripts:

| File        | Purpose                                                 |
| ----------- | ------------------------------------------------------- |
| `Client.py` | Runs on the target machine and executes commands   |
| `Server.py` | Runs as the monitoring dashboard inside Discord |

The system uses Discord channels as a communication layer between the server and the connected client machine.

When the client connects:

* A dedicated Discord channel is created for that machine
* The machine status is displayed
* Device information is shown
* Commands can be issued through Discord messages
* Responses are sent back into the channel
---

# Screenshots
<img width="206" height="243" alt="image" src="https://github.com/user-attachments/assets/7196d391-8f13-48fc-9808-8b4440a5c18d" />
<img width="203" height="244" alt="image" src="https://github.com/user-attachments/assets/8a9db6ae-3759-498f-bd0e-1eea004c3a87" />
<img width="379" height="426" alt="image" src="https://github.com/user-attachments/assets/e079a73e-fad2-4cf2-992b-75601f981396" />
<img width="254" height="75" alt="image" src="https://github.com/user-attachments/assets/e967d2c5-4dad-4414-ac36-9c9fc121fe77" />

---

# Commands

| Command       | Function              |
| ------------- | --------------------- |
| `/shell`      | Enable shell mode     |
| `/exit`       | Disable shell mode    |
| `/screenshot` | Capture screenshot    |
| `/webpic`     | Capture webcam image  |
| `/tasklist`   | Show active processes |
| `/popup`      | Display popup         |
| `/opensite`   | Open website          |
| `/geo`        | Get location data     |
| `/backround`  | Change wallpaper      |
| `/screenflip` | Rotate display        |
| `/run`        | Execute uploaded file |
| `/clear`      | Clear channel         |
| `/help`       | Show help menu        |

This project includes many more features which arent listsed here.

---
# Project Structure

```text
project-folder/
│
├── Client.py - ran on target device
├── Server.py - ran on server 
├── requirements.txt 
└── README.md
```

---

# Requirements

* Python 3.10+
* Windows OS (required for several Windows API features)
* A Discord account
* A Discord server you control
* Discord Developer Application + Bot (very easy to make and its free - bot requires administrative permissions)

---

# Python Dependencies

Install the required packages:

```bash
pip install discord.py pillow opencv-python pytz rotatescreen
```

---

# Configuration

Both scripts contain these variables:

```python
MAINCHANNEL = YOUR_CHANNEL_ID
DISCORDTOKEN = "YOUR_BOT_TOKEN"
```

Replace them with:

| Variable       | Description                             |
| -------------- | --------------------------------------- |
| `MAINCHANNEL`  | ID of your main Discord control channel |
| `DISCORDTOKEN` | Your Discord bot token                  |
---

# Running the Project

Run (On the server machine):

```bash
python Server.py
```

The dashboard bot will:

* Clear the main channel
* Create the monitoring table
* Begin scanning for clients

Run (On the client machine):

```bash
python Client.py
```

The client will:

* Request administrator privileges
* Connect to Discord
* Create/find a dedicated machine channel
* Send system information
* Begin listening for commands

---


# Planned Features

* Better authentication
* Encrypted communication
* Cross-platform support - linux, MacOs
* Persistent client storage
* File manager UI
* Live streaming
* Better error handling
* Logging system
* standalone server - non discord dependant

---

# Known Limitations

* Windows only
* Requires administrator privileges for certain operations
* Uses Discord rate-limited APIs
* Not optimized for production use (expect bugs/crashes)

---
