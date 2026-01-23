import os
import re
import json
from dataclasses import dataclass
from typing import Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Charge .env si présent (utile sur PC). Sur Railway, DISCORD_TOKEN doit être dans Variables.
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# ----------------- CONFIG -----------------
# Salons où le bot répond (1 ou 2 noms EXACTS) — Mets ici le salon où les gens commandent au barista
ALLOWED_CHANNELS = {"🛎️ᝰᐟ𝑪𝒐𝒎𝒎𝒂𝒏𝒅𝒆𝒔"}

# Salon où le bot envoie les commandes (nom EXACT)
ORDERS_CHANNEL_NAME = "🛎️ᝰᐟ𝑪𝒐𝒎𝒎𝒂𝒏𝒅𝒆𝒔"

# ----------------- TEXTES RP (FIXES) -----------------
WELCOME_TEXT = (
    "Derrière le comptoir, la barista ajuste son tablier, un sourire chaleureux aux lèvres tandis que l’odeur du café fraîchement moulu emplit l’air. "
    "<:33465brownribbon:1463820318329143296>\n"
    "« Bonjour et bienvenue au Galop Gourmand !  <:image1:1463626069629210808>  Que puis-je vous servir aujourd’hui ? »"
)

CHECKOUT_TEXT = (
    "Elle pianote doucement sur la caisse, jette un coup d’œil à l’écran avant de relever la tête. "
    "<:18706whitestar:1463819220759347231>\n"
    "« Parfait ! Cela vous fera un total de **{total}💰** <:7863symboldollarsign:1463822083481014303> . "
    "<:20698brownspiral2:1463624287025107169>\n"
    "Après règlement, il vous restera **{balance}💰** <:7863symboldollarsign:1463822083481014303> sur votre compte. »"
)

GOODBYE_TEXT = (
    "Elle tend la commande avec soin et un clin d’œil complice. "
    "<:54936emptybox:1463625944102342810>\n"
    "« Nous vous souhaitons une excellente dégustation ! <:Pancakes:1463615869979459851>\n"
    "À très bientôt au Galop Gourmand ! <:image1:1463626069629210808> <:31461caffelatte:1463624366465093774> »"
)

# ----------------- IMAGES PAR SITUATION (URL DIRECTES) -----------------
WELCOME_IMAGE = "https://cdn.discordapp.com/attachments/1463232375487070415/1463232376875520053/image.png?ex=69746098&is=69730f18&hm=799962548d319a74d040e32a4a0a30dd0816eb7969c13ff7333faef4b1580dc9&"
CHECKOUT_IMAGE = "https://cdn.discordapp.com/attachments/1463232375487070415/1463232400002777109/image.png?ex=6974609d&is=69730f1d&hm=304bcc0d96568cfc9b7f3b08f53ea2d9c55b2bb16ff719c17b9431e43b43dff0&"
GOODBYE_IMAGE = "https://cdn.discordapp.com/attachments/1463232375487070415/1463232447041896488/image.png?ex=697460a8&is=69730f28&hm=25ee1806f6499967ede4f885a4cc665b6fed8ca1a9bf16c3602ea90c62b9455a&"

# ----------------- SYSTEME ARGENT RP -----------------
MONEY_FILE = "money.json"
START_MONEY = 20  # argent de départ

# Prix (💰 = € dans ton RP, avec décimales possibles)
PRICES = {
    # 🍰 Pâtisseries & Viennoiseries
    "macaron": 1.5,
    "cinnamon_roll": 3.5,
    "croissant": 1.2,
    "pain_au_chocolat": 1.3,
    "brioche": 1.8,

    # 🍮 Desserts individuels
    "panna_cotta": 3.5,
    "muffin": 2.8,
    "donut": 2.5,
    "roule_japonais": 4.2,
    "cookie": 2.2,

    # 🥞 Crêpes & Gaufres
    "crepe_nature": 2.0,
    "crepe_garnie": 3.0,
    "gaufre_nature": 2.5,
    "gaufre_garnie": 3.0,

    # 🍧 Cheesecakes, Brownies & Éclairs
    "cheesecake": 4.5,
    "brownie": 2.5,
    "eclair": 3.0,

    # 🍩 Beignets & Gâteaux
    "beignet": 2.0,
    "gateau_part": 4.0,

    # 🥧 Tartes
    "tarte_part": 3.8,

    # 🍞 Toasts & Salés
    "toast_sucre": 3.0,
    "toast_avocat_saumon": 6.5,
    "toast_avocat_crevette": 6.8,

    # 🥞 Pancakes
    "pancakes": 3.8,

    # ☕ Café & dérivés (chaud)
    "espresso": 2.0,
    "cafe_allonge": 2.2,
    "americano": 2.5,
    "cafe_creme": 2.8,
    "cappuccino": 3.5,
    "chocolat_chaud": 3.8,
    "moka_blanc": 4.2,
    "matcha_latte": 4.5,
    "macchiato": 3.2,
    "caramel_latte": 4.2,
    "vanille_latte": 4.2,
    "latte_lavande": 4.5,
    "latte_speculoos": 4.5,

    # 🍵 Thés & infusions
    "the": 2.8,

    # 🧊 Boissons froides
    "milkshake": 4.5,
    "coca_cola": 2.5,
    "mojito_sans_alcool": 4.0,
    "bubble_tea": 4.9,
    "refreshing": 3.8,
    "mimi_matcha": 5.0,
    "jus_de_fruit": 3.5,
    "ice_tea_maison": 3.5,
}


