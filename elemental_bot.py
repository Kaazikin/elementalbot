# TODO Add Firebase backup
# TODO Sorting inventory
# TODO Sign
# TODO Add image
# TODO Unlocked by numbers
# TODO Hints
# TODO Reset inventory
# TODO Plurals
# TODO Pattern matching in on_message
# TODO Rewrite voting
import discord
import re
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
        return self.id == other.id and self.output == other.output and self.inputs == other.inputs

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

    def has_element(self, elem):
        return elem in self.inventory

    def __repr__(self):
        return "User: " + self.id


class Vote:
    def __init__(self, message_id, poll_type, creator_id, element=None, category=None, colour=None, note=None,
                 image=None, combinations=None, new_cat=None):
        self.message_id = message_id
        self.poll_type = poll_type
        self.creator_id = creator_id
        self.element = element
        self.category = category
        self.colour = colour
        self.note = note
        self.image = image
        self.combinations = combinations

        self.voters = []
        self.value = 0

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
            user_dictionary[user.id] = User(user.id, default_inventory[:])
    await client.change_presence(activity=discord.Game(random.choice(status_list)))
    random_status.start()


@client.event
async def on_message(message):

    if str(message.channel.id) in config.get("channel.play").data.split(", "):
        if "!" not in message.content:
            if "+" in message.content or "," in message.content:
                ctx = await client.get_context(message)
                await add(ctx=ctx, elements=message.content)

    await client.process_commands(message)


# Creates inventory for new members
@client.event
async def on_member_join(member):
    if member.id not in user_dictionary.keys():
        user_dictionary[member.id] = User(member.id, default_inventory[:])


# Voting reaction handling
@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.channel.id == int(config.get("channel.voting").data) and user != client.user:
        if reaction.message.id in vote_dictionary.keys():
            current_vote = vote_dictionary[reaction.message.id]
            if reaction.emoji.name == "eodr_upvote" and user.id not in current_vote.voters:

                current_vote.value += 1
                current_vote.voters.append(user.id)

                # Handling for passing the vote threshold for specific vote types
                if current_vote.value >= 2:
                    if current_vote.poll_type == "combination":  # If voting for a combination

                        out_combo = current_vote.combinations
                        out_combo.id = len(combo_dictionary)
                        combo_dictionary[out_combo.id] = out_combo
                        element_dictionary[out_combo.output.id].add_combo(combo_dictionary[out_combo.id])

                        if element_dictionary[out_combo.output.id] not in \
                                user_dictionary[current_vote.creator_id].inventory:
                            user_dictionary[current_vote.creator_id].add_inventory(element_dictionary
                                                                                            [out_combo.output.id])

                        element_unique = []
                        for element in out_combo.inputs:
                            if element not in element_unique:
                                element_unique.append(element)

                        for element in element_unique:
                            element.usecount += 1

                        await client.get_channel\
                            (int(config.get("channel.announcement").data)).\
                            send(":new: Combination **{}** *(Suggested by {})*".format(out_combo.output.name,
                                 client.get_user(current_vote.creator_id).mention))

                        vote_count_dictionary[current_vote.creator_id] -= 1
                        vote_dictionary.pop(reaction.message.id)
                        await reaction.message.delete()
                        for votes in vote_dictionary.keys():
                            if vote_dictionary[votes].combinations.inputs == out_combo.inputs:
                                vote_count_dictionary[vote_dictionary[votes].pop().creator_id] -= 1
                                await reaction.message.channel.get_message(votes).delete()

                    elif current_vote.poll_type == "element":  # If voting for a new element
                        out_elem = current_vote.element
                        curr = current_vote.combinations
                        j = len(combo_dictionary)
                        i = len(element_dictionary)
                        out_elem.id = i
                        element_dictionary[out_elem.id] = out_elem
                        element_index[out_elem.name.upper()] = out_elem.id
                        out_combo = Combination(j, element_dictionary[out_elem.id], curr.inputs)

                        element_dictionary[out_elem.id].add_combo(out_combo)
                        combo_dictionary[j] = out_combo
                        user_dictionary[current_vote.creator_id].add_inventory(out_elem)

                        element_unique = []
                        for element in out_combo.inputs:
                            if element not in element_unique:
                                element_unique.append(element)

                        for element in element_unique:
                            element.usecount += 1

                        await client.get_channel(int(config.get("channel.announcement").data)).\
                            send(":new: Element **{}** *(Suggested by {})*".format(out_elem.name,
                                client.get_user(current_vote.creator_id).mention))

                        vote_count_dictionary[current_vote.creator_id] -= 1
                        vote_dictionary.pop(reaction.message.id)
                        await reaction.message.delete()
                        for votes in vote_dictionary.keys():
                            if vote_dictionary[votes].combinations.compare_input(out_combo):
                                vote_count_dictionary[vote_dictionary[votes].pop().creator_id] -= 1
                                await reaction.message.channel.get_message(votes).delete()
                            elif vote_dictionary[votes].element.name == out_elem.name:
                                vote_dictionary[votes].element = out_elem

                    elif current_vote.poll_type == "colour":  # If voting to change colour
                        e = current_vote.element
                        c = current_vote.colour
                        e.colour = int(c, 16)
                        await client.get_channel(int(config.get("channel.announcement").data)). \
                            send(":paintbrush: Colour Change: **{}** *(Suggested by {})*".format(e.name,
                                client.get_user(current_vote.creator_id).mention))

                        vote_count_dictionary[current_vote.creator_id] -= 1
                        vote_dictionary.pop(reaction.message.id)
                        await reaction.message.delete()

                    elif current_vote.poll_type == "category":
                        e = current_vote.element
                        c = current_vote.category
                        if current_vote.new_cat:
                            c.id = len(category_dictionary)
                            category_dictionary[c.id] = c
                        e.category = c
                        await client.get_channel(int(config.get("channel.announcement").data)). \
                            send(":card_box: Category Change: **{}** *(Suggested by {})*".format(e.name,
                                 client.get_user(current_vote.creator_id).mention))

                        vote_count_dictionary[current_vote.creator_id] -= 1
                        vote_dictionary.pop(reaction.message.id)
                        await reaction.message.delete()

            elif reaction.emoji.name == "eodr_downvote" and user.id not in current_vote.voters:
                current_vote.value -= 1
                current_vote.voters.append(user.id)
                if user.id == current_vote.creator_id or current_vote.value <= -2:
                    vote_count_dictionary[vote_dictionary.pop(reaction.message.id).creator_id] -= 1
                    await reaction.message.delete()


