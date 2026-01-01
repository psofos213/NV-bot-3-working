# ================= IMPORTS =================
import discord
from discord.ext import commands
import asyncio, json, os, re, aiohttp
from datetime import datetime
from discord.ui import View, Select, Button


# ================= CONFIG =================
import os

token = os.environ['TOKEN']
print("Το token φορτώθηκε:", token)


SUPPORT_ROLE_ID = 1447201794546728960
ADMIN_ROLE_IDS = [
    1430598482376523978,
    1430597627447214221,
    1447222289438343239,
    1430597077552988243
]

VOICE_CHANNELS_TRACKED = [1430595558422216756, 1430595452868497619]
SUPPORT_VOICE_CHANNELS = [
    1453084859885944832,
    1453088268315791490,
    1453088314956582952,
    1453088345617076295
]

DATA_FILE = "voice_activity.json"
JOIN_LEAVE_LOG_CHANNEL = 1453395355176669289
AUTO_ROLE_NAME = "💤〢Nova"

# ================= BOT =================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= HELPERS =================
def is_admin(member):
    return any(r.id in ADMIN_ROLE_IDS for r in member.roles)

# ================= VOICE TRACK =================
voice_time = {}
voice_join_time = {}

if os.path.exists(DATA_FILE):
    with open(DATA_FILE) as f:
        voice_time = {int(k): int(v) for k,v in json.load(f).items()}

def save_voice_time():
    with open(DATA_FILE,"w") as f:
        json.dump({str(k):v for k,v in voice_time.items()}, f)

@bot.event
async def on_voice_state_update(member, before, after):
    before_id = before.channel.id if before.channel else None
    after_id = after.channel.id if after.channel else None

    if after_id in VOICE_CHANNELS_TRACKED and before_id not in VOICE_CHANNELS_TRACKED:
        voice_join_time[member.id] = datetime.utcnow()

    elif before_id in VOICE_CHANNELS_TRACKED and after_id not in VOICE_CHANNELS_TRACKED:
        join = voice_join_time.pop(member.id, None)
        if join:
            seconds = int((datetime.utcnow() - join).total_seconds())
            voice_time[member.id] = voice_time.get(member.id, 0) + seconds
            save_voice_time()

# ================= EVENTS =================





@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=AUTO_ROLE_NAME)
    if role:
        await member.add_roles(role)

    ch = bot.get_channel(JOIN_LEAVE_LOG_CHANNEL)
    if ch:
        await ch.send(f"👋 {member.mention} joined the server.")

@bot.event
async def on_member_remove(member):
    ch = bot.get_channel(JOIN_LEAVE_LOG_CHANNEL)
    if ch:
        await ch.send(f"👋 {member.mention} left the server.")

# ================= MESSAGE FILTER =================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if any(w in message.content.lower() for w in ["shit","fuck"]):
        await message.delete()
        await message.channel.send(f"{message.author.mention} - don't use that word!")

    if len(message.mentions) > 5:
        await message.delete()
        await message.channel.send(f"{message.author.mention} - Too many mentions!")

    await bot.process_commands(message)

# ================= COMMANDS =================

@bot.command()
async def say(ctx, *, message=None):
    files = [await a.to_file() for a in ctx.message.attachments]
    await ctx.send(content=message, files=files)

@bot.command()
@commands.has_permissions(manage_emojis=True)
async def addemoji(ctx, *, emoji: str):
    match = re.match(r'<(a?):(\w+):(\d+)>', emoji)
    if not match:
        return await ctx.send("❌ Μη έγκυρο custom emoji.")
    animated,name,emoji_id = match.groups()
    emoji_id=int(emoji_id)

    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            image = await resp.read()

    new = await ctx.guild.create_custom_emoji(name=name,image=image)
    await ctx.send(new)

@bot.command()
@commands.has_permissions(administrator=True)
async def dm(ctx, *, message):
    sent = 0
    for m in ctx.guild.members:
        if not m.bot:
            try:
                await m.send(message)
                sent += 1
            except:
                pass
    await ctx.send(f"✅ DM στάλθηκαν σε {sent} χρήστες!")

@bot.command()
@commands.has_permissions(administrator=True)
async def dmdelete(ctx):
    deleted = 0
    for m in ctx.guild.members:
        if m.bot: continue
        try:
            async for msg in m.dm_channel.history(limit=100):
                if msg.author == bot.user:
                    await msg.delete()
                    deleted += 1
        except:
            pass
    await ctx.send(f"✅ Διαγράφηκαν {deleted} DM!")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong 🏓 {round(bot.latency*1000)}ms")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)
    await ctx.send("🧹 Done", delete_after=5)

