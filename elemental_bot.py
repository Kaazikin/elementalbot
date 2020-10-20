# TODO Personal inventory
# TODO Add Firebase backup
# TODO Fix shared inventory bug
# TODO Fix duplicates in inventory bug

import discord
import math
import random
import pyrebase
from jproperties import Properties
from discord.ext import commands, tasks
import dpymenus
import datetime


# Will fill dictionaries with Firebase data
def populate_dictionaries():
    pass


def sort_element_id(element):
    return element.id


class Category:
    def __init__(self, id, name, desc, colour=0x000000, imageurl=""):
        self.id = id
        self.name = name
        self.desc = desc
        self.colour = colour
        self.imageurl = imageurl


class Combination:
    def __init__(self, id, output, inputs):
        self.id = id
        self.output = output
        self.inputs = sorted(inputs, key=sort_element_id)

    def compare_input(self, other):
        return sorted(self.inputs, key=sort_element_id) == sorted(other.inputs, key=sort_element_id)

    def get_generation(self):
        return max([i.generation for i in self.inputs])

    def __repr__(self):
        return "Combination({}, {}, {}, {})".format(self.id, self.output, self.inputs, self.get_generation())

    def __gt__(self, other):
        return self.id > other.id

    def __lt__(self, other):
        return self.id < other.id

    def __eq__(self, other):
        return self.id == other.id

    def __le__(self, other):
        return self.id <= other.id

    def __ge__(self, other):
        return self.id >= other.id


default = Category(0, "No Category", "These are elements with no category.")
starter = Category(1, "Core", "These are starter elements.")


class Element:
    def __init__(self, combinations, id, name, colour=0x000000, creationdate=datetime.datetime.now(), usecount=0,
                 unlockedcount=1, imageurl="", generation=-1, description="No note.", creator=None, category=default):
        self.combinations = combinations
        self.id = id
        self.name = name
        self.creationdate = creationdate
        self.colour = colour
        self.description = description
        self.imageurl = imageurl
        self.usecount = usecount
        self.unlockedcount = unlockedcount
        self.creator = creator
        self.generation = generation
        self.category = category

    def add_combo(self, combo):
        self.combinations.append(combo)

    def get_generation(self):
        if self.generation == -1:
            self.generation = self.combinations[0].get_generation()+1
            return self.generation
        else:
            return self.generation

    def get_combination_count(self):
        return len(self.combinations)

    def __repr__(self):
        return self.name + " (" + str(self.id) + ")"

    def __gt__(self, other):
        return self.id > other.id

    def __lt__(self, other):
        return self.id < other.id

    def __eq__(self, other):
        return self.id == other.id

    def __le__(self, other):
        return self.id <= other.id

    def __ge__(self, other):
        return self.id >= other.id


class User:
    def __init__(self, id, inventory):
        self.id = id
        self.inventory = inventory

    def get_created(self):
        return [i for i in self.inventory if i.creator == self.id]

    def add_inventory(self, elem):
        self.inventory.append(elem)

    def __repr__(self):
        return "User: " + self.id


intents = discord.Intents.default()
intents.members = True
intents.guild_messages = True
intents.guild_reactions = True
intents.messages = True
intents.reactions = True

client = commands.Bot(command_prefix='!', intents=intents)
config = Properties()

# Load config
with open('application.properties', 'rb') as config_file:
    config.load(config_file)


# Log in confirmation
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    guilds = client.guilds
    for g in guilds:
        for user in g.members:
            # TODO Load inventories from file
            user_dictionary[user.id] = User(user.id, default_inventory)
    await client.change_presence(activity=discord.Game("Looking for #play7"))


# sends all info of an element as an embed.
@client.command()
async def info(ctx, *element):
    element = " ".join(element).capitalize()
    try:
        if element[0] == "#":
            current = element_dictionary[int(element[1:])]
        else:
            current = element_dictionary[element_index[element.capitalize()]]
        output = discord.Embed()
        output.title = "Element Info: " + current.name + " (#" + str(current.id) + ")"
        output.description = current.description
        output.colour = discord.Colour(current.colour)
        output.set_thumbnail(url=current.imageurl)
        output.add_field(name="Created by:", value=str(client.get_user(current.creator)), inline=True)
        output.add_field(name="Created on:", value=str(current.creationdate), inline=True)
        output.add_field(name="Used in:", value=str(current.usecount), inline=True)
        output.add_field(name="Made with:", value=str(current.get_combination_count()), inline=True)
        output.add_field(name="Unlocked by:", value=str(current.unlockedcount), inline=True)
        output.add_field(name="Category:", value=current.category.name, inline=True)
        output.add_field(name="Generation:", value=str(current.get_generation()), inline=True)
        await ctx.send(content="", embed=output)
    except KeyError:
        await ctx.send("Invalid element.")


