# -*- coding: utf-8 -*- 

import os
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
import logging
import asyncio
import itertools
import sys
import traceback
import random
import itertools
import math
from async_timeout import timeout
from functools import partial
import functools
from youtube_dl import YoutubeDL
import youtube_dl
from io import StringIO
import time
import urllib.request
from gtts import gTTS

##################### 로깅 ###########################
log_stream = StringIO()    
logging.basicConfig(stream=log_stream, level=logging.WARNING)

#ilsanglog = logging.getLogger('discord')
#ilsanglog.setLevel(level = logging.WARNING)
#handler = logging.StreamHandler()
#handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
#ilsanglog.addHandler(handler)
#####################################################

access_token = "your_token_Hera"

def init():
	global command

	command = []
	fc = []

	command_inidata = open('command.ini', 'r', encoding = 'utf-8')
	command_inputData = command_inidata.readlines()

	############## 뮤직봇 명령어 리스트 #####################
	for i in range(len(command_inputData)):
		tmp_command = command_inputData[i][12:].rstrip('\n')
		fc = tmp_command.split(', ')
		command.append(fc)
		fc = []

	del command[0]

	command_inidata.close()

	#print (command)

init()

#mp3 파일 생성함수(gTTS 이용, 남성목소리)
async def MakeSound(saveSTR, filename):
	
	tts = gTTS(saveSTR, lang = 'ko')
	tts.save('./' + filename + '.wav')
	'''
	try:
		encText = urllib.parse.quote(saveSTR)
		urllib.request.urlretrieve("https://clova.ai/proxy/voice/api/tts?text=" + encText + "%0A&voicefont=1&format=wav",filename + '.wav')
	except Exception as e:
		print (e)
		tts = gTTS(saveSTR, lang = 'ko')
		tts.save('./' + filename + '.wav')
		pass
	'''
#mp3 파일 재생함수	
async def PlaySound(voiceclient, filename):
	source = discord.FFmpegPCMAudio(filename)
	try:
		voiceclient.play(source)
	except discord.errors.ClientException:
		while voiceclient.is_playing():
			await asyncio.sleep(1)
	while voiceclient.is_playing():
		await asyncio.sleep(1)
	voiceclient.stop()
	source.cleanup()

# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''


class VoiceError(Exception):
	pass


class YTDLError(Exception):
	pass


class YTDLSource(discord.PCMVolumeTransformer):
	YTDL_OPTIONS = {
		'format': 'bestaudio/best',
		'extractaudio': True,
		'audioformat': 'mp3',
		'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
		'restrictfilenames': True,
		'noplaylist': False,
		'nocheckcertificate': True,
		'ignoreerrors': False,
		'logtostderr': False,
		'quiet': True,
		'no_warnings': True,
		'default_search': 'auto',
		'source_address': '0.0.0.0',
		'force-ipv4' : True,
    		'-4': True
	}

	FFMPEG_OPTIONS = {
		'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
		'options': '-vn',
	}

	ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

	def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
		super().__init__(source, volume)
		self.requester = ctx.author
		self.channel = ctx.channel
		self.data = data

		self.uploader = data.get('uploader')
		self.uploader_url = data.get('uploader_url')
		date = data.get('upload_date')
		self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
		self.title = data.get('title')
		self.thumbnail = data.get('thumbnail')
		self.description = data.get('description')
		self.duration = self.parse_duration(int(data.get('duration')))
		self.tags = data.get('tags')
		self.url = data.get('webpage_url')
		self.views = data.get('view_count')
		self.likes = data.get('like_count')
		self.dislikes = data.get('dislike_count')
		self.stream_url = data.get('url')

	def __str__(self):
		return '**{0.title}** by **{0.uploader}**'.format(self)

	@classmethod
	async def create_source(cls, bot, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
		loop = loop or asyncio.get_event_loop()

		if "http" not in search:
			partial = functools.partial(cls.ytdl.extract_info, f"ytsearch5:{search}", download=False, process=False)

			data = await loop.run_in_executor(None, partial)

			if data is None:
				raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

			emoji_list : list = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "🚫"]
			song_list_str : str = ""
			cnt : int = 0
			song_index : int = 0

			for data_info in data["entries"]:
				cnt += 1
				if 'title' not in data_info:
					data_info['title'] = f"{search} - 제목 정보 없음"
				song_list_str += f"`{cnt}.` [**{data_info['title']}**](https://www.youtube.com/watch?v={data_info['url']})\n"

			embed = discord.Embed(description= song_list_str)
			embed.set_footer(text=f"10초 안에 미선택시 취소됩니다.")

			song_list_message = await ctx.send(embed = embed)

			for emoji in emoji_list:
				await song_list_message.add_reaction(emoji)

			def reaction_check(reaction, user):
				return (reaction.message.id == song_list_message.id) and (user.id == ctx.author.id) and (str(reaction) in emoji_list)
			try:
				reaction, user = await bot.wait_for('reaction_add', check = reaction_check, timeout = 10)
			except asyncio.TimeoutError:
				reaction = "🚫"

			for emoji in emoji_list:
				await song_list_message.remove_reaction(emoji, bot.user)

			await song_list_message.delete(delay = 10)
			
			if str(reaction) == "1️⃣":
				song_index = 0
			elif str(reaction) == "2️⃣":
				song_index = 1
			elif str(reaction) == "3️⃣":
				song_index = 2
			elif str(reaction) == "4️⃣":
				song_index = 3
			elif str(reaction) == "5️⃣":
				song_index = 4
			else:
				return False
			
			result_url = f"https://www.youtube.com/watch?v={data['entries'][song_index]['url']}"
		else:
			result_url = search

		webpage_url = result_url
		partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
		processed_info = await loop.run_in_executor(None, partial)
		if processed_info is None:
			raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))
		
		if 'entries' not in processed_info:
			info = processed_info
		else:
			info = None
			while info is None:
				try:
					info = processed_info['entries'].pop(0)
				except IndexError:
					raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

		return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

	@staticmethod
	def parse_duration(duration: int):
		return time.strftime('%H:%M:%S', time.gmtime(duration))


