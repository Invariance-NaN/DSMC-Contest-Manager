
import os
import discord
from running import *
import ast
from subprocess import call
import requests
from discord import app_commands

from contest import Contest
from team import Team
from question import Question
from contestDatabase import ContestDatabase
from customExceptions import *
from contestPeriod import ContestPeriod





# TODO: Fix channel creation!(Still kinda scuffed rn, channels aren't being deleted)









intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# important!
current_guild_id = 624314920158232616



@client.event
async def on_ready():
  client.database = ContestDatabase('password')
  client.something = 0
  #print(await tree.sync(guild=discord.Object(id=current_guild_id)))
  print("Ready!")



 




'''
@tree.command(name = "hello", description = "My first application Command", guild=discord.Object(id=current_guild_id))
async def first_command(interaction):
  await interaction.response.send_message("Hello!")




# unimportant test command.
@tree.command(name = "signin", description = "Signin test", guild=discord.Object(id=current_guild_id))
async def signin(interaction,thing_to_say: str, colors: str):
  await interaction.response.send_message(thing_to_say + str(client.something) + str(interaction.user))
  client.something += 1

@signin.autocomplete("colors")
async def rps_autocomplete(
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        choices = ['Rock', 'Paper', 'Scissors']
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices if current.lower() in choice.lower()
        ]

'''

'''
@tree.command(name = "testtest",description="temporary test", guild=discord.Object(id=current_guild_id))
async def test(interaction):
  await interaction.response.send_message("works!")
'''



# functional
@tree.command(name = "create_contest", description = "Creates a new Contest.",guild=discord.Object(id=current_guild_id))
@app_commands.checks.has_any_role('Olympiad Team', 'Olympiad Manager')
async def create_contest(interaction,name:str,link:str,team_size_limit:int=None,total_teams_limit:int=None):
  newContest = Contest(name.lower(),link,team_size_limit,total_teams_limit)
  await interaction.response.send_message("Contest successfully created!")
  client.database.update_contest(newContest)
  


# functional
async def getContestNames(interaction: discord.Interaction, current:str):
  data = []
  for contestName in client.database.get_all_contest_names():
    data.append(app_commands.Choice(name=contestName.lower(),value=contestName))
  return data