@client.event
async def on_reaction_remove(reaction, user):
    if reaction.message.channel.id == int(config.get("channel.voting").data) and user != client.user:
        if reaction.message.id in vote_dictionary.keys():
            current_poll = vote_dictionary[reaction.message.id]
            if reaction.emoji == UPVOTE and user.id in vote_dictionary[reaction.message.id][4]:
                current_poll.value -= 1
                vote_dictionary[reaction.message.id][4].remove(user.id)
            elif reaction.emoji == DOWNVOTE and user.id in vote_dictionary[reaction.message.id][4]:
                vote_dictionary[reaction.message.id][0] += 1
                vote_dictionary[reaction.message.id][4].remove(user.id)


# Changes bot presence every twenty minutes.
@tasks.loop(minutes=20.0)
async def random_status():
    await client.change_presence(activity=discord.Game(random.choice(status_list)))


# sends all info of an element as an embed.
@client.command(aliases=["?"], help="Returns information on an element.")
async def info(ctx, *element):
    element = " ".join(element).upper()
    try:
        if element[0] == "#":
            current = element_dictionary[int(element[1:])]
        else:
            current = element_dictionary[element_index[element]]
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
        output.add_field(name="Unlocked:", value=str(current in user_dictionary[ctx.message.author.id].inventory),
                         inline=True)
        await ctx.send(content="", embed=output)
    except KeyError:
        await ctx.send("Invalid element.")


