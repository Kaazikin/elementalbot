# TODO Implement element combinations
# TODO Personal inventory
# TODO Add Firebase backup
# TODO Fix <2 combo with elements that have been used in other combos
# TODO Fix combo count incrementing
# TODO Fix new element output string

import discord
import math
import pyrebase
from jproperties import Properties
from discord.ext import commands, tasks
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
    def __init__(self, ID, output, inputs):
        self.ID = ID
        self.output = output
        self.inputs = sorted(inputs, key=sort_element_id)

    def compare_input(self, other):
        for e in self.inputs:
            if e not in other.inputs:
                return False
        return True

    def get_generation(self):
        print([i.generation for i in self.inputs])
        return max([i.generation for i in self.inputs])

    def __repr__(self):
        return "Combination({}, {}, {}, {})".format(self.ID, self.output, self.inputs, self.get_generation())


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
            return self.combinations[0].get_generation() + 1
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


client = commands.Bot(command_prefix='!')
config = Properties()

# Load config
with open('application.properties', 'rb') as config_file:
    config.load(config_file)


# Log in confirmation
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Game("Looking for #play7"))


# sends all info of an element as an embed.
# TODO: Fix multi element combos. Start with the embed.
@client.command()
async def info(ctx, *element):
    element = " ".join(element)
    try:
        if element[0] == "#":
            current = element_dictionary[int(element[1:])]
        else:
            current = element_dictionary[element_index[element.capitalize()]]
        output = discord.Embed()
        output.title = "Element Info: " + current.name + " (#" + str(current.id) + ")"
        output.description = current.description
        output.colour = discord.Colour(current.colour)
        output.add_field(name="Created By:", value=str(client.get_user(current.creator)), inline=True)
        output.add_field(name="Created On:", value=str(current.creationdate), inline=True)
        output.add_field(name="Used in:", value=str(current.usecount), inline=True)
        output.add_field(name="Made with:", value=str(current.get_combination_count()), inline=True)
        output.add_field(name="Unlocked by ", value=str(current.unlockedcount), inline=True)
        output.add_field(name="Category:", value=current.category.name, inline=True)
        output.add_field(name="Generation Number:", value=str(current.get_generation()), inline=True)
        await ctx.send(content="", embed=output)
    except KeyError:
        await ctx.send("Invalid element.")


# Command to combine elements.
@client.command()
async def add(ctx, elements):
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
            # TODO Fix this check
            curr = element_dictionary[element_index[e.capitalize()]]
            if e.capitalize() != curr.name:
                elements_valid = False
            else:
                stored_elems.append(curr)
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
                await ctx.send("You created " + combo.output.name + ".")
            else:
                last_combo_dictionary[ctx.message.author] = tempcombo
                await ctx.send("This combo does not exist. Use !suggest to suggest a combo.")
                # TODO Clean this up
        else:
            await ctx.send("Invalid element.")
    else:
        await ctx.send("Invalid inputs.")


# Adds combinations & new elements
@client.command()
async def suggest(ctx, *element):
    # TODO Voting
    element = [e.capitalize() for e in element]
    if ctx.message.author in last_combo_dictionary.keys():
        if " ".join(element) in element_index.keys():
            i = element_index[" ".join(element)]
            out_elem = element_dictionary[i]
            curr = last_combo_dictionary[ctx.message.author]
            j = len(combo_dictionary) - 1
            out_combo = Combination(j, out_elem, curr.inputs)
            combo_dictionary[j] = out_combo
            element_dictionary[element_index[i]].add_combo(combo_dictionary[j])
            out_string = ""

            # TODO Put in combo thing

            for item in curr.inputs:
                out_string += item.name
                if item != curr.inputs[len(curr.inputs) - 1]:
                    out_string += " + "
                else:
                    out_string += " = " + out_elem.name
            await ctx.send("New combination: " + out_string + " :new:")
        else:
            curr = last_combo_dictionary[ctx.message.author]
            j = len(combo_dictionary)

            # TODO Fix Colours

            elem_colour = 0x000000
            out_elem = Element([], len(element_dictionary), " ".join(element), colour=elem_colour,
                               creationdate=datetime.datetime.now(), creator=ctx.message.author.id)

            element_dictionary[out_elem.id] = out_elem
            element_index[out_elem.name] = out_elem.id
            out_combo = Combination(j, element_dictionary[out_elem.id], curr.inputs)

            element_dictionary[out_elem.id].add_combo(out_combo)
            combo_dictionary[j] = out_combo

            for c in range(len(combo_dictionary)):
                print(combo_dictionary[c])

            out_string = ""
            for item in curr.inputs:
                out_string += item.name
                if item != curr.inputs[len(curr.inputs) - 1]:
                    out_string += " + "
                else:
                    out_string += " = " + out_elem.name

            await ctx.send("New element: " + out_string + " :new:")
    else:
        await ctx.send("No active combo!")


# Live storage of elements and combinations. Will update and save to Firebase regularly.
element_dictionary = {}
element_index = {}
combo_dictionary = {}
last_combo_dictionary = {}
kaazikin = config.get("kaazikin.id").data
print(kaazikin)

# Default elements for initial testing
element_dictionary[0] = Element([], 0, "Water", 0x4a8edf, datetime.datetime(2020, 10, 16, 0, 0, 0, 0), 1, 1, "", 0,
                                "A colorless, transparent, odorless liquid that forms the seas, lakes, rivers, "
                                + "and rain and is the basis of the fluids of living organisms.", int(kaazikin),
                                starter)
element_dictionary[1] = Element([], 1, "Earth", 0x764722, datetime.datetime(2020, 10, 16, 0, 0, 0, 0), 1, 1, "", 0,
                                "The substance of the land surface; soil.", int(kaazikin), starter)
element_dictionary[2] = Element([], 2, "Fire", 0xfe5913, datetime.datetime(2020, 10, 16, 0, 0, 0, 0), 0, 1, "", 0,
                                "Combustion or burning, in which substances combine chemically with oxygen from the air"
                                + " and typically give out bright light, heat, and smoke.", int(kaazikin), starter)
element_dictionary[3] = Element([], 3, "Air", 0xfffce0, datetime.datetime(2020, 10, 16, 0, 0, 0, 0), 0, 1, "", 0,
                                "The invisible gaseous substance surrounding the earth, "
                                + "a mixture mainly of oxygen and nitrogen.", int(kaazikin), starter)
# element_dictionary[4] = Element([], 4, "Mud", 0x968050, datetime.date.today(), 0, 1, creator=int(kaazikin))

# Testing with dummy combo.
# combo_dictionary[0] = Combination(0, element_dictionary[4], [element_dictionary[0], element_dictionary[1]])
# element_dictionary[4].combinations = [combo_dictionary[0]]

# Index elements for access by number
for x in range(len(element_dictionary)):
    element_index[element_dictionary[x].name] = x
    print("Indexed element " + str(x) + " " + element_dictionary[x].name)

# Run the bot
client.run(config.get("discord.token").data)
