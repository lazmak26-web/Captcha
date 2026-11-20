# Leakers$ CAPTCHA — Professional Discord Verification Bot

**Leakers$ CAPTCHA** is an enterprise-grade visual verification bot for Discord built with **Python 3.11+**, **discord.py 2.x**, **Pillow**, and **SQLite**. It offers sophisticated procedural distortion engines, in-Discord modal verification, and automated role provisioning.

---

## ✨ Features

- **13 Advanced Visual CAPTCHA Engines**:
  - `Collage`: Layered, multi-angle paper card cutouts with geometric backdrops.
  - `Snow`: Crystalline snowflakes, blizzard particles, and icy cool tones.
  - `Corrosion`: Acid pit erosion, rust dripping, and edge decay.
  - `SpiderWeb`: Interwoven radial filaments and dewdrop nodes.
  - `CrossShadow`: Opposing multi-directional drop shadows.
  - `CrossShadow2`: Tri-layer chromatic aberration cross-projections.
  - `Cut`: Razor-sliced horizontal sections with lateral displacement.
  - `Darts`: Projectile dart arrows, flight trails, and concentric target rings.
  - `Distortion`: Continuous algorithmic sinusoidal wave warp.
  - `Split`: Midline fracture with divergent horizontal shifts.
  - `Split2`: Four-quadrant tectonic cross displacement.
  - `Stitch`: Zigzag thread sutures, linen fabric weave, and cross-stitching.
  - `Strippy`: High-frequency vertical grating and scanline bands.
  - `Random`: Dynamically selects a new style for every single challenge.

- **Discord-Native Verification**:
  - Persistent green **Verify** button that survives bot restarts.
  - Ephemeral in-Discord challenges: images and answers are private to the verifying user.
  - Pop-up modal dialog for clean, intuitive code submission.
  - **New Image** refresh button if a challenge is difficult to decipher.

- **Automated Role Management**:
  - Automatically awards the **Verified** role upon solving.
  - Automatically strips an optional **Unverified** role.
  - Automatically assigns the **Unverified** role when new members join.

- **Security & Anti-Abuse**:
  - Cryptographically secure challenge generation (`secrets` module).
  - Unambiguous character set (no confusing `0`/`O` or `1`/`I`).
  - Isolated per-user verification sessions.
  - Single-use challenge validation with replay prevention.
  - Configurable expiration timers, attempt limits, and penalty cooldowns.
  - Interaction rate-limiting to prevent button spamming.

- **Asynchronous SQLite Architecture**:
  - Zero-lag asynchronous database queries via `aiosqlite` with `WAL` mode enabled.
  - Real-time audit logging and verification telemetry.

---

## 📋 Slash Commands

| Command | Permissions | Description |
| :--- | :--- | :--- |
| `/setup` | `Manage Server` | Sets up verification channel, verified/unverified roles, log channel, and posts the persistent verification panel. |
| `/verify` | Everyone | Manually prompts a verification challenge in chat. |
| `/settings` | `Manage Server` | Inspects and customizes CAPTCHA style, timeouts, attempt limits, and cooldowns. |
| `/stats` | Everyone | Displays server verification metrics, total challenges, pass rates, and active security rules. |
| `/help` | Everyone | Displays documentation, setup tips, and a directory of visual styles. |

---

## 🧪 Automated Testing & Diagnostics

The project includes a comprehensive automated test suite covering all modules:

```bash
# Run the complete test suite (21 unit & integration tests)
python tests/run_all.py

# Test all 13 CAPTCHA visual styles individually
python tests/test_captcha_styles.py

# Test SQLite database engine
python tests/test_database.py

# Test session security, rate-limiting, and anti-replay
python tests/test_session_manager.py

# Test Discord slash command tree and UI views
python tests/test_slash_commands.py

# Run main.py in diagnostic boot check mode
python main.py --dry-run
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.11 or higher (Python 3.10+ supported)
- A registered bot application in the [Discord Developer Portal](https://discord.com/developers/applications)
  - Under the **Bot** tab, enable the **Server Members Intent** (`discord.Intents.members`).

### 2. Install Dependencies
```bash
cd captcha
pip install -r requirements.txt
```

### 3. Configure Credentials
Duplicate `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and insert your Discord Bot Token:
```env
DISCORD_TOKEN=MTE5OD...your_actual_token_here
```

### 4. Run the Bot
```bash
# Live mode (connects to Discord gateway)
python main.py

# Or boot diagnostics mode (validates all systems without connecting)
python main.py --dry-run
```

### 5. Server Setup in Discord
1. Invite the bot to your server with `Manage Roles`, `Manage Channels`, and `Send Messages` permissions.
2. In Server Settings > Roles, make sure the **Leakers$ CAPTCHA** bot role is placed **ABOVE** the verified role.
3. In any channel, run:
   ```text
   /setup verification_channel:#verify verified_role:@Member
   ```
4. New members can now click the persistent **Verify** button to complete the CAPTCHA and receive their role!
