# HackTheBox machine setup

One command turns a fresh Ubuntu 22.04 or 24.04 machine into an attack box with an SSH server. Allow about 30 GB of free disk.

## Set up
1. Add your public SSH key to `authorized_keys`, then commit and push.
2. On the Ubuntu machine:

```bash
sudo apt-get update && sudo apt-get install -y git openssh-server
git clone https://github.com/ironfisto/machines.git
cd machines/hackthebox
sudo ./bootstrap.sh
```

The last task of the run lists any tools that failed. Re-running only retries what's missing.

Password login turns off only if a key is present. If you add a key later, run `sudo ./bootstrap.sh --tags ssh`.

## Daily use

```bash
htb-vpn lab.ovpn        # connect (keep .ovpn files out of git)
htb-vpn status
htb-box Lame 10.10.10.3 # create ~/htb/boxes/Lame
htb-listen 4444         # let targets reach this port over the VPN
htb-listen close 4444
```

## Add a tool
Add a line to `ansible/vars/tools.yml`, then run `sudo ./bootstrap.sh --tags tools`.

## Where things are
| Path | Contents |
|---|---|
| `/usr/share/seclists` | SecLists |
| `/usr/share/wordlists/rockyou.txt` | rockyou |
| `/opt/tools/linux` | Binaries to upload to Linux targets |
| `/opt/tools/windows` | Binaries to upload to Windows targets |
| `/opt/tools` | Responder, PayloadsAllTheThings, nishang, PowerSploit |

## Firewall
- SSH is allowed only on the main network interface, not over the VPN.
- All other inbound traffic is blocked, including from the VPN, until you open a port with `htb-listen`.
