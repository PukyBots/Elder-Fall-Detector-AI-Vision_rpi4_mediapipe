import subprocess

def connect_wifi(ssid, password):
    try:
        cmd = [
            "nmcli",
            "dev",
            "wifi",
            "connect",
            ssid,
            "password",
            password
        ]

        subprocess.run(cmd, check=True)
        return "connected"

    except Exception as e:
        return str(e)