# Command to combine elements.
@client.command(aliases=["+"], help="Combines two to nine (inclusive) elements together.")
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
            if e.upper() in map(lambda k: k.upper(), element_index.keys()):
                curr = element_dictionary[element_index[e.upper()]]
                if curr not in user_dictionary[ctx.message.author.id].inventory:
                    elements_valid = False
                    break
                stored_elems.append(curr)
            else:
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
                if combo.output in user_dictionary[ctx.message.author.id].inventory:
                    await ctx.send("{} You made **{}**, but already have it :blue_circle:".format(ctx.message.author.
                                                                                                  mention, combo.
                                                                                                  output.name))
                else:
                    user_dictionary[ctx.message.author.id].add_inventory(combo.output)
                    await ctx.send("{} You made {} :new:".format(ctx.message.author.mention, combo.output.name))
            else:
                last_combo_dictionary[ctx.message.author] = tempcombo
                await ctx.send(ctx.message.author.mention +
                               " This combo does not exist. :red_circle:\nUse !suggest to suggest a combo.")
        else:
            await ctx.send("Invalid element.")
    else:
        await ctx.send("Invalid inputs.")


# Adds combinations & new elements
@client.command(aliases=["s"], help="Suggest a new element or combination.")
async def suggest(ctx, *, element):
    element = element.strip()
    element_length = len(element)
    element_original = element
    element = element[0].upper()
    element_valid = True
    for c in range(1, element_length):
        element += element_original[c]
    for e in element:
        if len(e) > 65 or "+" in e or "," in e or "!" in e:
            element_valid = False
    if ctx.message.author in last_combo_dictionary.keys():
        if element.upper() in element_index.keys():  # New combination
            i = element_index[element.upper()]
            out_elem = element_dictionary[i]
            curr = last_combo_dictionary.pop(ctx.message.author, None)
            j = len(combo_dictionary)
            out_combo = Combination(j, out_elem, curr.inputs)

            # Embed building for vote
            out_string = ""
            used_elems = []
            for z in range(len(curr.inputs)):
                out_string += curr.inputs[z].name
                if curr.inputs[z] not in used_elems:
                    used_elems.append(curr.inputs[z])
                if z != len(curr.inputs) - 1:
                    out_string += " + "
                else:
                    out_string += " = " + out_elem.name

            # Poll count restriction
            try:
                can_add_poll = (vote_count_dictionary[ctx.message.author.id] <= 10)
            except KeyError:
                can_add_poll = True

            for poll in vote_dictionary:
                if vote_dictionary[poll].poll_type == "combination":
                    if vote_dictionary[poll].combinations.compare_input(out_combo) and \
                            vote_dictionary[poll].element == out_elem:
                        can_add_poll = False

            if can_add_poll:
                embed = discord.Embed()
                embed.title = ":new: Combination"
                embed.description = "{}\nSuggested by {}".format(out_string, ctx.message.author.mention)
                embed.colour = int(hex(rand.randint(0, 16777215)), 16)
                embed.set_footer(text="Your vote can be changed, but will not be counted until you remove your other"
                                      + " vote. Creators may downvote to delete.")
                message = await client.get_channel(int(config.get("channel.voting").data)).send(content="", embed=embed)

                vote_dictionary[message.id] = Vote(message.id, "combination", element=out_elem, combinations=out_combo,
                                                   creator_id=ctx.message.author.id)

                try:
                    vote_count_dictionary[ctx.message.author.id] += 1
                except KeyError:
                    vote_count_dictionary[ctx.message.author.id] = 1

                await message.add_reaction(UPVOTE)
                await message.add_reaction(DOWNVOTE)

                await ctx.send("Poll sent! {}".format(ctx.message.author.mention))
            else:
                await ctx.send("You cannot submit this poll!")

        elif element_valid:  # New Element
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

            out_string = ""
            used_elems = []
            for z in range(len(curr.inputs)):
                out_string += curr.inputs[z].name
                if curr.inputs[z] not in used_elems:
                    used_elems.append(curr.inputs[z])
                if z != len(curr.inputs) - 1:
                    out_string += " + "
                else:
                    out_string += " = " + out_elem.name

            try:
                can_add_poll = (vote_count_dictionary[ctx.message.author.id] <= 10)
            except KeyError:
                can_add_poll = True

            for poll in vote_dictionary:
                if vote_dictionary[poll].poll_type == "element":
                    if vote_dictionary[poll].combinations.compare_input(curr) or \
                            vote_dictionary[poll].element.name == out_elem.name:
                        can_add_poll = False

            if can_add_poll:
                embed = discord.Embed()
                embed.title = ":new: Element"
                embed.description = "{}\nSuggested by {}".format(out_string, ctx.message.author.mention)
                embed.colour = out_elem.colour
                embed.set_footer(text="Your vote can be changed, but will not be counted until you remove your other"
                                      + " vote. Creators may downvote to delete.")
                message = await client.get_channel(int(config.get("channel.voting").data)).send(content="", embed=embed)

                vote_dictionary[message.id] = Vote(message.id, "element", element=out_elem, combinations=curr,
                                                   creator_id=ctx.message.author.id)

                try:
                    vote_count_dictionary[ctx.message.author.id] += 1
                except KeyError:
                    vote_count_dictionary[ctx.message.author.id] = 1

                await message.add_reaction(UPVOTE)
                await message.add_reaction(DOWNVOTE)

                await ctx.send("Poll sent! {}".format(ctx.message.author.mention))
            else:
                await ctx.send("You cannot submit this poll!")
        else:
            await ctx.send("Invalid element name! :no_entry_sign:")
    else:
        await ctx.send("No active combo!")


