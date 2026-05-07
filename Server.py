import discord
import asyncio
import datetime
from discord import Embed
from discord.ui import Button, View

# Settings
MAINCHANNEL = YOUR_CHANNEL_ID
DISCORDTOKEN = "YOUR_BOT_TOKEN"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

server = discord.Client(intents=intents)

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

# Global variable to store the table message
table_message = None
clients_info = {}  # Dictionary to store client info: {channel_id: {name, ip, time, country}}

class DeleteChannelView(View):
    """View with delete button for client channels"""
    def __init__(self, channel_id):
        super().__init__()
        self.channel_id = channel_id
    
    @discord.ui.button(label="Delete Channel", style=discord.ButtonStyle.red)
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        try:
            channel = interaction.client.get_channel(self.channel_id)
            # Acknowledge immediately so interaction doesn't time out
            if channel:
                await channel.delete()
                print(f"[DEBUG] Channel {self.channel_id} deleted via button")
                # Remove from clients_info
                if self.channel_id in clients_info:
                    del clients_info[self.channel_id]
                # Refresh the table message if available
                try:
                    if table_message and table_message.channel:
                        await update_table(table_message.channel)
                except Exception as e:
                    print(f"[DEBUG] Error updating table after delete: {e}")
            else:
                # Channel not found
                await interaction.followup.send("Channel not found", ephemeral=True)
        except Exception as e:
            print(f"[DEBUG] Error deleting channel: {e}")
            try:
                await interaction.followup.send(f"Error: {e}", ephemeral=True)
            except Exception:
                pass

@server.event
async def on_ready():
    global table_message
    print(f"[DEBUG] Server connected as {server.user}")
    
    main_channel = server.get_channel(MAINCHANNEL)
    guild = main_channel.guild
    print(f"[DEBUG] Guild: {guild.name}")
    print(f"[DEBUG] Main Channel: {main_channel.name}")
    
    # Clear main channel on connect
    print(f"[DEBUG] Clearing main channel...")
    async for message in main_channel.history(limit=None):
        await message.delete()
    print(f"[DEBUG] Main channel cleared")
    
    # Send initial empty table
    print(f"[DEBUG] Creating initial table...")
    table_embed = Embed(title='Connected Clients', description='Searching for clients...', color=0x0000ff)
    table_embed.add_field(name='PC Name', value='Searching...', inline=False)
    table_message = await main_channel.send(embed=table_embed)
    
    # Start concurrent tasks for discovery, activity checking, and table updates
    print(f"[DEBUG] Starting concurrent monitoring tasks...")
    server.loop.create_task(discover_new_clients(guild))
    server.loop.create_task(check_client_activity())
    server.loop.create_task(update_table_loop(main_channel))

async def discover_new_clients(guild):
    """Continuously scan for new client channels (slower, every 5 seconds)"""
    SCAN_INTERVAL = 5  # seconds between discovery scans
    
    while True:
        try:
            await asyncio.sleep(SCAN_INTERVAL)
            print(f"[DEBUG] Scanning for new client channels...")
            
            # List all channels
            for channel in guild.text_channels:
                # Skip the main channel
                if channel.id == MAINCHANNEL:
                    continue
                
                # Skip if we already know about this channel
                if channel.id in clients_info:
                    continue
                
                print(f"[DEBUG] Found new channel: {channel.name}")
                
                # Look for the status message (Client Connected embed) in the channel
                try:
                    async for message in channel.history(limit=20):  # Check recent messages
                        if message.author == server.user and message.embeds:
                            embed = message.embeds[0]
                            # Title contains 'Client Connected'
                            if embed.title and 'Client Connected' in embed.title:
                                print(f"[DEBUG] Found status message in new channel {channel.name}")
                                
                                # Extract info from the embed
                                info = {}
                                for field in embed.fields:
                                    if field.name == 'IP':
                                        info['ip'] = field.value
                                    elif field.name == 'Name':
                                        info['name'] = field.value
                                    elif field.name == 'Time':
                                        info['time'] = field.value
                                    elif field.name == 'Country':
                                        info['country'] = field.value

                                if 'ip' in info and 'name' in info:
                                    clients_info[channel.id] = {
                                        'name': info.get('name', 'Unknown'),
                                        'ip': info.get('ip', 'Unknown'),
                                        'time': info.get('time', 'Unknown'),
                                        'country': info.get('country', 'Unknown'),
                                        'channel': channel,
                                        'last_seen': None,
                                        'active': False,
                                        'age': 0,
                                        'previous_title': embed.title,
                                        'message_id': message.id
                                    }
                                    print(f"[DEBUG] New client added: {info.get('name', 'Unknown')}")
                                break
                except Exception as e:
                    print(f"[DEBUG] Error checking new channel {channel.name}: {e}")
                    
        except Exception as e:
            print(f"[DEBUG] Error in discovery task: {e}")

