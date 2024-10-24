import os
import sys
import toml
import asyncio
import time
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from urllib.parse import urlparse
from ui import Console
import ctypes
import requests
from telethon import functions
import random

console = Console()

messages_sent = 0
messages_forwarded = 0
cycles_completed = 0
start_time = time.time()

def load_config():
    with open("config.toml", "r") as config_file:
        return toml.load(config_file)   

def load_groups():
    with open("groups.txt", "r") as groups_file:
        return [group.strip() for group in groups_file.readlines()]

def save_session(session_string):
    os.makedirs("sessions", exist_ok=True)
    with open("sessions/session.dat", "w") as session_file:
        session_file.write(session_string)

def load_session():
    try:
        with open("sessions/session.dat", "r") as session_file:
            return session_file.read().strip()
    except FileNotFoundError:
        return ""

def title():
    elapsed_time = int(time.time() - start_time)
    title = f"Telegram Adbot | Messages Sent: {messages_sent} | Messages Forwarded: {messages_forwarded} | Cycles Completed: {cycles_completed} | Time Elapsed: {elapsed_time}s"
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    else:
        sys.stdout.write(f"\33]0;{title}\a")
        sys.stdout.flush()

async def update_terminal_title():
    while True:
        title()
        await asyncio.sleep(1)

def webhook_logs(embed):
    if not bot.config['logging']['discord_logging']:
        return
    webhook_url = bot.config['logging']['webhook_url']
    if not webhook_url:
        console.error("Webhook URL is not set in the configuration file.")
        exit(1)
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "embeds": [embed]
    }
    response = requests.post(webhook_url, json=payload, headers=headers)
    if response.status_code != 204:
        pass

def create_embed(title, description, color, fields=None):
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "fields": [],
        "footer": {
            "text": f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"
        }
    }
    if fields:
        for name, value, inline in fields:
            embed['fields'].append({
                "name": name,
                "value": value,
                "inline": inline
            })
    return embed

def print_settings(config):
    console.info("Configuration Settings:")
    console.info(f"API ID: {config['telegram']['api_id']}")
    console.info(f"API Hash: {config['telegram']['api_hash']}")
    console.info(f"Phone Numbers: {', '.join(config['telegram']['phone_numbers'])}")
    console.info(f"Password: {'Set' if config['telegram']['password'] else 'Not Set'}")
    console.info(f"Joiner: {config['settings']['joiner']}")
    console.info(f"Forward Message: {config['settings']['forward_message']}")
    console.info(f"Forward Message ID: {config['settings']['forward_message_id']}")
    console.info(f"Forward From Group: {config['settings']['forward_from_group']}")
    console.info(f"Send Custom Message: {config['settings']['send_custom_message']}")
    console.info(f"Custom Message Text: {config['settings']['custom_msg_text']}")
    console.info(f"Delay: {config['settings']['delay']}")
    console.info(f"Cycle Delay: {config['settings']['cycle_delay']}")
    console.info(f"Skip Messages: {config['settings']['skip_msg']}")
    console.info(f"Discord Logging: {config['logging']['discord_logging']}")
    console.info(f"Webhook URL: {'Set' if config['logging']['webhook_url'] else 'Not Set'}\n\n")

def send_settings_to_discord(config):
    fields = [
        ("API ID", config['telegram']['api_id'], True),
        ("API Hash", config['telegram']['api_hash'], True),
        ("Phone Numbers", ', '.join(config['telegram']['phone_numbers']), False),
        ("Password", "Set" if config['telegram']['password'] else "Not Set", True),
        ("Joiner", str(config['settings']['joiner']), True),
        ("Forward Message", str(config['settings']['forward_message']), True),
        ("Forward Message ID", config['settings']['forward_message_id'], True),
        ("Forward From Group", config['settings']['forward_from_group'], False),
        ("Send Custom Message", str(config['settings']['send_custom_message']), True),
        ("Custom Message Text", config['settings']['custom_msg_text'], False),
        ("Delay", str(config['settings']['delay']), True),
        ("Cycle Delay", str(config['settings']['cycle_delay']), True),
        ("Skip Messages", str(config['settings']['skip_msg']), True),
        ("Discord Logging", str(config['logging']['discord_logging']), True),
        ("Webhook URL", "Set" if config['logging']['webhook_url'] else "Not Set", True)
    ]
    embed = create_embed(
        title="Configuration Settings",
        description="The following are the current configuration settings of the bot.",
        color=0x3498db,
        fields=fields
    )
    webhook_logs(embed)

