import subprocess


def send_imessage(contact: str, message: str) -> str:
    """Send an iMessage. contact can be a name or phone number."""
    safe_msg = message.replace('\\', '\\\\').replace('"', '\\"')
    safe_contact = contact.replace('"', '\\"')

    script = f'''
    tell application "Messages"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant "{safe_contact}" of targetService
        send "{safe_msg}" to targetBuddy
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback: try sending to phone number directly
        script2 = f'''
        tell application "Messages"
            send "{safe_msg}" to buddy "{safe_contact}" of (1st service whose service type = iMessage)
        end tell
        '''
        result2 = subprocess.run(["osascript", "-e", script2], capture_output=True, text=True)
        if result2.returncode != 0:
            return f"Couldn't send iMessage to {contact}: {result2.stderr.strip()}"
    return f"iMessage sent to {contact}."


def send_sms(phone: str, message: str) -> str:
    """Send an SMS via Messages app."""
    safe_msg = message.replace('\\', '\\\\').replace('"', '\\"')

    script = f'''
    tell application "Messages"
        set smsService to 1st service whose service type = SMS
        send "{safe_msg}" to buddy "{phone}" of smsService
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Couldn't send SMS to {phone}: {result.stderr.strip()}"
    return f"SMS sent to {phone}."
