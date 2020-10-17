# TODO Implement element combinations
# TODO Personal inventory
# TODO Add Firebase backup
import discord
import pyrebase
from jproperties import Properties
from discord.ext import commands, tasks
import datetime


# Calculates generation
def min_generation(combination):
    return min(i.generation for i in combination.inputs) + 1


# Will fill dictionaries with Firebase data
def populate_dictionaries():
    pass


def sort_element_id(element):
    return element.id


class Category:
    def __init__(self, id, name, desc, colour=0x000000, imageurl = ""):
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
        return self.inputs.sort() == other.inputs.sort()

    def get_generation(self):
        return max(i for i in self.inputs)


default = Category(0, "Core Elements", "These are the starter elements")


class Element:
    def __init__(self, combinations, id, name, colour=0x000000, creationdate=datetime.date.today(), usecount=0,
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

    def get_generation(self):
        if self.generation == -1:
            return min_generation(self.combinations[0].get_generation())
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
@client.command()
async def info(ctx, element):
    try:
        if element[0] == "#":
            current = elementdictionary[int(element[1:])]
        else:
            current = elementdictionary[elementindex[element.capitalize()]]
        output = discord.Embed()
        output.title = "Element Info: " + current.name + " (#" + str(current.id) + ")"
        output.description = current.description
        output.colour = discord.Colour(current.colour)
        output.add_field(name="Created By:", value=str(client.get_user(current.creator)), inline=True)
        output.add_field(name="Created On:", value=str(current.creationdate), inline=True)
        output.add_field(name="Used in:", value=str(current.usecount), inline=True)
        output.add_field(name="Made with:" , value=str(current.get_combination_count()), inline=True)
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
            curr = elementdictionary[elementindex[e.capitalize()]]
            if e.capitalize() != curr.name:
                elements_valid = False
                stored_elems.append(curr)
        if elements_valid:
            tempcombo = Combination(-1, None, stored_elems)
            combo_found = False
            combo = None
            for curr_combo in combodictionary:
                if tempcombo.compare_input(combodictionary[curr_combo]):
                    combo_found = True
                    combo = combodictionary[curr_combo]
                    break
            if combo_found:
                # TODO Inventory stuff, validation stuff
                await ctx.send("You created " + combo.output.name + ".")
            else:
                await ctx.send("This combo does not exist. Use !suggest to suggest a combo.")
                # TODO Clean this up
        else:
            await ctx.send("Invalid element.")
    else:
        await ctx.send("Invalid inputs.")

# Live storage of elements and combinations. Will update and save to Firebase regularly.
elementdictionary = {}
elementindex = {}
combodictionary = {}
kaazikin = config.get("kaazikin.id").data
print(kaazikin)


# Default elements for initial testing
elementdictionary[0] = Element([], 0, "Water", 0x4a8edf, datetime.date.today(), 1, 1, "", 0,
                               "A colorless, transparent, odorless liquid that forms the seas, lakes, rivers, "
                               + "and rain and is the basis of the fluids of living organisms.", int(kaazikin))
elementdictionary[1] = Element([], 1, "Earth", 0x764722, datetime.date.today(), 1, 1, "", 0,
                               "The substance of the land surface; soil.", int(kaazikin))
elementdictionary[2] = Element([], 2, "Fire", 0xfe5913, datetime.date.today(), 0, 1, "", 0,
                               "Combustion or burning, in which substances combine chemically with oxygen from the air "
                               + "and typically give out bright light, heat, and smoke.", int(kaazikin))
elementdictionary[3] = Element([], 3, "Air", 0xfffce0, datetime.date.today(), 0, 1, "", 0,
                               "The invisible gaseous substance surrounding the earth, "
                               + "a mixture mainly of oxygen and nitrogen.", int(kaazikin))
elementdictionary[4] = Element([], 4, "Mud", 0x968050, datetime.date.today(), 0, 1, creator=int(kaazikin))

# Testing with dummy combo.
combodictionary[0] = Combination(0, elementdictionary[4], [elementdictionary[0], elementdictionary[1]])
elementdictionary[4].combinations = [combodictionary[0]]

# Index elements for access by number
for x in range(len(elementdictionary)):
    elementindex[elementdictionary[x].name] = x
    print("Indexed element " + str(x) + " " + elementdictionary[x].name)

# Run the bot
client.run(config.get("discord.token").data)