class TelegramAdBot:
    def __init__(self):
        self.config = load_config()
        self.groups = load_groups()
        session_string = load_session()
        self.client = TelegramClient(StringSession(session_string), self.config['telegram']['api_id'], self.config['telegram']['api_hash'])
        self.session_exists = bool(session_string)

    async def start(self):
        await self.check_config_settings()
        await self.validate_settings()
        await self.connect()
        await self.join_groups()

    async def check_config_settings(self):
        if self.config['show_settings']['print_settings']:
            print_settings(self.config)
        if self.config['show_settings']['webhook_settings']:
            send_settings_to_discord(self.config)
        if not self.config['telegram']['api_id']:
            console.error("API ID is not set.")
            embed = create_embed("Configuration Error", "API ID is missing in the configuration file.", 0xff0000)
            webhook_logs(embed)
            exit(1)
        if not self.config['telegram']['api_hash']:
            console.error("API Hash is not set.")
            embed = create_embed("Configuration Error", "API Hash is missing in the configuration file.", 0xff0000)
            webhook_logs(embed)
            exit(1)
        if not self.config['telegram']['phone_numbers']:
            console.error("Phone Number is not set.")
            embed = create_embed("Configuration Error", "Phone number is missing in the configuration file.", 0xff0000)
            webhook_logs(embed)
            exit(1)

    async def validate_settings(self):
        if self.config['settings']['send_custom_message'] and self.config['settings']['forward_message']:
            console.error("Both Send Custom Message & Forward Message are enabled. Please enable only one of them.")
            embed = create_embed(
                title="Invalid Settings",
                description="Both Send Custom Message & Forward Message are enabled. Please enable only one of them.",
                color=0xff0000
            )
            webhook_logs(embed)
            exit(1)
        if not self.config['settings']['send_custom_message'] and not self.config['settings']['forward_message']:
            console.error("Both Send Custom Message & Forward Message are disabled. Please enable one of them.")
            embed = create_embed(
                title="Invalid Settings",
                description="Both Send Custom Message & Forward Message are disabled. Please enable one of them.",
                color=0xff0000
            )
            webhook_logs(embed)
            exit(1)
        if self.config['settings']['send_custom_message'] and not self.config['settings']['custom_msg_text']:
            console.error("Custom Message Text is empty. Please provide a message to send.")
            embed = create_embed(
                title="Custom Message Text Empty",
                description="Custom Message Text is empty. Please provide a message to send.",
                color=0xff0000
            )
            webhook_logs(embed)
            exit(1)
        if self.config['settings']['forward_message'] and not self.config['settings']['forward_from_group']:
            console.error("Forward From Link is empty. Please provide a link to forward messages from.")
            embed = create_embed(
                title="Forward From Link Empty",
                description="Forward From Link is empty. Please provide a link to forward messages from.",
                color=0xff0000
            )
            webhook_logs(embed)
            exit(1)
        if self.config['settings']['forward_message'] and not self.config['settings']['forward_message_id']:
            console.error("Forward Message ID is empty. Please provide a message ID to forward.")
            embed = create_embed(
                title="Forward Message ID Empty",
                description="Forward Message ID is empty. Please provide a message ID to forward.",
                color=0xff0000
            )
            webhook_logs(embed)
            exit(1)

    async def connect(self):
        try:
            await self.client.connect()
            if not self.session_exists and not await self.client.is_user_authorized():
                await self.authenticate()
        except errors.AuthKeyDuplicatedError:
            console.error("Session is invalid or used elsewhere. Reconnecting...")
            embed = create_embed(
                title="Session Invalid",
                description="Session is invalid or used elsewhere. Reconnecting...",
                color=0xff0000
            )
            webhook_logs(embed)
            self.client = TelegramClient(StringSession(), self.config['telegram']['api_id'], self.config['telegram']['api_hash'])
            await self.client.connect()
            await self.authenticate()
        phone_number = self.config['telegram']['phone_numbers'][0]
        masked_number = '*' * (len(phone_number) - 4) + phone_number[-4:]
        console.info(f"Connecting to Telegram ({masked_number})")
        embed = create_embed(
            title="Connecting to Telegram",
            description=f"Connecting to Telegram ({masked_number})",
            color=0xffff00,
            fields=[("Phone Number", masked_number, False)]
        )
        self.user = await self.client.get_me()
        console.info(f"Successfully signed into account {self.user.username if self.user else 'N/A'}")
        embed = create_embed(
            title="Connected to Telegram",
            description=f"Successfully signed into account {self.user.username if self.user else 'N/A'}",
            color=0x00ff00,
            fields=[("Phone Number", masked_number, False)]
        )
        webhook_logs(embed)

    async def authenticate(self):
        phone_number = self.config['telegram']['phone_numbers'][0]
        masked_number = '*' * (len(phone_number) - 4) + phone_number[-4:]
        try:
            await self.client.send_code_request(phone_number)
            console.info(f"Sent verification code to {masked_number}")
            embed = create_embed(
                title="Sent Verification Code",
                description=f"Sent verification code to {masked_number}",
                color=0xffff00,
                fields=[("Phone Number", masked_number, False)]
            )
            verification_code = input(f"{console.colors['lightblack']}{console.timestamp()} » {console.colors['lightblue']}INFO    {console.colors['lightblack']}• {console.colors['white']}Enter the verification code: {console.colors['reset']}")
            await self.client.sign_in(phone_number, verification_code)
            embed = create_embed(
                title="Verification Code Entered",
                description="Verification code entered. Signing in...",
                color=0xffff00,
                fields=[("Phone Number", masked_number, False)]
            )
            webhook_logs(embed)
            save_session(self.client.session.save())
        except errors.PhoneNumberBannedError:
            console.error("Your phone number has been banned from Telegram")
            embed = create_embed(
                title="Phone Number Banned",
                description="Your phone number has been banned from Telegram",
                color=0xff0000,
                fields=[("Phone Number", masked_number, False)]
            )
            webhook_logs(embed)
            exit(1)
        except errors.SessionPasswordNeededError:
            password = self.config['telegram']['password']
            await self.client.sign_in(password=password)
            console.info("Two-step verification is enabled. Password entered.")
            embed = create_embed(
                title="Two-Step Verification",
                description="Two-step verification is enabled. Password entered.",
                color=0xffff00,
                fields=[("Phone Number", masked_number, False)]
            )
            webhook_logs(embed)
            save_session(self.client.session.save())

    async def check_config_settings(self):
        if self.config['show_settings']['print_settings']:
            print_settings(self.config)
        if self.config['show_settings']['webhook_settings']:
            send_settings_to_discord(self.config)

    async def join_groups(self):
        if not self.config['settings']['joiner']:
            return
        for group_url in self.groups:
            try:
                parsed_url = urlparse(group_url)
                path_parts = parsed_url.path.strip('/').split('/')
                group_name = path_parts[0]
                try:
                    await self.client(JoinChannelRequest(group_name))
                    console.success(f"Joined group {group_name}")
                    embed = create_embed(
                        title="Joined Group",
                        description=f"Successfully joined group {group_name}",
                        color=0x00ff00,
                        fields=[("Group Name", group_name, False)]
                    )
                    webhook_logs(embed)
                    await asyncio.sleep(2)
                except errors.ChannelInvalidError:
                    console.error(f"Invalid group: {group_name}")
                    embed = create_embed(
                        title="Failed to Join Group",
                        description=f"Invalid group: {group_name}",
                        color=0xff0000,
                        fields=[("Group Name", group_name, False)]
                    )
                    webhook_logs(embed)
                except errors.ChannelPrivateError:
                    console.error(f"Group is private: {group_name}")
                    embed = create_embed(
                        title="Failed to Join Group",
                        description=f"Group is private: {group_name}",
                        color=0xff0000,
                        fields=[("Group Name", group_name, False)]
                    )
                    webhook_logs(embed)
                except errors.UserBannedInChannelError:
                    console.error(f"Banned from group: {group_name}")
                    embed = create_embed(
                        title="Failed to Join Group",
                        description=f"Banned from group: {group_name}",
                        color=0xff0000,
                        fields=[("Group Name", group_name, False)]
                    )
                    webhook_logs(embed)
                except errors.FloodWaitError as e:
                    console.error(f"Rate-limited. Sleeping for {e.seconds} seconds")
                    await asyncio.sleep(e.seconds)
                    embed = create_embed(
                        title="Rate Limited",
                        description=f"Rate-limited. Sleeping for {e.seconds} seconds",
                        color=0xff0000,
                        fields=[("Group Name", group_name, False)]
                    )
                    webhook_logs(embed)
                except errors.RPCError as e:
                    console.error(f"Failed to join group {group_name}: {str(e)}")
                    embed = create_embed(
                        title="Failed to Join Group",
                        description=f"Failed to join group {group_name}: {str(e)}",
                        color=0xff0000,
                        fields=[("Group Name", group_name, False)]
                    )
                    webhook_logs(embed)
            except Exception as e:
                console.error(f"Failed to process group URL {group_url}: {str(e)}")
                embed = create_embed(
                    title="Failed to Process Group",
                    description=f"Failed to process group URL {group_url}: {str(e)}",
                    color=0xff0000,
                    fields=[("Group URL", group_url, False)]
                )
                webhook_logs(embed)

    async def get_last_message_in_group(self, group):
        try:
            last_message = await self.client.get_messages(group, limit=1)
            return last_message[0] if last_message else None
        except Exception as e:
            return None

    async def send_custom_message(self, message):
        global messages_sent
        if not self.client.is_connected():
            await self.client.connect()
        for url in self.groups:
            try:
                parsed_url = urlparse(url)
                path_parts = parsed_url.path.strip('/').split('/')
                group_name = path_parts[0]
                to_peer = await self.client.get_input_entity(group_name)
                if self.config['settings']['skip_msg']:
                    last_message = await self.get_last_message_in_group(to_peer)
                    if last_message and last_message.sender_id == self.user.id:
                        console.info(f"Skipping {group_name} as the last message is already from the bot.")
                        embed = create_embed(
                            title="Skipped Group",
                            description=f"Skipping {group_name} as the last message is already from the bot.",
                            color=0xffff00,
                            fields=[("Group Name", group_name, False)]
                        )
                        continue
                if len(path_parts) == 2:
                    forum_id = int(path_parts[1])
                    await self.client.send_message(to_peer, message, reply_to=forum_id)
                else:
                    await self.client.send_message(to_peer, message)
                messages_sent += 1
                console.success(f"Message sent to {group_name}")
                await asyncio.sleep(self.config['settings']['delay'])
                embed = create_embed(
                    title="Message Sent",
                    description=f"Message sent to {group_name}",
                    color=0x00ff00,
                    fields=[("Group Name", group_name, False)]
                )
                webhook_logs(embed)
            except errors.SlowModeWaitError as e:
                console.warning(f"Skipping group {url} due to cooldown of {e.seconds} seconds.")
                embed = create_embed(
                    title="Slow Mode",
                    description=f"Skipping group {url} due to cooldown of {e.seconds} seconds.",
                    color=0xffff00,
                    fields=[("Group Name", group_name, False)]
                )
                webhook_logs(embed)
            except errors.FloodWaitError as e:
                console.warning(f"Skipping group {url} due to cooldown of {e.seconds} seconds.")
                embed = create_embed(
                    title="Flood Wait",
                    description=f"Skipping group {url} due to cooldown of {e.seconds} seconds.",
                    color=0xffff00,
                    fields=[("Group Name", group_name, False)]
                )
                webhook_logs(embed)
            except ValueError:
                console.error(f"Invalid group identifier in URL: {url}")
                embed = create_embed(
                    title="Invalid Group",
                    description=f"Invalid group identifier in URL: {url}",
                    color=0xff0000,
                    fields=[("Group URL", url, False)]
                )
                webhook_logs(embed)
            except Exception as e:
                console.error(f"Failed to send message to {url}: {str(e)}")
                embed = create_embed(
                    title="Failed to Send Message",
                    description=f"Failed to send message to {url}: {str(e)}",
                    color=0xff0000,
                    fields=[("Group URL", url, False)]
                )
                webhook_logs(embed)

    async def forward_message(self):
        global messages_forwarded
        if not self.client.is_connected():
            await self.client.connect()
        try:
            forward_from_link = self.config['settings']['forward_from_group']
            forward_message_id = self.config['settings']['forward_message_id']
            message = await self.client.get_messages(forward_from_link, ids=int(forward_message_id))
            if not message:
                console.error(f"Could not find message with ID {forward_message_id} in {forward_from_link}")
                return
        except Exception as e:
            console.error(f"Failed to get message to forward: {str(e)}")
            return
        for group_url in self.groups:
            try:
                parsed_url = urlparse(group_url)
                path_parts = parsed_url.path.strip('/').split('/')
                group_name = path_parts[0]
                topic_id = None
                if len(path_parts) > 1:
                    try:
                        topic_id = int(path_parts[1])
                    except ValueError:
                        console.error(f"Invalid topic ID in URL: {group_url}")
                        continue
                target_group_entity = await self.client.get_input_entity(group_name)
                if self.config['settings']['skip_msg']:
                    last_message = await self.get_last_message_in_group(target_group_entity)
                    if last_message and last_message.sender_id == self.user.id:
                        console.info(f"Skipping {group_name} as the last message is already from the bot.")
                        embed = create_embed(
                            title="Skipped Group",
                            description=f"Skipping {group_name} as the last message is already from the bot.",
                            color=0xffff00,
                            fields=[("Group Name", group_name, False)]
                        )
                        webhook_logs(embed)
                        continue
                forwarded = await self.client(functions.messages.ForwardMessagesRequest(
                    from_peer=await self.client.get_input_entity(forward_from_link),
                    id=[message.id],
                    to_peer=target_group_entity,
                    top_msg_id=topic_id if topic_id else None,
                    random_id=[random.randint(0, 2147483647)],
                    drop_author=False,
                    drop_media_captions=False
                ))
                messages_forwarded += 1
                console.success(f"Message forwarded to {group_name}" + (f" topic {topic_id}" if topic_id else ""))
                await asyncio.sleep(self.config['settings']['delay'])
                embed = create_embed(
                    title="Message Forwarded",
                    description=f"Message forwarded to {group_name}" + (f" topic {topic_id}" if topic_id else ""),
                    color=0x00ff00,
                    fields=[("Group Name", group_name, False)]
                )
                webhook_logs(embed)
            except errors.SlowModeWaitError as e:
                console.warning(f"Skipping group {group_name} due to cooldown of {e.seconds} seconds.")
                embed = create_embed(
                    title="Slow Mode",
                    description=f"Skipping group {group_name} due to cooldown of {e.seconds} seconds.",
                    color=0xffff00,
                    fields=[("Group Name", group_name, False)]
                )
                webhook_logs(embed)
            except errors.FloodWaitError as e:
                console.warning(f"Skipping group {group_name} due to cooldown of {e.seconds} seconds.")
                embed = create_embed(
                    title="Flood Wait",
                    description=f"Skipping group {group_name} due to cooldown of {e.seconds} seconds.",
                    color=0xffff00,
                    fields=[("Group Name", group_name, False)]
                )
                webhook_logs(embed)
            except errors.TopicDeletedError:
                console.error(f"Topic is deleted in group {group_name}")
                embed = create_embed(
                    title="Topic Deleted",
                    description=f"Cannot send message to deleted topic in group {group_name}",
                    color=0xff0000,
                    fields=[("Group Name", group_name, False)]
                )
                webhook_logs(embed)
            except ValueError as e:
                console.error(f"Invalid group identifier in URL: {group_url}")
                embed = create_embed(
                    title="Invalid Group",
                    description=f"Invalid group identifier in URL: {group_url}",
                    color=0xff0000,
                    fields=[("Group URL", group_url, False)]
                )
                webhook_logs(embed)
            except Exception as e:
                console.error(f"Failed to forward message to {group_name}: {str(e)}")
                embed = create_embed(
                    title="Failed to Forward Message",
                    description=f"Failed to forward message to {group_name}: {str(e)}",
                    color=0xff0000,
                    fields=[("Group Name", group_name, False)]
                )
                webhook_logs(embed)

    async def handle_messages(self):
        global cycles_completed
        try:
            if self.config['settings']['forward_message']:
                await self.forward_message()
            elif self.config['settings']['send_custom_message']:
                await self.send_custom_message(self.config['settings']['custom_msg_text'])
            cycles_completed += 1
        except errors.AuthKeyDuplicatedError:
            console.error("Session is invalid or used elsewhere. Reconnecting...")
            embed = create_embed(
                title="Session Invalid",
                description="Session is invalid or used elsewhere. Reconnecting...",
                color=0xff0000
            )
            webhook_logs(embed)
            await self.connect()
            await self.handle_messages()    

    async def run(self):
        await self.start()
        while True:
            await self.handle_messages()
            console.info("Completed all tasks. Sleeping...")
            embed = create_embed(
                title="Cycle Completed",
                description="Completed all tasks. Sleeping...",
                color=0x00ff00
            )
            webhook_logs(embed)
            await asyncio.sleep(self.config['settings']['cycle_delay'])

if __name__ == "__main__":
    bot = TelegramAdBot()
    loop = asyncio.get_event_loop()
    loop.create_task(update_terminal_title())
    loop.run_until_complete(bot.run())
