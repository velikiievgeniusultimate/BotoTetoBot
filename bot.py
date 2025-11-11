# bot.py
import os
import asyncio
import logging
import discord
from discord.ext import commands

# ---- НАСТРОЙКИ ----
TOKEN = "MTQzNzkyOTE2NzA1OTY4NTM3OA.GmsCao.PG5hz_q0SF23zhqk2yRmP4lbzZoSRoyt9fXa0w"
ROLE_ID = 1437927270810517576  # роль, которую выдаём

# ---- ЛОГИ ----
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("autorole")

# ---- INTENTS (в Dev Portal должен быть включён SERVER MEMBERS INTENT) ----
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    log.info(f"Зашёл как {bot.user} (id={bot.user.id})")
    try:
        await bot.change_presence(activity=discord.Game("выдаю роли"))
    except Exception:
        pass


@bot.event
async def on_member_join(member: discord.Member):
    """Автовыдача роли при заходе."""
    if member.bot:
        return

    role = member.guild.get_role(ROLE_ID)
    if role is None:
        log.error(f"Роль с ID {ROLE_ID} не найдена на сервере {member.guild.name}")
        return

    # небольшая задержка, чтобы Discord успел "дослать" данные юзера
    await asyncio.sleep(1.0)

    try:
        await member.add_roles(role, reason="Auto-assign on join")
        log.info(f"Выдал '{role.name}' пользователю {member} на сервере '{member.guild.name}'")
    except discord.Forbidden:
        log.error("Нет прав: нужно 'Manage Roles' и роль бота ДОЛЖНА быть выше целевой.")
    except discord.HTTPException as e:
        log.error(f"Ошибка Discord API при выдаче роли: {e}")


# Команда на всякий случай: выдать роль существующему участнику
@bot.command()
@commands.has_permissions(manage_roles=True)
async def give(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    role = ctx.guild.get_role(ROLE_ID)
    if role is None:
        return await ctx.reply("Роль не найдена. Проверь ROLE_ID.")
    try:
        await member.add_roles(role, reason="Manual give")
        await ctx.reply(f"Выдал роль **{role.name}** пользователю **{member.display_name}**")
    except discord.Forbidden:
        await ctx.reply("Нет прав. У бота должна быть роль выше целевой и право Manage Roles.")


# --- МАЛЕНЬКИЙ ВЕБ-СЕРВЕР ДЛЯ RENDER (если деплоишь как Web Service) ---
# Если Render задаёт переменную PORT — поднимем HTTP, иначе просто бота.
async def maybe_start_http_server():
    port = os.getenv("PORT")
    if not port:
        return
    from aiohttp import web

    async def ok(_):
        return web.Response(text="ok")

    app = web.Application()
    app.router.add_get("/", ok)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(port))
    await site.start()
    log.info(f"HTTP healthcheck server on :{port}")

# Запуск всего
async def main():
    await maybe_start_http_server()
    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
