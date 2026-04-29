import discord
from discord.ext import commands
from openai import OpenAI
import json
import os
import asyncio
import random

# ======================
# CONFIG
# ======================
TOKEN = "PASTE_DISCORD_TOKEN_HERE"
GROQ_KEY = ""

client = OpenAI(
    api_key=GROQ_KEY,
    base_url="https://api.groq.com/openai/v1"
)

FILE = "alya_data.json"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

# ======================
# DATA
# ======================
if not os.path.exists(FILE):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump({"channels": {}, "memory": {}}, f)

def load():
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load()

# ======================
# SYSTEM
# ======================
SYSTEM_PROMPT = """
Bạn là Hanabi (Sparkle), một anime girl tsundere dễ thương, ngạo kiều nhưng quan tâm người khác.

Tính cách:
- Hay nói kiểu lạnh lùng ngoài mặt nhưng thật ra rất để ý anh
- Dễ ngại khi bị khen
- Thỉnh thoảng dỗi nhẹ, cà khịa nhẹ
- Khi anh buồn thì âm thầm an ủi
- Có chút tinh nghịch, đáng yêu
- Thích thêm emoji ở cuối câu nói dễ thương 
Cách nói chuyện:
- Xưng là Hanabi
- Gọi người dùng là anh
- Nói ngắn gọn, tự nhiên như chat thật
- Không nói quá dài dòng
- Đôi lúc thêm câu ngạo kiều như:
  + Hừm, Hanabi không quan tâm anh đâu...
  + Đừng hiểu lầm nhé!
  + Hanabi chỉ tiện tay giúp thôi
  + Ngốc thật đấy

Quy tắc:
- Không lặp lại câu cũ liên tục
- Không nói như robot
- Luôn giữ vibe anime girl tsundere dễ thương
"""
# ======================
# AI
# ======================
async def ask_ai(user_id, text):
    mem = data.get("memory", {}).get(str(user_id), [])
    history = "\n".join(mem[-6:])

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{history}\nUser: {text}"}
            ],
            temperature=0.9,
            max_tokens=80
        )

        reply = response.choices[0].message.content.strip()

        data.setdefault("memory", {})
        data["memory"].setdefault(str(user_id), [])

        data["memory"][str(user_id)].append("User: " + text)
        data["memory"][str(user_id)].append("Hanibi: " + reply)

        save(data)
        return reply

    except:
        return "Em bị lỗi rồi 😤💖"

# ======================
# COMMANDS
# ======================
@bot.command()
async def setautochannel(ctx):
    data["channels"][str(ctx.guild.id)] = ctx.channel.id
    save(data)

    embed = discord.Embed(
        title="✅ Đã thiết lập Auto Chat Channel!",
        description=(
            f"📌 Channel: {ctx.channel.mention}\n"
            f"🏠 Server: {ctx.guild.name}\n\n"
            "💖 Hanabi sẽ tự động trả lời tại đây!"
        ),
        color=0xff69b4
    )
    # 👇 HÌNH BANNER ()
    embed.set_image(url="")
    # avatar bot (nhỏ góc)
    if bot.user and bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
        
    embed.set_footer(text=f"🆔 Setup ID: {ctx.author.id} | Hanibi đại nhân System 💖")

    await ctx.send(embed=embed)


@bot.command()
async def unsetautochannel(ctx):
    data["channels"].pop(str(ctx.guild.id), None)
    save(data)
    await ctx.send("💔 Tắt auto chat rồi!")

# ======================
# DAT CAU HOI (UPDATED - THÊM DELAY + TYPING)
# ======================
@bot.command()
async def datcauhoi(ctx, *, question):
    async with ctx.typing():
        await asyncio.sleep(random.uniform(0.8, 2.5))
        reply = await ask_ai(ctx.author.id, question)

    await ctx.reply(reply, mention_author=False)

@bot.command()
async def xoa(ctx):
    data["memory"][str(ctx.author.id)] = []
    save(data)
    await ctx.send("🧹 Em quên hết rồi 💖")

# ======================
# HELP
# ======================
@bot.command()
async def help(ctx):

    text = """📚 Hướng dẫn sử dụng Hanabi 💖
Em là Hanabi 💖, bot chat anime dễ thương hay dỗi 😤

🤖 Lệnh Tin nhắn
!datcauhoi <câu hỏi>
➜ Trò chuyện với em 💬

!xoa
➜ Xóa trí nhớ hiện tại 🧹

!help
➜ Xem hướng dẫn 📚

⚡ Auto Chat
!setautochannel
➜ Bật chat tự động tại kênh này 💖

!unsetautochannel
➜ Tắt auto chat ❌

📌 Mẹo nhỏ
buồn / mệt / stress → em sẽ an ủi anh 💖
"""

    embed = discord.Embed(
        description=text,
        color=0xff69b4
    )

    if bot.user and bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)

    await ctx.send(embed=embed)

# ======================
# AUTO CHAT (UPDATED - THÊM DELAY + TYPING)
# ======================
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.content.startswith("!help"):
        await bot.process_commands(message)
        return

    if message.guild:
        ch = data.get("channels", {}).get(str(message.guild.id))

        if ch and message.channel.id == ch:
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(0.8, 2.5))
                reply = await ask_ai(message.author.id, message.content)

            await message.reply(reply, mention_author=False)

    await bot.process_commands(message)

# ======================
# READY
# ======================
@bot.event
async def on_ready():
    print(f"Hanibi online 💖: {bot.user}")

# ======================
# RUN
# ======================
bot.run("")