# Command to combine elements.
@client.command()
async def add(ctx, *, elements):
    valid = False
    if "," in elements:
        elements = elements.split(",")
        valid = True
    elif "+" in elements:
        elements = elements.split("+")
        valid = True
    if 1 < len(elements) < 10 and valid:
        elements_valid = True
        stored_elems = []
        for e in elements:
            e = e.strip()
            e_length = len(e)
            e_original = e
            e = e[0].upper()
            for c in range(1, e_length):
                e += e_original[c]
            try:
                curr = element_dictionary[element_index[e]]
                if curr not in user_dictionary[ctx.message.author.id].inventory:
                    elements_valid = False
                    break
                stored_elems.append(curr)
            except KeyError:
                elements_valid = False
                break
        if elements_valid:
            tempcombo = Combination(-1, None, stored_elems)
            combo_found = False
            combo = None
            for curr_combo in range(len(combo_dictionary)):
                if tempcombo.compare_input(combo_dictionary[curr_combo]):
                    combo_found = True
                    combo = combo_dictionary[curr_combo]
                    break
            if combo_found:
                # TODO Inventory stuff, validation stuff
                user_dictionary[ctx.message.author.id].add_inventory(combo.output)
                await ctx.send("You created " + combo.output.name + ".")
            else:
                last_combo_dictionary[ctx.message.author] = tempcombo
                await ctx.send("This combo does not exist. :red_circle:\nUse !suggest to suggest a combo.")
                # TODO Clean this up
        else:
            await ctx.send("Invalid element.")
    else:
        await ctx.send("Invalid inputs.")


# Adds combinations & new elements
@client.command()
async def suggest(ctx, *, element):
    # TODO Voting
    element = element.strip()
    element_length = len(element)
    element_original = element
    element = element[0].upper()
    for c in range(1, element_length):
        element += element_original[c]

    if ctx.message.author in last_combo_dictionary.keys():
        if element in element_index.keys():
            i = element_index[element]
            out_elem = element_dictionary[i]
            curr = last_combo_dictionary.pop(ctx.message.author, None)
            j = len(combo_dictionary)
            out_combo = Combination(j, out_elem, curr.inputs)
            combo_dictionary[j] = out_combo
            element_dictionary[i].add_combo(combo_dictionary[j])
            out_string = ""
            used_elems = []
            for z in range(len(curr.inputs)):
                out_string += curr.inputs[z].name
                if curr.inputs[z] not in used_elems:
                    curr.inputs[z].usecount += 1
                    used_elems.append(curr.inputs[z])
                if z != len(curr.inputs) - 1:
                    out_string += " + "
                else:
                    out_string += " = " + out_elem.name
            user_dictionary[ctx.message.author.id].add_inventory(out_elem)
            await ctx.send("New combination: " + out_string + " :new:")
        else:
            curr = last_combo_dictionary.pop(ctx.message.author, None)

            j = len(combo_dictionary)

            # TODO Replace random colour with either average colour or colour in range between parents.
            creation_time = datetime.datetime.now()
            creation_time = datetime.datetime(creation_time.year, creation_time.month, creation_time.day,
                                              creation_time.hour, creation_time.minute, creation_time.second)

            elem_colour = int(hex(rand.randint(0, 16777215)), 16)
            out_elem = Element([], len(element_dictionary), element, colour=elem_colour,
                               creationdate=creation_time, creator=ctx.message.author.id,
                               generation=(curr.get_generation() + 1))

            element_dictionary[out_elem.id] = out_elem
            element_index[out_elem.name] = out_elem.id
            out_combo = Combination(j, element_dictionary[out_elem.id], curr.inputs)

            element_dictionary[out_elem.id].add_combo(out_combo)
            combo_dictionary[j] = out_combo

            out_string = ""
            used_elems = []
            for z in range(len(curr.inputs)):
                out_string += curr.inputs[z].name
                if curr.inputs[z] not in used_elems:
                    curr.inputs[z].usecount += 1
                    used_elems.append(curr.inputs[z])
                if z != len(curr.inputs) - 1:
                    out_string += " + "
                else:
                    out_string += " = " + out_elem.name
            user_dictionary[ctx.message.author.id].add_inventory(out_elem)
            await ctx.send("New element: " + out_string + " :new:")
    else:
        await ctx.send("No active combo!")