@bot.command()
async def roles(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [r.name for r in member.roles if r != ctx.guild.default_role]
    await ctx.send(", ".join(roles) if roles else "No roles")

@bot.command()
async def activity(ctx, role: discord.Role):
    if not is_admin(ctx.author):
        return
    msg = f"**Voice activity for {role.name}:**\n"
    for m in role.members:
        t = voice_time.get(m.id, 0)
        h, r = divmod(t, 3600)
        m_, s = divmod(r, 60)
        msg += f"{m.display_name}: {h}h {m_}m {s}s\n"
    await ctx.send(msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset_activity(ctx, role: discord.Role = None):
    global voice_time
    if role:
        for m in role.members:
            voice_time[m.id] = 0
    else:
        voice_time = {k:0 for k in voice_time}
    save_voice_time()
    await ctx.send("✅ Voice activity reset!")


TICKET_CATEGORY_ID = 1430592456251932703
LOG_CHANNEL_ID = 1447656535986798603

ADMIN_ROLE_IDS = [
    1430598482376523978,
    1430597627447214221,
    1447222289438343239,
    1430597077552988243
]

THUMBNAIL_GIF = "https://cdn.discordapp.com/attachments/1452671984948477962/1454471257872400628/yourgif.gif"

class CloseTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Close Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket_button"
    )
    async def close(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction
    ):
        # ACK ΑΜΕΣΑ
        await interaction.response.defer()

        # permission check
        if not any(role.id in ADMIN_ROLE_IDS for role in interaction.user.roles):
            await interaction.followup.send(
                "❌ Δεν έχεις permission να κλείσεις αυτό το ticket.",
                ephemeral=True
            )
            return

        # disable button
        button.disabled = True
        await interaction.message.edit(view=self)

        await interaction.followup.send(
            "🔒 Το ticket θα κλείσει σε **5 δευτερόλεπτα**..."
        )

        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(
                f"📁 Ticket `{interaction.channel.name}` closed by {interaction.user.mention}"
            )

        await asyncio.sleep(5)
        await interaction.channel.delete(reason="Ticket closed")






class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support", emoji="🛠", value="support"),
            discord.SelectOption(label="Purchase", emoji="💰", value="purchase"),
            discord.SelectOption(label="Contact Owner", emoji="📩", value="contact")
        ]

        super().__init__(
            placeholder="Choose category...",
            options=options,
            custom_id="ticket_dropdown"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(TICKET_CATEGORY_ID)

        if not category:
            return await interaction.followup.send("❌ Category not found.", ephemeral=True)

        for ch in category.text_channels:
            if ch.name.endswith(str(user.id)):
                return await interaction.followup.send(
                    f"❌ Έχεις ήδη ticket: {ch.mention}",
                    ephemeral=True
                )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        for rid in ADMIN_ROLE_IDS:
            role = guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True
                )

        channel = await guild.create_text_channel(
            name=f"ticket-{self.values[0]}-{user.id}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎟️ Ticket Opened",
            description=(
                f"{user.mention}\n\n"
                "📩 Περιέγραψε το πρόβλημά σου.\n"
                "⏳ Το staff θα σε εξυπηρετήσει σύντομα."
            ),
            color=discord.Color.dark_theme()
        )

        embed.set_thumbnail(url=THUMBNAIL_GIF)
        embed.set_author(name="NV Security", icon_url=THUMBNAIL_GIF)

        # ⬅️ ΕΔΩ το μυστικό: δημιουργείται ΕΝΤΟΣ event loop
        await channel.send(embed=embed, view=CloseTicket())


        await interaction.followup.send(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


@bot.command()
@commands.has_permissions(administrator=True)
async def ticketpanel(ctx):
    embed = discord.Embed(
        title="🎟️ NV | Tickets",
        description=(
            "**ΓΙΑ ΤΗΝ ΑΜΕΣΗ ΕΞΥΠΗΡΕΤΗΣΗ ΣΑΣ**\n\n"
            "👉 Άνοιξε ticket επιλέγοντας κατηγορία από το dropdown."
        ),
        color=discord.Color.dark_theme()
    )

    embed.set_thumbnail(url=THUMBNAIL_GIF)

    await ctx.send(
        embed=embed,
        view=TicketPanel()
    )






# ================= READY =================
@bot.event
async def on_ready():
    bot.add_view(TicketPanel())
    bot.add_view(CloseTicket())
    print("✅ Ticket panel & close button active after restart")


FEEDBACK_CHANNEL_ID = 1448312366055034930 

@bot.command()
async def feedback(ctx, stars: int, *, message):
    if stars < 1 or stars > 5:
        await ctx.send("❌ Βάλε έναν αριθμό από 1 έως 5 για τα stars.")
        return

    channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
    if channel is None:
        await ctx.send("❌ Κάτι πήγε λάθος: δεν βρέθηκε το κανάλι για feedback.")
        return

    stars_display = "⭐" * stars
    embed = discord.Embed(
        title=f"Νέο Feedback: {stars_display}",
        description=message,
        color=discord.Color.gold()
    )
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    
    await channel.send(embed=embed)
    await ctx.send(f"✅ Ευχαριστούμε για το feedback σου! Έβαλες {stars}⭐")


from keep_alive import keep_alive
import time

def start_bot():
    print("Το bot ξεκίνησε!")
    while True:
        print("Το bot τρέχει...")
        time.sleep(10)

if __name__ == "__main__":
    keep_alive()
    start_bot()













# ================= RUN =================
bot.run(TOKEN)