class Song:
	__slots__ = ('source', 'requester')

	def __init__(self, source: YTDLSource):
		self.source = source
		self.requester = source.requester

	def create_embed(self):
		embed = (discord.Embed(title='Now playing',
							description='**```fix\n{0.source.title}\n```**'.format(self),
							color=discord.Color.blurple())
				.add_field(name='Duration', value=self.source.duration)
				.add_field(name='Requested by', value=self.requester.mention)
				.add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
				.add_field(name='URL', value='[Click]({0.source.url})'.format(self))
				.set_thumbnail(url=self.source.thumbnail))

		return embed


class SongQueue(asyncio.Queue):
	def __getitem__(self, item):
		if isinstance(item, slice):
			return list(itertools.islice(self._queue, item.start, item.stop, item.step))
		else:
			return self._queue[item]

	def __iter__(self):
		return self._queue.__iter__()

	def __len__(self):
		return self.qsize()

	def clear(self):
		self._queue.clear()

	def shuffle(self):
		random.shuffle(self._queue)

	def select(self, index : int, loop : bool = False):
		for i in range(index-1):
			if not loop:
				del self._queue[0]
			else:
				self._queue.append(self._queue[0])
				del self._queue[0]

	def remove(self, index: int):
		del self._queue[index]


class VoiceState:
	def __init__(self, bot: commands.Bot, ctx: commands.Context):
		self.bot = bot
		self._ctx = ctx
		self._cog = ctx.cog

		self.current = None
		self.voice = None
		self.next = asyncio.Event()
		self.songs = SongQueue()

		self._loop = False
		self._volume = 0.5
		self.skip_votes = set()

		self.audio_player = bot.loop.create_task(self.audio_player_task())

	def __del__(self):
		self.audio_player.cancel()

	@property
	def loop(self):
		return self._loop

	@loop.setter
	def loop(self, value: bool):
		self._loop = value

	@property
	def volume(self):
		return self._volume

	@volume.setter
	def volume(self, value: float):
		self._volume = value

	@property
	def is_playing(self):
		return self.voice and self.current

	async def audio_player_task(self):
		while True:
			self.next.clear()

			if self.loop and self.current is not None:
				source1 = await YTDLSource.create_source(self.bot, self._ctx, self.current.source.url, loop=self.bot.loop)
				song1 = Song(source1)
				await self.songs.put(song1)
			else:
				pass

			try:
				async with timeout(180):  # 3 minutes
					self.current = await self.songs.get()
			except asyncio.TimeoutError:
				self.bot.loop.create_task(self.stop())
				return

			self.current.source.volume = self._volume
			self.voice.play(self.current.source, after=self.play_next_song)
			play_info_msg = await self.current.source.channel.send(embed=self.current.create_embed())
			await play_info_msg.delete(delay = 20)

			await self.next.wait()

	def play_next_song(self, error=None):
		if error:
			raise VoiceError(str(error))

		self.next.set()

	def skip(self):
		self.skip_votes.clear()

		if self.is_playing:
			self.voice.stop()

	async def stop(self):
		self.songs.clear()

		if self.voice:
			await self.voice.disconnect()
			self.voice = None

		self.bot.loop.create_task(self._cog.cleanup(self._ctx))