@client.command(aliases=["bag", "elems"])
async def inv(ctx):
    pages = []
    k = 1
    temp = dpymenus.Page()
    inv = user_dictionary[ctx.message.author.id].inventory
    temp.title = "{}'s Inventory ({} elements)".format(ctx.message.author.name, len(inv))
    out_str = ""
    for i in range(len(inv)):
        out_str += str(inv[i]) + "\n"
        if i > k * 30:
            k += 1
            temp.description = out_str
            pages.append(temp)
            out_str = ""
            temp = dpymenus.Page()
            temp.title = "{}'s Inventory ({} elements)".format(ctx.message.author.name, len(inv))
    if k == 1:
        temp.description = out_str
        pages.append(temp)
        temp = dpymenus.Page()
        temp.title = "{}'s Inventory ({} elements)".format(ctx.message.author.name, len(inv))
        temp.description = "You don't have more elements bud!"
        pages.append(temp)
    msg = dpymenus.PaginatedMenu(ctx)
    msg.add_pages(pages)
    await msg.open()

# Live storage of elements and combinations. Will update and save to Firebase regularly.
element_dictionary = {}
element_index = {}
combo_dictionary = {}
last_combo_dictionary = {}
category_dictionary = {0: default}
user_dictionary = {}
kaazikin = config.get("kaazikin.id").data

# Default elements for initial testing
element_dictionary[0] = Element([], 0, "Water", 0x4a8edf, datetime.datetime(2020, 10, 16, 0, 0, 0), 0, 1,
                                "https://vignette.wikia.nocookie.net/avatar/images/5/50/Waterbending_emblem.png/"
                                + "revision/latest?cb=20130729182922", 0,
                                "A colorless, transparent, odorless liquid that forms the seas, lakes, rivers, "
                                + "and rain and is the basis of the fluids of living organisms.", int(kaazikin),
                                starter)
element_dictionary[1] = Element([], 1, "Earth", 0x764722, datetime.datetime(2020, 10, 16, 0, 0, 0), 0, 1,
                                "https://vignette.wikia.nocookie.net/avatar/images/e/e4/Earthbending_emblem.png/"
                                + "revision/latest?cb=20130729200732", 0,
                                "The substance of the land surface; soil.", int(kaazikin), starter)
element_dictionary[2] = Element([], 2, "Fire", 0xfe5913, datetime.datetime(2020, 10, 16, 0, 0, 0), 0, 1,
                                "https://vignette.wikia.nocookie.net/avatar/images/4/4b/"
                                + "Firebending_emblem.png/revision/latest?cb=20130729203233", 0,
                                "Combustion or burning, in which substances combine chemically with oxygen from the air"
                                + " and typically give out bright light, heat, and smoke.", int(kaazikin), starter)
element_dictionary[3] = Element([], 3, "Air", 0xfffce0, datetime.datetime(2020, 10, 16, 0, 0, 0), 0, 1,
                                "https://vignette.wikia.nocookie.net/avatar/images/8/82/Airbending_emblem.png/revision/"
                                + "latest?cb=20130729210446", 0,
                                "The invisible gaseous substance surrounding the earth, "
                                + "a mixture mainly of oxygen and nitrogen.", int(kaazikin), starter)

default_inventory = [element_dictionary[0], element_dictionary[1], element_dictionary[2], element_dictionary[3]]

# Index elements for access by number
for x in range(len(element_dictionary)):
    element_index[element_dictionary[x].name] = x
    print("Indexed element " + str(x) + " " + element_dictionary[x].name)

rand = random.Random()
rand.seed()

# Run the bot
client.run(config.get("discord.token").data)