# Displays the inventory to a user.
@client.command(aliases=["bag", "elems"], help="Displays user inventory.")
async def inv(ctx):
    pages = []
    k = 1
    temp = dpymenus.Page()
    inv = user_dictionary[ctx.message.author.id].inventory
    temp.title = "{}'s Inventory ({} elements)".format(ctx.message.author.name, len(inv))
    out_str = ""
    for i in range(len(inv)):
        out_str += str(inv[i]) + "\n"
        if i >= k * 30:
            k += 1
            temp.description = out_str
            pages.append(temp)
            out_str = ""
            temp = dpymenus.Page()
            temp.title = "{}'s Inventory ({} elements)".format(ctx.message.author.name, len(inv))
    if out_str != "":
        temp.description = out_str
        pages.append(temp)
    temp = dpymenus.Page()
    temp.title = "{}'s Inventory ({} elements)".format(ctx.message.author.name, len(inv))
    temp.description = "You don't have more elements bud!"
    pages.append(temp)
    msg = dpymenus.PaginatedMenu(ctx)
    msg.add_pages(pages)
    await msg.open()


# Change colour of element
@client.command(aliases=["color"], help="Change the colour of an element. No vote required if you created element.\n" +
                "Colour must be hex code. If your element is more than one word, put it in quotation marks. Do not use"
                + "# sign before colour name.")
async def colour(ctx, element, colour):
    if element.upper() in element_index.keys():
        e = element_dictionary[element_index[element.upper()]]
        if re.match("^([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", colour) is None:
            await ctx.send("Invalid hex.")
        else:
            if e.creator == ctx.message.author.id:
                e.colour = int(colour, 16)
                await ctx.send("Changed colour! {}".format(ctx.message.author.mention))
            elif user_dictionary[ctx.message.author.id].has_elem(e):
                try:
                    can_add_poll = (vote_count_dictionary[ctx.message.author.id] <= 10)
                except KeyError:
                    can_add_poll = True

                for poll in vote_dictionary:
                    if vote_dictionary[poll].poll_type == "colour":
                        if vote_dictionary[poll].element == element and vote_dictionary[poll].creator_id == \
                                ctx.message.author.id:
                            can_add_poll = False
                if can_add_poll:
                    embed = discord.Embed()
                    embed.title = ":paintbrush: Colour Change: " + e.name
                    embed.description = "Old Colour: {}\nNew Colour: {}\nSuggested by {}".format(e.colour, colour,
                                                                                                 ctx.message.author.
                                                                                                 mention)
                    embed.colour = colour
                    embed.set_footer(text="Your vote can be changed but will not be counted until you remove your other"
                                          + " vote. Creators may downvote to delete.")
                    message = await client.get_channel(int(config.get("channel.voting").data)).send(content="",
                                                                                                    embed=embed)

                    vote_dictionary[message.id] = Vote(message.id, "colour", element=e, colour=colour, creator_id=
                                                       ctx.message.author.id)

                    try:
                        vote_count_dictionary[ctx.message.author.id] += 1
                    except KeyError:
                        vote_count_dictionary[ctx.message.author.id] = 1

                    await message.add_reaction(UPVOTE)
                    await message.add_reaction(DOWNVOTE)

                    await ctx.send("Poll sent! {}".format(ctx.message.author.mention))
                else:
                    await ctx.send("You cannot submit this poll!")
            else:
                await ctx.send("You don't have that element.")

    else:
        await ctx.send("Invalid element.")