class Music(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.voice_states = {}

	def get_voice_state(self, ctx: commands.Context):
		state = self.voice_states.get(ctx.guild.id)
		if not state:
			state = VoiceState(self.bot, ctx)
			self.voice_states[ctx.guild.id] = state

		return state

	def cog_unload(self):
		for state in self.voice_states.values():
			self.bot.loop.create_task(state.stop())

	def cog_check(self, ctx: commands.Context):
		if not ctx.guild:
			raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

		return True

	async def cog_before_invoke(self, ctx: commands.Context):
		ctx.voice_state = self.get_voice_state(ctx)

	async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
		await ctx.send('에러 : {}'.format(str(error)))
	'''
	@commands.command(name='join', invoke_without_subcommand=True)
	async def _join(self, ctx: commands.Context):
		destination = ctx.author.voice.channel
		if ctx.voice_state.voice:
			await ctx.voice_state.voice.move_to(destination)
			return
		ctx.voice_state.voice = await destination.connect()
	'''
	async def cleanup(self, ctx: commands.Context):
		del self.voice_states[ctx.guild.id]

	@commands.command(name=command[0][0], aliases=command[0][1:])
	#@commands.has_permissions(manage_guild=True)
	async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
		if not channel and not ctx.author.voice:
			raise VoiceError(':no_entry_sign: 현재 접속중인 음악채널이 없습니다.')

		destination = channel or ctx.author.voice.channel
		if ctx.voice_state.voice:
			await ctx.voice_state.voice.move_to(destination)
			return

		ctx.voice_state.voice = await destination.connect()

	@commands.command(name=command[1][0], aliases=command[1][1:])
	#@commands.has_permissions(manage_guild=True)
	async def _leave(self, ctx: commands.Context):
		if not ctx.voice_state.voice:
			return await ctx.send(':no_entry_sign: 현재 접속중인 음악채널이 없습니다.')

		await ctx.voice_state.stop()
		del self.voice_states[ctx.guild.id]

	@commands.command(name=command[8][0], aliases=command[8][1:])
	async def _volume(self, ctx: commands.Context, *, volume: int):
		vc = ctx.voice_client

		if not ctx.voice_state.is_playing:
			return await ctx.send(':mute: 현재 재생중인 음악이 없습니다.')

		if not 0 < volume < 101:
			return await ctx.send('```볼륨은 1 ~ 100 사이로 입력 해주세요.```')

		if vc.source:
			vc.source.volume = volume / 100

		ctx.voice_state.volume = volume / 100
		await ctx.send(':loud_sound: 볼륨을 {}%로 조정하였습니다.'.format(volume))

	@commands.command(name=command[7][0], aliases=command[7][1:])
	async def _now(self, ctx: commands.Context):
		await ctx.send(embed=ctx.voice_state.current.create_embed())

	@commands.command(name=command[3][0], aliases=command[3][1:])
	#@commands.has_permissions(manage_guild=True)
	async def _pause(self, ctx: commands.Context):
		if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
			ctx.voice_state.voice.pause()
			await ctx.message.add_reaction('⏸')

	@commands.command(name=command[4][0], aliases=command[4][1:])
	#@commands.has_permissions(manage_guild=True)
	async def _resume(self, ctx: commands.Context):
		if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
			ctx.voice_state.voice.resume()
			await ctx.message.add_reaction('⏯')

	@commands.command(name=command[9][0], aliases=command[9][1:])
	#@commands.has_permissions(manage_guild=True)
	async def _stop(self, ctx: commands.Context):
		ctx.voice_state.songs.clear()

		if ctx.voice_state.is_playing:
			ctx.voice_state.voice.stop()
			await ctx.message.add_reaction('⏹')

	@commands.command(name=command[5][0], aliases=command[5][1:])
	async def _skip(self, ctx: commands.Context, *, args: int = 1):
		if not ctx.voice_state.is_playing:
			return await ctx.send(':mute: 현재 재생중인 음악이 없습니다.')

		await ctx.message.add_reaction('⏭')

		if args != 1:
			ctx.voice_state.songs.select(args, ctx.voice_state.loop)

		ctx.voice_state.skip()
		'''	
		voter = ctx.message.author
		if voter == ctx.voice_state.current.requester:
			await ctx.message.add_reaction('⏭')
			ctx.voice_state.skip()
		elif voter.id not in ctx.voice_state.skip_votes:
			ctx.voice_state.skip_votes.add(voter.id)
			total_votes = len(ctx.voice_state.skip_votes)
			if total_votes >= 3:
				await ctx.message.add_reaction('⏭')
				ctx.voice_state.skip()
			else:
				await ctx.send('Skip vote added, currently at **{}/3**'.format(total_votes))
		else:
			await ctx.send('```이미 투표하셨습니다.```')
		'''
	@commands.command(name=command[6][0], aliases=command[6][1:])
	async def _queue(self, ctx: commands.Context, *, page: int = 1):

		if len(ctx.voice_state.songs) == 0:
			return await ctx.send(':mute: 재생목록이 없습니다.')
		
		items_per_page = 10
		pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

		start = (page - 1) * items_per_page
		end = start + items_per_page

		queue = ''
		for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
			queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

		if ctx.voice_state.loop:
			embed = discord.Embed(title = '🔁  Now playing', description='**```fix\n{0.source.title}\n```**'.format(ctx.voice_state.current))
		else:
			embed = discord.Embed(title = 'Now playing', description='**```fix\n{0.source.title}\n```**'.format(ctx.voice_state.current))
		embed.add_field(name ='\u200B\n**{} tracks:**\n'.format(len(ctx.voice_state.songs)), value = f"\u200B\n{queue}")
		embed.set_thumbnail(url=ctx.voice_state.current.source.thumbnail)
		embed.set_footer(text='Viewing page {}/{}'.format(page, pages))
		await ctx.send(embed=embed)

	@commands.command(name=command[11][0], aliases=command[11][1:])
	async def _shuffle(self, ctx: commands.Context):
		if len(ctx.voice_state.songs) == 0:
			return await ctx.send(':mute: 재생목록이 없습니다.')

		ctx.voice_state.songs.shuffle()
		result = await ctx.send('셔플 완료!')
		await result.add_reaction('🔀')

	@commands.command(name=command[10][0], aliases=command[10][1:])
	async def _remove(self, ctx: commands.Context, index: int):
		if len(ctx.voice_state.songs) == 0:
			return await ctx.send(':mute: 재생목록이 없습니다.')
		
		remove_result = '`{0}.` [**{1.source.title}**] 삭제 완료!\n'.format(index, ctx.voice_state.songs[index - 1])
		result = await ctx.send(remove_result)
		ctx.voice_state.songs.remove(index - 1)
		await result.add_reaction('✅')
		

	@commands.command(name=command[14][0], aliases=command[14][1:])
	async def _loop(self, ctx: commands.Context):
		if not ctx.voice_state.is_playing:
			return await ctx.send(':mute: 현재 재생중인 음악이 없습니다.')

		# Inverse boolean value to loop and unloop.
		ctx.voice_state.loop = not ctx.voice_state.loop
		if ctx.voice_state.loop :
			result = await ctx.send('반복재생이 설정되었습니다!')
		else:
			result = await ctx.send('반복재생이 취소되었습니다!')
		await result.add_reaction('🔁')

	@commands.command(name=command[2][0], aliases=command[2][1:])
	async def _play(self, ctx: commands.Context, *, search: str):
		if not ctx.voice_state.voice:
			await ctx.invoke(self._summon)

		async with ctx.typing():
			try:
				source = await YTDLSource.create_source(self.bot, ctx, search, loop=self.bot.loop)
				if not source:
					return await ctx.send(f"노래 재생/예약이 취소 되었습니다.")
			except YTDLError as e:
				await ctx.send('에러가 발생했습니다 : {}'.format(str(e)))
			else:
				song = Song(source)

				await ctx.voice_state.songs.put(song)
				await ctx.send('재생목록 추가 : {}'.format(str(source)))

	@commands.command(name=command[13][0], aliases=command[13][1:])
	async def clear_channel_(self, ctx: commands.Context, *, msg: int = 1):
		try:
			msg = int(msg)
		except:
			await ctx.send(f"```지우고 싶은 줄수는 [숫자]로 입력해주세요!```")
		await ctx.channel.purge(limit = msg)

	@_summon.before_invoke
	@_play.before_invoke
	async def ensure_voice_state(self, ctx: commands.Context):
		if not ctx.author.voice or not ctx.author.voice.channel:
			raise commands.CommandError('음성채널에 접속 후 사용해주십시오.')

		if ctx.voice_client:
			if ctx.voice_client.channel != ctx.author.voice.channel:
				raise commands.CommandError('봇이 이미 음성채널에 접속해 있습니다.')

	@commands.command(name=command[12][0], aliases=command[12][1:])   #도움말
	async def menu_(self, ctx):
		command_list = ''
		command_list += '!인중 : 봇상태가 안좋을 때 쓰세요!'     #!
		command_list += ','.join(command[0]) + '\n'     #!들어가자
		command_list += ','.join(command[1]) + '\n'     #!나가자
		command_list += ','.join(command[2]) + ' [검색어] or [url]\n'     #!재생
		command_list += ','.join(command[3]) + '\n'     #!일시정지
		command_list += ','.join(command[4]) + '\n'     #!다시재생
		command_list += ','.join(command[5]) + ' (숫자)\n'     #!스킵
		command_list += ','.join(command[6]) + ' 혹은 [명령어] + [숫자]\n'     #!목록
		command_list += ','.join(command[7]) + '\n'     #!현재재생
		command_list += ','.join(command[8]) + ' [숫자 1~100]\n'     #!볼륨
		command_list += ','.join(command[9]) + '\n'     #!정지
		command_list += ','.join(command[10]) + '\n'     #!삭제
		command_list += ','.join(command[11]) + '\n'     #!섞기
		command_list += ','.join(command[14]) + '\n'     #!
		command_list += ','.join(command[13]) + ' [숫자]\n'     #!경주
		embed = discord.Embed(
				title = "----- 명령어 -----",
				description= '```' + command_list + '```',
				color=0xff00ff
				)
		await ctx.send( embed=embed, tts=False)
	################ 음성파일 생성 후 재생 ################ 			
	@commands.command(name="!인중")
	async def playText_(self, ctx):
		#msg = ctx.message.content[len(ctx.invoked_with)+1:]
		#sayMessage = msg
		await MakeSound('뮤직봇이 마이 아파요. 잠시 후 사용해주세요.', './say' + str(ctx.guild.id))
		await ctx.send("```뮤직봇이 마이 아파요. 잠시 후 사용해주세요.```", tts=False)
		
		if not ctx.voice_state.voice:
			await ctx.invoke(self._summon)
			
		if ctx.voice_state.is_playing:
			ctx.voice_state.voice.stop()
		
		await PlaySound(ctx.voice_state.voice, './say' + str(ctx.guild.id) + '.wav')


		await ctx.voice_state.stop()
		del self.voice_states[ctx.guild.id]

bot = commands.Bot('', help_command = None, description='해성뮤직봇')
bot.add_cog(Music(bot))

@bot.event
async def on_ready():
	print("Logged in as ") #화면에 봇의 아이디, 닉네임이 출력됩니다.
	print(bot.user.name)
	print(bot.user.id)
	print("===========")
	
	await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name=command[12][0], type=1), afk = False)

@bot.event 
async def on_command_error(ctx, error):
	if isinstance(error, CommandNotFound):
		return
	elif isinstance(error, discord.ext.commands.MissingRequiredArgument):
		return
	raise error

bot.run(access_token)
