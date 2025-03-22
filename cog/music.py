import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import os
import asyncio
import pytube


class Channel:
    def __init__(self):
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.loop: bool = False
        self.current = ""
        self.music_queue = []
        self.vc = None


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel = {}

        self.FFMPEG_OPTIONS = {'options': '-vn'}

        self.YTDL_OPTIONS = {'format': 'bestaudio/best',
                             'reconnect': 1,
                             'reconnect_streamed': 1,
                             'reconnect_delay_max': 5}
        self.ytdl = YoutubeDL(self.YTDL_OPTIONS)

    @staticmethod
    async def log(text):
        print(f'[log] {text}')

    @commands.hybrid_command()
    async def play(self, ctx, query):
        vcid = ctx.author.voice.channel.id
        await self.log(f'{ctx.author.name}: {query}')

        song = await self.search(query)

        await ctx.reply(f"**'{song['title']}'** добавлена в очередь")

        await self.connect(ctx)
        self.channel[vcid].music_queue.append([song, ctx.author.voice.channel])
        if not self.channel[vcid].is_playing:
            await self.play_song(ctx)

    @commands.hybrid_command()
    async def skip(self, ctx):
        vcid = ctx.author.voice.channel.id
        if self.channel[vcid].vc:
            self.channel[vcid].vc.stop()
            await self.play_song(ctx, connect=0)

    @commands.hybrid_command()
    async def queue(self, ctx):
        vcid = ctx.author.voice.channel.id
        if not self.channel[vcid].music_queue and not self.channel[vcid].current:
            await ctx.reply('```Нет музыки в очереди```')

        retval = ""
        if self.channel[vcid].loop:
            retval += f'сейчас зациклена: {self.channel[vcid].current[0]["title"]}  \n'
        else:
            retval += f'сейчас играет: {self.channel[vcid].current[0]["title"]}  \n'
        for i in range(0, len(self.channel[vcid].music_queue)):
            retval += f'#{i+1}' + self.channel[vcid].music_queue[i][0]["title"] + '\n'
        if retval != "":
            await ctx.reply(f'```Очередь:\n{retval}```')

    @commands.hybrid_command()
    async def clear(self, ctx):
        vcid = ctx.author.voice.channel.id
        if self.channel[vcid].vc is not None and self.channel[vcid].is_playing:
            self.channel[vcid].vc.stop()
        self.channel[vcid] = Channel()
        await ctx.reply("Очередь очищена")

    @commands.hybrid_command()
    async def stop(self, ctx):
        vcid = ctx.author.voice.channel.id
        await self.channel[vcid].vc.disconnect()
        self.channel[vcid] = Channel()


    @commands.hybrid_command()
    async def remove(self, ctx, number):
        vcid = ctx.author.voice.channel.id
        try:
            self.channel[vcid].music_queue.pop(number-1)
        except Exception as err:
            await self.log(f'can`t delete song #{number}: {err}')
            await ctx.reply("Не могу удалить песню")

    @commands.hybrid_command()
    async def loop(self, ctx):
        vcid = ctx.author.voice.channel.id
        self.channel[vcid].loop = not self.channel[vcid].loop
        if self.channel[vcid].loop:
            await ctx.reply("зацикливание включено")
        else:
            await ctx.reply("зацикливание выключено")

    @commands.hybrid_command()
    async def pause(self, ctx):
        vcid = ctx.author.voice.channel.id
        if self.channel[vcid].is_playing:
            self.channel[vcid].is_playing = False
            self.channel[vcid].is_paused = True
            self.channel[vcid].vc.pause()
        elif self.channel[vcid].is_paused:
            self.channel[vcid].is_paused = False
            self.channel[vcid].is_playing = True
            self.channel[vcid].vc.resume()

    @commands.hybrid_command()
    async def playlist(self, ctx, url, count=10):
        vcid = ctx.author.voice.channel.id
        try:
            playlist = pytube.Playlist(url)
        except Exception as err:
            await self.log(f'ERROR: {err}')
            return
        await self.log(f'playing playlist "{playlist.title}"')

        if vcid not in self.channel:
            self.channel[vcid] = Channel()
        try:
            voice_channel = ctx.author.voice.channel
        except Exception as err:
            await ctx.reply("Сначала ты должен подключиться к голосовому каналу!")
            await self.log(err)
            return
        if self.channel[vcid].is_paused:
            self.channel[vcid].vc.resume()
        else:
            if self.channel[vcid].is_playing:
                await ctx.send(
                    f"**{len(self.channel[vcid].music_queue) + 1} ' {playlist.title}'** добавлен в очередь")
            else:
                await ctx.send(f"РїР»РµР№Р»РёСЃС‚ **'{playlist.title}'** добавлен в очередь")
            try:
                i = 0
                for url in playlist:
                    if i < count:
                        song = self.search(url)
                        self.channel[vcid].music_queue.append([song, ctx.author.voice.channel])
                        i += 1
                        continue
                    break
            except Exception as err:
                await self.log(f'ERROR: {err}')
                return
            if not self.channel[vcid].is_playing:
                await self.play_music(ctx)

    @commands.Cog.listener()
    async def on_voice_state_update(self, _member, before, _after):
        vcid = before.channel.id
        await self.check_leave(vcid)

    async def check_leave(self, ctx):
        vcid = ctx.author.voice.channel.id
        if len(self.channel[vcid].vc.channel.members) == 1:
            # await self.stop(vcid)
            pass

    async def play_song(self, ctx, connect=0):
        vcid = ctx.author.voice.channel.id
        self.channel[vcid].vc.stop()
        if len(self.channel[vcid].music_queue) > 0 or self.channel[vcid].loop:
            self.channel[vcid].is_playing = True

            url = await self.get_song(ctx)
            if connect:
                await self.connect(ctx)
            await self.check_leave(ctx)

            if not self.channel[vcid].loop or not os.path.exists(f'tmp/music/{vcid}.weba'):
                await self.download(url, ctx)
            await self.log(f"playing {url}")
            self.channel[vcid].vc.play(
                discord.FFmpegPCMAudio(f'tmp/music/{vcid}.weba', executable="ffmpeg", **self.FFMPEG_OPTIONS),
                after=lambda e: asyncio.run_coroutine_threadsafe(self.play_song(ctx, connect=0), self.bot.loop)
            )
        else:
            self.channel[vcid].is_playing = False
            self.channel[vcid].current = ""

    async def get_song(self, ctx):
        vcid = ctx.author.voice.channel.id
        if not self.channel[vcid].loop or not self.channel[vcid].current:
            self.channel[vcid].current = self.channel[vcid].music_queue.pop(0)
        return self.channel[vcid].current[0]['url']

    @staticmethod
    async def search(query):
        # for some reason doesn't work

        # if query.startswith("https://"):
        #     video = pytube.YouTube(query)
        #     return {'url': video.watch_url, 'title': video.title}
        search = pytube.Search(query)
        return {'url': search.results[0].watch_url, 'title': search.results[0].title}

    async def connect(self, ctx):
        vcid = ctx.author.voice.channel.id
        if vcid not in self.channel.keys():
            self.channel[vcid] = Channel()
        if not self.channel[vcid].vc or not self.channel[vcid].vc.is_connected():
            try:
                self.channel[vcid].vc = await ctx.author.voice.channel.connect()
            except Exception as err:
                await ctx.reply("can`t connect to vc")
                await self.log(f"can`t connect to vc: {err}")
                return

    async def download(self, song, ctx: commands.Context):
        vcid = ctx.author.voice.channel.id

        if os.path.exists(f'tmp/music/{vcid}.weba'):
            os.remove(f'tmp/music/{vcid}.weba')

        options = self.YTDL_OPTIONS
        options["outtmpl"] = f'tmp/music/{vcid}.weba'
        ytdl = YoutubeDL(options)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: ytdl.download(song))