def load_money():
    if not os.path.exists(MONEY_FILE):
        return {}
    with open(MONEY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_money(data):
    with open(MONEY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


money_data = load_money()


def get_balance(user_id: int) -> float:
    uid = str(user_id)
    if uid not in money_data:
        money_data[uid] = START_MONEY
        save_money(money_data)
    return float(money_data[uid])


def add_money(user_id: int, amount: float):
    uid = str(user_id)
    money_data[uid] = get_balance(user_id) + float(amount)
    save_money(money_data)


def remove_money(user_id: int, amount: float) -> bool:
    uid = str(user_id)
    if get_balance(user_id) < float(amount):
        return False
    money_data[uid] = get_balance(user_id) - float(amount)
    save_money(money_data)
    return True


# ----------------- MENU + DETECTION -----------------
DRINK_KEYWORDS = {
    # ☕ Café & dérivés (chaud)
    "espresso": ["expresso", "espresso", "café expresso", "cafe expresso"],
    "cafe_allonge": ["café allongé", "cafe allonge", "allongé", "allonge"],
    "americano": ["américano", "americano"],
    "cafe_creme": ["café crème", "cafe creme", "creme"],
    "cappuccino": ["cappuccino", "cappu"],
    "chocolat_chaud": ["chocolat chaud", "choco chaud"],
    "moka_blanc": ["moka blanc", "mocha blanc"],
    "matcha_latte": ["matcha latté", "matcha latte", "latte matcha"],
    "macchiato": ["macchiato"],
    "caramel_latte": ["caramel latté", "caramel latte", "latte caramel"],
    "vanille_latte": ["vanille latté", "vanille latte", "latte vanille"],
    "latte_lavande": ["latté lavande", "latte lavande", "lavande latte"],
    "latte_speculoos": ["latté spéculoos", "latte speculoos", "latte spéculoos", "speculoos latte"],

    # 🍵 Thés & infusions
    "the": ["thé", "the", "infusion", "tisane"],

    # 🧊 Boissons froides
    "milkshake": ["milkshake", "milk shake"],
    "coca_cola": ["coca-cola", "coca cola", "coca"],
    "mojito_sans_alcool": ["mojito sans alcool", "mojito (sans alcool)", "mojito"],
    "bubble_tea": ["bubble tea", "bubbletea", "boba"],
    "refreshing": [
        "refreshing",
        "boisson rafraîchissante",
        "boisson rafraichissante",
        "rafraîchissante maison",
        "rafraichissante maison",
    ],
    "mimi_matcha": ["mimi matcha"],
    "jus_de_fruit": ["jus de fruit", "jus", "jus d'orange", "jus de pomme"],
    "ice_tea_maison": ["ice tea", "ice tea maison", "thé glacé", "the glace", "iced tea"],
}

FOOD_KEYWORDS = {
    "macaron": ["macaron", "macarons"],
    "cinnamon_roll": ["cinnamon roll", "cinnamon rolls", "roule a la cannelle", "roulé à la cannelle"],
    "croissant": ["croissant"],
    "pain_au_chocolat": ["pain au chocolat", "chocolatine"],
    "brioche": ["brioche", "tranche de brioche"],

    "panna_cotta": ["panna cotta"],
    "muffin": ["muffin", "muffins"],
    "donut": ["donut", "donuts"],
    "roule_japonais": ["roulé japonais", "roule japonais"],
    "cookie": ["cookie", "cookies"],

    "crepe_nature": ["crêpe nature", "crepe nature"],
    "crepe_garnie": ["crêpe nutella", "crêpe caramel", "crêpe confiture", "crêpe chantilly",
                     "crepe nutella", "crepe caramel", "crepe confiture", "crepe chantilly"],
    "gaufre_nature": ["gaufre nature"],
    "gaufre_garnie": ["gaufre nutella", "gaufre caramel", "gaufre confiture", "gaufre chantilly"],

    "cheesecake": ["cheesecake"],
    "brownie": ["brownie"],
    "eclair": ["éclair", "eclairs", "eclair"],

    "beignet": ["beignet", "beignets"],
    "gateau_part": ["part de gâteau", "part de gateau", "gateau", "gâteau"],

    "tarte_part": ["tarte", "part de tarte"],

    "toast_sucre": ["toast sucré", "toast sucre", "toast nutella", "toast caramel", "toast confiture"],
    "toast_avocat_saumon": ["toast avocat saumon"],
    "toast_avocat_crevette": ["toast avocat crevette"],

    "pancakes": ["pancake", "pancakes"],
}


def normalize(text: str) -> str:
    return text.lower().strip()


@dataclass
class OrderLine:
    item: str
    quantity: int


NUMBER_WORDS = {
    "un": 1, "une": 1,
    "deux": 2,
    "trois": 3,
    "quatre": 4,
    "cinq": 5,
    "six": 6,
    "sept": 7,
    "huit": 8,
    "neuf": 9,
    "dix": 10,
}


def _extract_qty_before(text: str, start_index: int) -> int:
    """
    Cherche une quantité juste avant un item.
    Ex: "2 cookies" => 2 ; "deux cookies" => 2 ; sinon 1.
    """
    left = text[:start_index].lower()
    window = left[-25:]

    m = re.search(r"(\d{1,2})\s*$", window)
    if m:
        q = int(m.group(1))
        return max(1, min(q, 20))

    for w, n in NUMBER_WORDS.items():
        if re.search(rf"\b{re.escape(w)}\b\s*$", window):
            return n

    return 1


def parse_orders(text: str) -> list[OrderLine]:
    """
    Retourne une liste d'items trouvés dans le message.
    Ex: "2 donuts et 1 cappuccino" => [donut x2, cappuccino x1]
    """
    t = normalize(text)

    aliases: list[tuple[str, str]] = []
    for item, keys in DRINK_KEYWORDS.items():
        for k in keys:
            aliases.append((normalize(k), item))
    for item, keys in FOOD_KEYWORDS.items():
        for k in keys:
            aliases.append((normalize(k), item))

    aliases.sort(key=lambda x: len(x[0]), reverse=True)

    found: list[tuple[int, int, str]] = []
    used_ranges: list[tuple[int, int]] = []

    def overlaps(a, b):
        return not (a[1] <= b[0] or b[1] <= a[0])

    for phrase, item in aliases:
        start = 0
        while True:
            idx = t.find(phrase, start)
            if idx == -1:
                break
            rng = (idx, idx + len(phrase))
            if any(overlaps(rng, r) for r in used_ranges):
                start = idx + 1
                continue
            found.append((rng[0], rng[1], item))
            used_ranges.append(rng)
            start = idx + 1

    if not found:
        return []

    found.sort(key=lambda x: x[0])

    counts: dict[str, int] = {}
    for start, end, item in found:
        q = _extract_qty_before(t, start)
        counts[item] = counts.get(item, 0) + q

    return [OrderLine(item=k, quantity=v) for k, v in counts.items()]


def pretty_item(item: str) -> str:
    mapping = {
        # Nourriture
        "macaron": "macaron",
        "cinnamon_roll": "cinnamon roll",
        "croissant": "croissant",
        "pain_au_chocolat": "pain au chocolat",
        "brioche": "tranche de brioche",
        "panna_cotta": "panna cotta",
        "muffin": "muffin",
        "donut": "donut",
        "roule_japonais": "roulé japonais",
        "cookie": "cookie",
        "crepe_nature": "crêpe nature",
        "crepe_garnie": "crêpe garnie",
        "gaufre_nature": "gaufre nature",
        "gaufre_garnie": "gaufre garnie",
        "cheesecake": "cheesecake",
        "brownie": "brownie",
        "eclair": "éclair",
        "beignet": "beignet",
        "gateau_part": "part de gâteau",
        "tarte_part": "part de tarte",
        "toast_sucre": "toast sucré",
        "toast_avocat_saumon": "toast avocat saumon",
        "toast_avocat_crevette": "toast avocat crevette",
        "pancakes": "portion de pancakes",
        # Boissons
        "espresso": "café expresso",
        "cafe_allonge": "café allongé",
        "americano": "américano",
        "cafe_creme": "café crème",
        "cappuccino": "cappuccino",
        "chocolat_chaud": "chocolat chaud",
        "moka_blanc": "moka blanc",
        "matcha_latte": "matcha latté",
        "macchiato": "macchiato",
        "caramel_latte": "caramel latté",
        "vanille_latte": "vanille latté",
        "latte_lavande": "latté lavande",
        "latte_speculoos": "latté spéculoos",
        "the": "thé",
        "milkshake": "milkshake",
        "coca_cola": "Coca-Cola",
        "mojito_sans_alcool": "mojito (sans alcool)",
        "bubble_tea": "bubble tea",
        "refreshing": "Refreshing (maison)",
        "mimi_matcha": "Mimi Matcha (signature)",
        "jus_de_fruit": "jus de fruit",
        "ice_tea_maison": "Ice Tea maison",
    }
    return mapping.get(item, item)


def fmt_money(x: float) -> str:
    # Affiche 2 décimales si besoin, sinon entier propre
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.2f}"


# ----------------- DISCORD BOT -----------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")


def channel_allowed(channel: discord.abc.GuildChannel) -> bool:
    if not hasattr(channel, "name"):
        return False
    return normalize(channel.name) in {normalize(c) for c in ALLOWED_CHANNELS}


async def get_orders_channel(guild: discord.Guild) -> Optional[discord.TextChannel]:
    for ch in guild.text_channels:
        if normalize(ch.name) == normalize(ORDERS_CHANNEL_NAME):
            return ch
    return None


async def post_order_to_channel(message: discord.Message, parts: list[str], total_price: float):
    orders_channel = await get_orders_channel(message.guild)
    if not orders_channel:
        return

    await orders_channel.send(
        f"🧾 **Commande** de {message.author.mention} dans {message.channel.mention} : "
        + " | ".join(parts)
        + (f" | Total: **{fmt_money(total_price)}💰**" if total_price > 0 else "")
    )


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if not isinstance(message.channel, discord.TextChannel):
        return
    if not channel_allowed(message.channel):
        return

    content = message.content.strip()
    if not content:
        return

    orders = parse_orders(content)

    # Situation 1 : Accueil
    if not orders:
        if any(w in normalize(content) for w in ["bonjour", "salut", "coucou", "hello"]):
            embed = discord.Embed(description=WELCOME_TEXT)
            embed.set_image(url=WELCOME_IMAGE)
            await message.channel.send(embed=embed)
        return

    # --- Calcul total + paiement ---
    parts: list[str] = []
    total_price = 0.0

    for o in orders:
        item_str = pretty_item(o.item)
        parts.append(f"**{o.quantity}× {item_str}**")
        total_price += float(PRICES.get(o.item, 0.0)) * o.quantity

    balance = get_balance(message.author.id)

    if total_price > 0 and balance < total_price:
        embed = discord.Embed(
            description=(
                f"❌ Vous n’avez pas assez d’argent. Total: **{fmt_money(total_price)}💰**, "
                f"Solde: **{fmt_money(balance)}💰**."
            )
        )
        embed.set_image(url=CHECKOUT_IMAGE)
        await message.channel.send(embed=embed)
        return

    if total_price > 0:
        remove_money(message.author.id, total_price)

    new_balance = get_balance(message.author.id)

    # Situation 2 : Passage en caisse
    embed_checkout = discord.Embed(
        description=CHECKOUT_TEXT.format(total=fmt_money(total_price), balance=fmt_money(new_balance))
    )
    embed_checkout.set_image(url=CHECKOUT_IMAGE)
    await message.channel.send(embed=embed_checkout)

    # Situation 3 : Au revoir / Dégustation
    embed_goodbye = discord.Embed(description=GOODBYE_TEXT)
    embed_goodbye.set_image(url=GOODBYE_IMAGE)
    await message.channel.send(embed=embed_goodbye)

    # Envoi dans le salon commandes
    await post_order_to_channel(message, parts, total_price)

    await bot.process_commands(message)


# ----------------- COMMANDES ARGENT -----------------
@bot.command()
async def balance(ctx):
    bal = get_balance(ctx.author.id)
    await ctx.send(f"💰 Tu as **{fmt_money(bal)}💰**.")


@bot.command()
@commands.has_permissions(administrator=True)
async def give(ctx, member: discord.Member, amount: float):
    add_money(member.id, amount)
    await ctx.send(
        f"💸 {member.mention} reçoit **{fmt_money(amount)}💰** (nouveau solde: **{fmt_money(get_balance(member.id))}💰**)."
    )


@bot.command()
@commands.has_permissions(administrator=True)
async def setmoney(ctx, member: discord.Member, amount: float):
    uid = str(member.id)
    money_data[uid] = max(0.0, float(amount))
    save_money(money_data)
    await ctx.send(f"🧾 Solde de {member.mention} fixé à **{fmt_money(get_balance(member.id))}💰**.")


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN manquant. Mets-le dans Railway > Variables (clé DISCORD_TOKEN).")
    bot.run(TOKEN)