@client.command(help="Add a category to an element.\n Put quotations around element and category names if longer than"
                + " one word each. e.g. !category \"A A\" \"B B\"")
async def category(ctx, element, category):

    category = category.strip()
    cat_length = len(category)
    cat_original = category
    category = category[0].upper()

    for character in range(1, cat_length):
        category += cat_original[character]

    if element.upper() in element_index.keys():
        e = element_dictionary[element_index[element.upper()]]
        category_exists = False
        c = None
        c_index = -1
        for i in category_dictionary.keys():
            if category_dictionary[i].name.upper == category.upper():
                category_exists = True
                c = category_dictionary[i]
                c_index = i
                break
        if not category_exists:
            c = Category(len(category_dictionary), category, desc="")
        try:
            can_add_poll = (vote_count_dictionary[ctx.message.author.id] <= 10) and \
                           user_dictionary[ctx.message.author.id].has_element(e)
        except KeyError:
            can_add_poll = True and user_dictionary[ctx.message.author.id].has_element(e)

        for poll in vote_dictionary:
            if vote_dictionary[poll][1] == "category":
                if vote_dictionary[poll][2] == e and vote_dictionary[poll][5] == ctx.message.author.id:
                    can_add_poll = False
        if can_add_poll:
            embed = discord.Embed()
            embed.title = ":card_box: Category Change: " + e.name
            embed.description = "Old Category: {}\nNew Category: {}\nSuggested by {}".format(e.category.name, c.name,
                                                                                           ctx.message.author.mention)
            embed.colour = e.colour
            embed.set_footer(text="Your vote can be changed, but will not be counted until you remove your other"
                                  + " vote. Creators may downvote to delete.")
            message = await client.get_channel(int(config.get("channel.voting").data)).send(content="", embed=embed)

            vote_dictionary[message.id] = Vote(message.id, "category", creator_id=ctx.message.author.id, element=e,
                                               category=c, new_cat= not category_exists)
            try:
                vote_count_dictionary[ctx.message.author.id] += 1
            except KeyError:
                vote_count_dictionary[ctx.message.author.id] = 1

            await message.add_reaction(UPVOTE)
            await message.add_reaction(DOWNVOTE)

            await ctx.send("Poll sent! {}".format(ctx.message.author.mention))
        else:
            await ctx.send("You cannot submit this poll!")
    else:
        await ctx.send("Invalid element!")

# Live storage of elements and combinations. Will update and save to Firebase regularly.
element_dictionary = {}
element_index = {}
combo_dictionary = {}

# Stores the last combo made in !add.
last_combo_dictionary = {}

# Stores categories
category_dictionary = {0: default, 1: starter}

# Stores users
user_dictionary = {}

# Stores votes
vote_dictionary = {}
vote_count_dictionary = {}

kaazikin = config.get("kaazikin.id").data

UPVOTE = "<:eodr_upvote:769286560188989481"
DOWNVOTE = "<:eodr_downvote:769286560134332497"

# Stores statuses
status_list = ["Looking for play7", "Submitting a spelling combination", "Adding 1000 numbers by hand", "Asking Kaaz " +
               "to enable testing", "Doodling some gods", "Stepping on small alchemists",
               "with chains that won'T continue", "B L O O P", "Praying to Egg gods", "with a water melon melon melon"]

# Default elements for initial testing
# TODO Replace these hardcoded elements with elements loaded from file / firebase
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
    element_index[element_dictionary[x].name.upper()] = x
    print("Indexed element " + str(x) + " " + element_dictionary[x].name)

rand = random.Random()
rand.seed()

# Run the bot
client.run(config.get("discord.token").data)
