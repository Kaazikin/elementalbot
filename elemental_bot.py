# TODO Implement element combinations
# TODO Personal inventory
# TODO Add Firebase backup
import discord
import pyrebase
from jproperties import Properties
from discord.ext import commands, tasks
import datetime


# Calculates generation
def min_generation(combinations):
    # TODO Implement min_generation
    return 0


# Will fill dictionaries with Firebase data
def populate_dictionaries():
    pass


class Category:
    def __init__(self, ID, name, desc, colour=0x000000, imageurl = ""):
        self.ID = ID
        self.name = name
        self.desc = desc
        self.colour = colour
        self.imageurl = imageurl


class Combination:
    def __init__(self, ID, output, **inputs):
        self.ID = ID
        self.output = output
        self.inputs = inputs


default = Category(0, "Core Elements", "These are the starter elements")


class Element:
    def __init__(self, combinations, ID, name, colour=0x000000, creationdate=datetime.date.today(), usecount=0,
                 unlockedcount=1, imageurl="", generation=-1, description="No note.", creator=None, category=default):
        self.combinations = combinations
        self.ID = ID
        self.name = name
        self.creationdate = creationdate
        self.colour = colour
        self.description = description
        self.imageurl = imageurl
        self.usecount = usecount
        self.unlockedcount = unlockedcount
        self.combinationcount = len(combinations)
        self.creator = creator
        if generation == -1:
            self.generation = min_generation(combinations)
        else:
            self.generation = generation

        self.category = category


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
        output.title = "Element Info: " + current.name
        output.description = current.description
        output.colour = discord.Colour(current.colour)
        output.add_field(name="Created By:", value=str(client.get_user(current.creator)), inline=True)
        output.add_field(name="Created On:", value=str(current.creationdate), inline=True)
        output.add_field(name="Used in:", value=str(current.usecount), inline=True)
        output.add_field(name="Made with:" , value=str(current.combinationcount), inline=True)
        output.add_field(name="Unlocked by ", value=str(current.unlockedcount), inline=True)
        output.add_field(name="Category:", value=current.category.name, inline=True)
        output.add_field(name="Generation Number:", value=str(current.generation), inline=True)
        await ctx.send(content="", embed=output)
    except KeyError:
        await ctx.send("Invalid element.")

# Live storage of elements and combinations. Will update and save to Firebase regularly.
elementdictionary = {}
elementindex = {}
combodictionary = {}
kaazikin = config.get("kaazikin.id").data
print(kaazikin)


# Default elements for initial testing
elementdictionary[0] = Element([], 0, "Water", 0x4a8edf, datetime.date.today(), 0, 1, "", 0,
                               "A colorless, transparent, odorless liquid that forms the seas, lakes, rivers, "
                               + "and rain and is the basis of the fluids of living organisms.", int(kaazikin))
elementdictionary[1] = Element([], 1, "Earth", 0x764722, datetime.date.today(), 0, 1, "", 0,
                               "The substance of the land surface; soil.", int(kaazikin))
elementdictionary[2] = Element([], 2, "Fire", 0xfe5913, datetime.date.today(), 0, 1, "", 0,
                               "Combustion or burning, in which substances combine chemically with oxygen from the air "
                               + "and typically give out bright light, heat, and smoke.", int(kaazikin))
elementdictionary[3] = Element([], 3, "Air", 0xfffce0, datetime.date.today(), 0, 1, "", 0,
                               "The invisible gaseous substance surrounding the earth, "
                               + "a mixture mainly of oxygen and nitrogen.", int(kaazikin))

# Index elements for access by number
for x in range(len(elementdictionary)):
    elementindex[elementdictionary[x].name] = x
    print("Indexed element " + str(x) + " " + elementdictionary[x].name)

# Run the bot
client.run(config.get("discord.token").data)

