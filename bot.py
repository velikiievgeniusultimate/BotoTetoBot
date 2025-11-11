# bot.py
import os
import asyncio
import logging
import discord
from discord.ext import commands

# --- CONFIG (из переменных окружения) ---
TOKEN = os.getenv("DISCORD_TOKEN")               # НОВЫЙ токен положим в Render
ROLE_ID = int(os.getenv("ROLE_ID", "1437927270810517576"))  # твой ID роли по умолчанию

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set")

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("autorole")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    log.info(f"Зашёл как {bot.user}")
    await bot.change_presence(activity=discord.Game("выдаю роли"))

@bot.event
async def on_member_join(member: discord.Member):
    if member.bot:
        return
    role = member.guild.get_role(ROLE_ID)
    if role is None:
        log.error(f"Роль {ROLE_ID} не найдена в {member.guild.name}")
        return
    await asyncio.sleep(1)
    try:
        await member.add_roles(role, reason="Auto role")
        log.info(f"Выдал '{role.name}' пользователю {member}")
    except discord.Forbidden:
        log.error("Нет прав: у бота должно быть Manage Roles и его роль выше целевой.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def give(ctx, member: discord.Member=None):
    if member is None:
        member = ctx.author
    role = ctx.guild.get_role(ROLE_ID)
    if role is None:
        return await ctx.reply("Роль не найдена.")
    await member.add_roles(role, reason="Manual give")
    await ctx.reply(f"Выдал роль **{role.name}** пользователю **{member.display_name}**")

# HTTP healthcheck для Render (если это Web Service)
async def maybe_start_http_server():
    port = os.getenv("PORT")
    if not port:
        return
    from aiohttp import web
    async def ok(_): return web.Response(text="ok")
    app = web.Application()
    app.router.add_get("/", ok)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(port)); await site.start()
    log.info(f"Healthcheck http://0.0.0.0:{port}/")

async def main():
    await maybe_start_http_server()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