# this command allows a user to register their own team, along with 3 invited members.
@tree.command(name = "register_team", description = "Registers a team into a contest. ",guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
async def register_team(interaction, contest_name: str, team_name: str, member_two: discord.Member = None, member_three: discord.Member = None, member_four: discord.Member = None):

  inviteList = []
  if member_two != None: inviteList.append(member_two)
  if member_three != None: inviteList.append(member_three)
  if member_four != None: inviteList.append(member_four)
  
  contest = client.database.get_contest(contest_name)

  try:
    newTeam = Team(contestInstance = contest,name = team_name, ownerID = interaction.user.id, invitedMemberIDs = [member.id for member in inviteList])
    contest.add_team(newTeam)
    print(newTeam.getData())
    
    await interaction.response.send_message("Team '{teamName}' has been added to the contest with the users {members} invited. In order for them to join your team, they must use /join_team {teamName}.".format(members = [member.display_name for member in inviteList], teamName = team_name))
    
    for member in inviteList:
      channel = await member.create_dm()
      await channel.send("The user {user} has invited you to join the team '{teamName}' for the contest '{contestName}'. In order to join, use '/join_team {teamName}' in the Mathematics Server (it doesn't work within DMs). If you don't want to join, ignore this message.".format(user = interaction.user, contestName = contest.name, teamName = team_name))
    
    client.database.update_contest(contest)
  except WrongPeriodException:
    await interaction.response.send_message("You can only create a team when this contest is in it's signup phase. Sorry!")





async def team_name_autocompletion(interaction: discord.Interaction, current: str):
  contestName = interaction.namespace.contest_name
  contest = client.database.get_contest(contestName)

  team_name_choices = []

  for team in contest.all_teams:
    if interaction.user.id in team.invitedMemberIDs:
      team_name_choices.append(app_commands.Choice(name = team.name.lower(), value = team.name))
  return team_name_choices


# this command allows a user to join a team. @tree.command represents a slash command.
@tree.command(name = "join_team", description = "Join one of the teams you were invited to.", guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames, team_name = team_name_autocompletion)
async def join_team(interaction, contest_name:str, team_name:str):
  contestName = interaction.namespace.contest_name
  contest = client.database.get_contest(contestName)

  try:
    contest.get_team(team_name).addMember(interaction.user.id)
    await interaction.response.send_message("Horray! You have officially joined team {teamName}! to leave, use /leave_current_team.".format(teamName = team_name))
    client.database.update_contest(contest)
  except MemberNotInvitedException:
    await interaction.response.send_message("Hmmm.... It seems that you haven't been invited to this team.", ephemeral = True)
  except MemberInAnotherTeamException:
    await interaction.response.send_message("You've already joined another team! Use /leave_current_team to leave your current team, then use /join_team to join this one.", ephemeral = True)




@tree.command(name = "modify_team_size_limit", description = "Modifies the team size limit for a contest. ",guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
@app_commands.checks.has_any_role('Olympiad Team', 'Olympiad Manager')
async def modify_team_size_limit(interaction, contest_name: str, size_limit: int):
  contest = client.database.get_contest(contest_name)
  contest.teamSizeLimit = size_limit
  client.database.update_contest(contest)

@tree.command(name = "modify_total_teams_limit", description = "Modifies the total teams limit for a contest. ",guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
@app_commands.checks.has_any_role('Olympiad Team', 'Olympiad Manager')
async def modify_team_size_limit(interaction, contest_name: str, teams_limit: int):
  contest = client.database.get_contest(contest_name)
  contest.totalTeamsLimit = teams_limit
  client.database.update_contest(contest)









# untested
@tree.command(name = "leave_current_team", description = "Leaves your current team in the respective contest.", guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
async def leave_current_team(interaction, contest_name: str):
  contest = client.database.get_contest(contest_name)
  user_team = contest.get_team_of_user(interaction.user.id)
  if user_team == None:
    await interaction.response.send_message("Hmmm... You don't seem to be in a team as of now.",ephemeral = True)
  else:
    try:
      user_team.removeMember(interaction.user.id)
      client.database.update_contest(contest)
      await interaction.response.send_message("You have officially left your current team.")
    except OwnerLeaveTeamException:
      await interaction.response.send_message("As the owner of this team, you cannot leave. You must either delete the team or transfer ownership to another person(via the /transfer_ownership command)")
    except:
      await interaction.response.send_message("Looks like something went wrong. Please contact @DanielRocksUrMom to follow up with him(Error code 1)")


# unstested
@tree.command(name = "transfer_ownership", description = "If you are the owner of a team, transfers ownership to another person within your team.", guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
async def leave_current_team(interaction, contest_name: str, new_owner: discord.Member):
  contest = client.database.get_contest(contest_name)
  player_team = contest.get_team_of_user(interaction.user.id)
  if interaction.user.id == player_team.ownerID:
    player_team.transfer_ownership(new_owner.id)
    client.database.update_contest(contest)
    await interaction.response.send_message("Ownership has been successfully transfered to {newOwner}!".format(newOwner = new_owner))
  else:
    await interaction.response.send_message("Sorry, you're not the owner of the team you're in, so you cannot transfer ownership.", ephemeral = True)
  



# untested
@tree.command(name = "unregister_team", description = "Unregisters your team ",guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
async def unregister_team(interaction, contest_name: str):
  contest = client.database.get_contest(contest_name)
  
  user_team = contest.get_team_of_user(interaction.user.id)

  if user_team == None:
    await interaction.response.send_message("Hmm.... You don't seem to be in a team as of now.", ephemeral = True)
  elif user_team.ownerID != interaction.user.id:
    await interaction.response.send_message("Holdup! You can't delete this team, as it was created by someone else. Ask the creator to delete the team. If you want to leave, use /leave_current_team.", ephemeral = True)
  else:
    contest.remove_team(user_team)
    for memberID in user_team.memberIDs:
      channel = await interaction.guild.get_member(memberID).create_dm()
      await channel.send("The original owner of team {teamName} has deleted this team. To sign up for another team, ask another team owner to invite you, then use /join.".format(user = interaction.user, contestName = contest.name, teamName = user_team.name))
    await interaction.response.send_message("Success!")
    client.database.update_contest(contest)




@tree.command(name = "add_question", description = "Adds a question into a contest. Mods only!",guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
@app_commands.checks.has_any_role('Olympiad Team', 'Olympiad Manager')
async def add_question(interaction, contest_name: str, answer: float, points: int, problem_number: int = None):
  contest = client.database.get_contest(contest_name)
  try:
    if problem_number == None:
      contest.add_question(Question(contest,answer,points))
    else:
      contest.add_question(Question(contest,answer,points),problem_number)
    client.database.update_contest(contest)
    await interaction.response.send_message("Success!")
  except WrongPeriodException:
    await interaction.response.send_message("currently, the contest is underway. You cannot add questions at this time.")


# untested
@tree.command(name = "remove_question", description = "Removes a question from a specified contest.",guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
@app_commands.checks.has_any_role('Olympiad Team', 'Olympiad Manager')
async def remove_question(interaction,contest_name: str, question_number: int):
  contest = client.database.get_contest(contest_name)
  try:
    contest.remove_question(question_number)
    client.update_contest(contest)
  except WrongPeriodException:
    await interaction.response.send_message("The competition is underway, so you cannot add or remove questions.")




@tree.command(name = "change_contest_period", description = "changes the period of a contest.", guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
@app_commands.choices(period = [
    app_commands.Choice(name = 'pre-signup', value = 'pre-signup'),
    app_commands.Choice(name = 'signup', value = 'signup'),
    app_commands.Choice(name = 'competition', value = 'competition'),
    app_commands.Choice(name = 'post-competition', value = 'post-competition')
  ])
@app_commands.checks.has_any_role('Olympiad Team', 'Olympiad Manager')
async def change_contest_period(interaction, contest_name: str, period: str):
  if period == 'pre-signup':
    period = ContestPeriod.preSignup
  elif period == 'signup':
    period = ContestPeriod.signup
  elif period == 'competition':
    period = ContestPeriod.competition
  elif period == 'post-competition':
    period = ContestPeriod.postCompetition

  
  contest = client.database.get_contest(contest_name)
  contest.period = period
  client.database.update_contest(contest)
  await interaction.response.send_message("Success! The contest period has been changed to " + str(period))







@tree.command(name = "create_contest_channels", description = "Creates the private channels for all of the teams.",guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
@app_commands.checks.has_any_role('Olympiad Team', 'Olympiad Manager')
async def create_contest_channels(interaction,contest_name:str):
  contest = client.database.get_contest(contest_name)

  for team in contest.all_teams:
    manager_role = discord.utils.get(interaction.guild.roles,name="Olympiad Team")
    admin_role = discord.utils.get(interaction.guild.roles,name="Olympiad Manager")
    overwrites = {
      interaction.guild.default_role: discord.PermissionOverwrite(read_messages = False),
      manager_role: discord.PermissionOverwrite(read_messages = True),
      admin_role: discord.PermissionOverwrite(read_messages = True),
    }
    for memberID in team.memberIDs:
      overwrites[interaction.guild.get_member(memberID)] = discord.PermissionOverwrite(read_messages = True)
    channel = await interaction.guild.create_text_channel(team.name+'-contest-channel',overwrites=overwrites)
    contest.channelIDInfo[team.name] = interaction.channel_id
  
  await interaction.response.send_message("Channels have been opened!.")



# untested.
@tree.command(name = "delete_contest_channels", description = "Deletes all of the contest channels",guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
@app_commands.checks.has_any_role('Olympiad Team', 'Olympiad Manager')
async def delete_contest_channels(interaction,contest_name: str):
  contest = client.database.get_contest(contest_name)
  for team in contest.all_teams:
    await interaction.guild.get_channel(contest.channelIDInfo[team.name]+'-contest-channel').delete()
  
    
  await interaction.response.send_message("All contest channels deleted!.")





@tree.command(name = "answer_question", description = "answer a question on a specific test",guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name=getContestNames)
async def answer_question(interaction,contest_name:str,question_number: int, answer: float):
  try:
    contest = client.database.get_contest(contest_name)
    contest.get_team_of_user(interaction.user.id).answer(contest.get_question(question_number),answer)
    client.database.update_contest(contest)
    await interaction.response.send_message(str(interaction.user) + " has answered question #{questionNumber}!".format(questionNumber = question_number))
  except AnswersAlreadySubmittedException:
    await interaction.response.send_message("Sorry, you have already submitted your answers. Once you submit your answers, you cannot answer anything else.",ephemeral = True)
  except WrongPeriodException:
    await interaction.response.send_message("Sorry, you can't submit any answers right now, as the contest period is not the competition period.",ephemeral = True)
  except:
    await interaction.response.send_message("Sorry, but the contest doesn't have a problem with number " + str(question_number))
  


@tree.command(name = "submit_all_answers", description = "Submits your teams' answers. Once you submit, you CANNOT unsubmit!", guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name = getContestNames)
async def submit_team_answers(interaction, contest_name: str):
  try:
    contest = client.database.get_contest(contest_name)
    player_team = contest.get_team_of_user(interaction.user.id)
    if player_team.ownerID == interaction.user.id:
      player_team.submit_answers()
      client.database.update_contest(contest)
      await interaction.response.send_message("The owner has officially submitted all of their teams' answers!")
    else:
      await interaction.response.send_message("Sorry, you are not the owner, and thus you cannot submit any answers.")
  except WrongPeriodException:
    await interaction.response.send_message("Sorry, but you cannot submit any answers right now, as the contest is not in the competition period.")


@tree.command(name = "all_questions", description = "gets the answer and point value of all of the questions within the specified contest.", guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name = getContestNames)
@app_commands.checks.has_any_role('Olympiad Team', 'Olympiad Manager')
async def all_questions(interaction, contest_name: str):
  contest = client.database.get_contest(contest_name) 
  question_string = ""

  for question in contest.all_questions:
    question_string += "Q{questionNumber}: answer = {answer}, points = {pointValue} \n".format(
      questionNumber = question.getNumber(), answer = question.correctAnswer, pointValue = question.pointValue)
  try:
    await interaction.response.send_message(question_string)
  except:
    await interaction.response.send_message("Hmm... There doesn't seem to be any teams at the moment.")





@tree.command(name = "link", description = "gets the link of a contest.", guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name = getContestNames)
async def link(interaction, contest_name: str):
  contest = client.database.get_contest(contest_name)
  if contest.period == ContestPeriod.competition or contest.period == ContestPeriod.postCompetition:
    await interaction.response.send_message(contest.link,ephemeral = True)
  else:
    await interaction.response.send_message("Sorry, you cannot access this right now.",ephemeral = True)

@tree.command(name = "change_link", description = "changes the link of a contest.", guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name = getContestNames)
@app_commands.checks.has_any_role('Olympiad Team', 'Olympiad Manager')
async def change_link(interaction, contest_name: str, new_link: str):
  contest = client.database.get_contest(contest_name)
  contest.link = new_link
  client.database.update_contest(contest)
  await interaction.response.send_message("Link has been changed!")


@tree.command(name = "team_rankings", description = "get the team rankings for the specified contest.", guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name = getContestNames)
async def team_rankings(interaction, contest_name: str):
  try:
    contest = client.database.get_contest(contest_name) 
    rankingString = ""
    counter = 1
    for team in contest.team_rankings:
      rankingString += "#{rank}: {teamName}, with {points} points. \n".format(rank = counter, teamName = team.name, points = team.totalPoints)
      counter += 1
    try:
      await interaction.response.send_message(rankingString)
    except:
      await interaction.response.send_message("Oops... Looks like there isn't any teams left in this competition. Hopefully, this is a glitch(everybody leaving DSMC would be really sadge). ")
  except WrongPeriodException:
    await interaction.response.send_message("The competition hasn't started yet, and thus there aren't any rankings. Use /all_teams to get a list of every team.")


@tree.command(name = "all_teams",description = "shows all teams, as well as which members are in each team.", guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name = getContestNames)
async def all_teams(interaction, contest_name: str):
  contest = client.database.get_contest(contest_name)
  allTeamsString = ""
  for team in contest.all_teams:
    allTeamsString += "Team '{teamName}', with owner '{owner}' and members {members}, \n".format(
      teamName = team.name, 
      owner = interaction.guild.get_member(team.ownerID).name,
      members = [interaction.guild.get_member(memberID).name for memberID in team.memberIDs]
    )
  await interaction.response.send_message("All teams: \n" + allTeamsString)


@tree.command(name = "delete_contest", description = "deletes a contest. WARNING - avoid using this command.",guild=discord.Object(id=current_guild_id))
@app_commands.autocomplete(contest_name = getContestNames)
@app_commands.checks.has_any_role('Olympiad Team', 'Olympiad Manager')
async def delete_contest(interaction, contest_name: str):
  client.database.delete_contest(contest_name)
  await interaction.response.send_message("Contest has been deleted!")
  

# Description of all of the nessecary commands

# create Contest - ADMIN

# register Team

# unregister Team - ADMIN

# add question - ADMIN

# answer question

# get_team_score

# submit_answers

# all registered users - ADMIN

# all questions

# team rankings

# DO NOT DELETE THESE LINES OF CODE:
running()
client.run(os.environ['token'])




