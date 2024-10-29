import os
import asyncio
import random
from pyrogram import Client
from pyrogram.errors import FloodWait, UserAlreadyParticipant, UsernameInvalid, PeerIdInvalid

API_ID = ""
API_HASH = ""
SESSIONS_FOLDER = "sessions"
REFERRAL_LINK = ""
PROXIES_FILE = "proxies.txt"
DELAY_BETWEEN_TASKS = (1, 3)
DELAY_BETWEEN_ACTIONS = (2, 5)

def load_sessions():
    try:
        if not os.path.exists(SESSIONS_FOLDER):
            os.makedirs(SESSIONS_FOLDER)
            print(f"Created sessions folder: {SESSIONS_FOLDER}")
            return []

        sessions = []
        for file in os.listdir(SESSIONS_FOLDER):
            if file.endswith('.session'):
                sessions.append(file[:-8])
        return sessions
    except Exception as e:
        print(f"Error loading sessions: {str(e)}")
        return []

def load_proxies():
    try:
        with open(PROXIES_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: {PROXIES_FILE} not found!")
        return []
    except Exception as e:
        print(f"Error reading proxies file: {str(e)}")
        return []

def parse_proxy(proxy_string):
    try:
        if '@' in proxy_string:
            auth, proxy = proxy_string.split('@')
            username, password = auth.split(':')
            host, port = proxy.split(':')
        else:
            username = password = None
            host, port = proxy_string.split(':')

        return {
            "scheme": "socks5",
            "hostname": host,
            "port": int(port),
            "username": username,
            "password": password
        }
    except Exception as e:
        print(f"Error parsing proxy {proxy_string}: {str(e)}")
        return None

def extract_bot_username(link):
    parts = link.split('/')
    return parts[0] if parts else None

async def start_bot_with_retries(app, bot_username, start_parameter, max_retries=3):
    for attempt in range(max_retries):
        try:
            await app.send_message(bot_username, f"/start {start_parameter}")
            print(f"Successfully started bot: {bot_username}")
            return True
        except FloodWait as e:
            print(f"FloodWait: {e.x} seconds")
            await asyncio.sleep(e.x)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            await asyncio.sleep(2)
    return False

async def join_mini_app(session_name, proxy=None):
    try:
        client_config = {
            "name": session_name,
            "api_id": API_ID,
            "api_hash": API_HASH,
            "workdir": SESSIONS_FOLDER
        }
        
        if proxy:
            client_config["proxy"] = proxy

        async with Client(**client_config) as app:
            try:
                me = await app.get_me()
                print(f"Logged in as {me.first_name} ({me.id})")

                bot_username = extract_bot_username(REFERRAL_LINK)
                start_parameter = REFERRAL_LINK.split('?startapp=')[1] if '?startapp=' in REFERRAL_LINK else ''
                
                print(f"Trying to start bot: {bot_username} with parameter: {start_parameter}")

                success = await start_bot_with_retries(app, bot_username, start_parameter)
                if success:
                    print(f"Successfully started bot with account: {me.first_name}")
                else:
                    print(f"Failed to start bot after multiple attempts with account: {me.first_name}")

                delay = random.uniform(*DELAY_BETWEEN_ACTIONS)
                await asyncio.sleep(delay)

            except Exception as e:
                print(f"Error performing actions: {str(e)}")
    except Exception as e:
        print(f"Error initializing session: {str(e)}")

async def main():
    sessions = load_sessions()
    if not sessions:
        print("No session files found!")
        return
    
    proxies = load_proxies()
    if not proxies:
        print("No proxies found, running without proxies")

    print(f"Found {len(sessions)} sessions")
    tasks = []
    
    for i, session_name in enumerate(sessions):
        proxy = None
        if proxies:
            proxy_string = proxies[i % len(proxies)]
            proxy = parse_proxy(proxy_string)
        
        task = asyncio.create_task(join_mini_app(session_name, proxy))
        tasks.append(task)
        
        delay = random.uniform(*DELAY_BETWEEN_TASKS)
        await asyncio.sleep(delay)
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("Starting mini app joiner...")
    print(f"Using sessions from: {SESSIONS_FOLDER}")
    print(f"Using proxies from: {PROXIES_FILE}")
    print(f"Target: {REFERRAL_LINK}")
    
    asyncio.run(main())