async def check_client_activity():
    """Continuously check activity on known clients by monitoring embed changes"""
    ACTIVITY_CHECK_INTERVAL = 0.5  # seconds between activity checks
    INACTIVE_THRESHOLD = 5  # seconds without embed changes => inactive
    
    while True:
        try:
            await asyncio.sleep(ACTIVITY_CHECK_INTERVAL)
            
            # Check activity for each known client
            for channel_id, info in list(clients_info.items()):
                channel = info.get('channel')
                if not channel:
                    continue
                
                try:
                    # Try to fetch the specific message if we have the ID
                    message_id = info.get('message_id')
                    if message_id:
                        try:
                            message = await channel.fetch_message(message_id)
                        except:
                            # Message not found, search recent history
                            message = None
                            async for msg in channel.history(limit=20):
                                if msg.author == server.user and msg.embeds:
                                    embed = msg.embeds[0]
                                    if embed.title and 'Client Connected' in embed.title:
                                        message = msg
                                        clients_info[channel_id]['message_id'] = msg.id
                                        break
                    else:
                        # No message ID stored, search history
                        message = None
                        async for msg in channel.history(limit=20):
                            if msg.author == server.user and msg.embeds:
                                embed = msg.embeds[0]
                                if embed.title and 'Client Connected' in embed.title:
                                    message = msg
                                    clients_info[channel_id]['message_id'] = msg.id
                                    break
                    
                    if message and message.embeds:
                        embed = message.embeds[0]
                        current_title = embed.title
                        previous_title = info.get('previous_title', '')
                        
                        # Check if the embed title changed (animation is running)
                        if current_title != previous_title:
                            # Title changed = client is active
                            clients_info[channel_id]['active'] = True
                            clients_info[channel_id]['last_seen'] = datetime.datetime.now(datetime.timezone.utc)
                            clients_info[channel_id]['age'] = 0
                            print(f"[DEBUG] {info['name']} is ACTIVE - embed updated")
                        else:
                            # Title didn't change, check how long it's been
                            last_seen = info.get('last_seen')
                            if last_seen:
                                now_dt = datetime.datetime.now(datetime.timezone.utc)
                                age = (now_dt - last_seen).total_seconds()
                                clients_info[channel_id]['age'] = int(age)
                                active = age <= INACTIVE_THRESHOLD
                                clients_info[channel_id]['active'] = active
                                print(f"[DEBUG] {info['name']} - age={int(age)}s, active={active}")
                            else:
                                # First check
                                clients_info[channel_id]['last_seen'] = datetime.datetime.now(datetime.timezone.utc)
                                clients_info[channel_id]['active'] = True
                                clients_info[channel_id]['age'] = 0
                        
                        # Update previous title for next comparison
                        clients_info[channel_id]['previous_title'] = current_title
                        
                except Exception as e:
                    print(f"[DEBUG] Error checking activity for channel {channel_id}: {e}")
                    
        except Exception as e:
            print(f"[DEBUG] Error in activity check task: {e}")

async def update_table_loop(main_channel):
    """Continuously update the table (very fast, every 0.5 seconds)"""
    UPDATE_INTERVAL = 0.5  # seconds between table updates
    
    while True:
        try:
            await asyncio.sleep(UPDATE_INTERVAL)
            await update_table(main_channel)
        except Exception as e:
            print(f"[DEBUG] Error in update table task: {e}")

async def update_table(main_channel):
    """Update the client table in the main channel"""
    global table_message
    
    def format_age(age_seconds):
        """Format age in seconds to human-readable format"""
        if age_seconds < 20:
            return "just now"
        
        hours = int(age_seconds // 3600)
        minutes = int((age_seconds % 3600) // 60)
        seconds = int(age_seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    try:
        if not clients_info:
            # No clients connected
            table_embed = Embed(title='Connected Clients', description='No clients connected', color=0xff0000)
            await table_message.edit(embed=table_embed, view=None)
        else:
            # Build table with all clients, include active/inactive status
            table_embed = Embed(title='Connected Clients', description=f'{len(clients_info)} client(s) discovered', color=0x00ff00)

            for channel_id, info in clients_info.items():
                status = '🟢 Active' if info.get('active') else '🔴 Inactive'
                age = info.get('age', 0)
                age_formatted = format_age(age)
                
                # Get country with flag emoji
                country_info = info.get('country', 'Unknown')
                # Extract country name from the value (might include flag)
                if country_info and country_info != 'Unknown':
                    # The country value is already in format "🇺🇸 United States", so use it as-is
                    country_display = country_info
                else:
                    country_display = 'Unknown'
                
                client_text = (
                    f"**Status:** {status}\n"
                    f"**IP:** {info['ip']}\n"
                    f"**Country:** {country_display}\n"
                    f"**Last Seen:** {age_formatted}\n"
                    f"**Channel:** <#{channel_id}>"
                )
                table_embed.add_field(name=info['name'], value=client_text, inline=False)

            # Create view with delete buttons for each client (unique callbacks)
            view = View()
            for channel_id, info in clients_info.items():
                # create a button with a unique callback bound to this channel id
                btn = Button(label=f"Delete {info['name']}", style=discord.ButtonStyle.red)

                def make_callback(ch_id):
                    async def callback(interaction: discord.Interaction):
                        try:
                            # Respond quickly to avoid interaction timeout
                            channel = interaction.client.get_channel(ch_id)
                            if channel:
                                await channel.delete()
                                print(f"[DEBUG] Channel {ch_id} deleted via button")
                                # Remove from clients_info if present
                                clients_info.pop(ch_id, None)
                                # Refresh the table
                                try:
                                    if table_message and table_message.channel:
                                        await update_table(table_message.channel)
                                except Exception as e:
                                    print(f"[DEBUG] Error updating table after delete: {e}")
                            else:
                                await interaction.followup.send("Channel not found", ephemeral=True)
                        except Exception as e:
                            print(f"[DEBUG] Error deleting channel via button: {e}")
                            try:
                                await interaction.followup.send(f"Error: {e}", ephemeral=True)
                            except Exception:
                                pass
                    return callback

                btn.callback = make_callback(channel_id)
                view.add_item(btn)

            await table_message.edit(embed=table_embed, view=view)
            print(f"[DEBUG] Table updated with {len(clients_info)} client(s)")
            
    except Exception as e:
        print(f"[DEBUG] Error updating table: {e}")

server.run(DISCORDTOKEN)

# if your reading this yes i did use ai to anotate and try fix bugs but id say 90% is written by me myself and I. (: 