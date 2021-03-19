import re
import time
import traceback


from .streamer import Streamer
from .player import Mode, State

class ProcessCommand(object):
    def __init__(self, player, ttclient, services, default_service, admins, banned_users):
        self.player = player
        self.ttclient = ttclient
        self.services = services
        self.service = default_service
        self.streamer = Streamer(self.services)
        self.admins = admins
        self.banned_users = banned_users
        self.commands_dict = {'p': self.play_pause, 's': self.stop, 'm': self.mode,     'sb': self.seek_back, 'sf': self.seek_forward, 'r': self.rate, 'v': self.volume, 'u': self.play_by_url, 'h': self.help, 'n': self.next, 'b': self.back, 'c': self.change_service}
        self.admin_commands_dict = {'girl': lambda arg: 'Настенька', "cn": self.change_nickname}


    def __call__(self, message, user):
        if user.szUsername in self.banned_users:
            return _('You are banned')
        self.user = user
        self.is_admin = user.szUsername in self.admins
        if not self.is_admin:
            if user.nChannelID != self.ttclient.getMyChannelID():
                return _('You aren\'t in channel with bot')
        try:    
            command = re.findall('[a-z]+', message.split(' ')[0].lower())[0]
        except IndexError:
            return self.help()
        arg = ' '.join(message.split(' ')[1::])
        try:
            if command in self.commands_dict:
                return self.commands_dict[command](arg)
            elif self.is_admin and command in self.admin_commands_dict:
                return self.admin_commands_dict[command](arg)
            else:
                return _('Unknown command.\n') + self.help()
        except Exception as e:
            traceback.print_exc()
            return f'error: {e}'

    def play_pause(self, arg):
        if arg:
            self.ttclient.send_message(_('it is finding'), self.user.nUserID)
            track_list = self.service.search(arg)
            if track_list:
                self.player.play(track_list)
                self.ttclient.send_message(_("{} offered {}").format(self.user.szNickname, track_list[0].name), type=2)
                return _('Playing {}').format(track_list[0].name)
            else:
                return _('not found')
        else:
            if self.player.state == State.Playing:
                self.player.pause()
            elif self.player.state == State.Paused:
                self.player.play()


    def rate(self, arg):
        if not arg:
            self.player._vlc_player.set_rate(1)
            return
        try:
            rate_number = abs(float(arg))
            if rate_number > 0 and rate_number <= 4:
                self.player._vlc_player.set_rate(rate_number)
            else:
                return _('Speed must be from 1 to 4')
        except ValueError:
            return _('Введите число, используйте .')

    def play_by_url(self, arg):
        if arg:
            try:
                tracks = self.streamer.get(arg, self.is_admin)
                if tracks:
                    self.player.play(tracks)
                elif tracks == []:
                    return _('Пустая Папка')
                else:
                    return _('Not exist file')
            except ValueError:
                return _('Неверный протокол')
        elif not arg:
            return self.help()

    def stop(self, arg):
        self.player.stop()

    def volume(self, arg):
        try:
            volume = int(arg)
            if volume >= 0 and volume <= 100:
                self.player.set_volume(int(arg))
            else:
                return _('Громкость в диапозоне 1 100')
        except ValueError:
            return _('Недопустимое значение. Укажите число от 1 до 100.')

    def seek_back(self, arg):
        try:
            self.player.seek_back(arg)
        except ValueError:
            return _('Недопустимое значение. Укажите число от 1 до 100.')

    def seek_forward(self, arg):
        try:
            self.player.seek_forward(arg)
        except ValueError:
            return _('Недопустимое значение. Укажите число от 1 до 100.')

    def next(self, arg):
        try:
            self.player.next()
        except IndexError:
            return _('это последний трек')

    def back(self, arg):
        try:
            self.player.back()
        except IndexError:
            return _('Это первый трек')

    def mode(self, arg):
        mode_help = 'current_ mode: {current_mode}\n{modes}'.format(current_mode=self.player.mode.name, modes='\n'.join(['{name} - {value}'.format(name=i.name, value=i.value) for i in [Mode.Single, Mode.TrackList]]))
        if arg:
            try:
                mode = Mode(int(arg))
                self.player.mode = Mode(mode)
            except TypeError:
                return mode_help
        else:
            return mode_help

    mode.help = 'ModeHelp'

    def change_service(self, arg):
        service_help = 'current service: {current_service}\nevalable: {services}'.format(current_service=self.service.__module__.split('.')[-1], services=', '.join([i for i in self.services]))
        if arg:
            if arg in self.services:
                self.service = self.services[arg]
            else:
                return service_help
        else:
            return service_help

    def change_nickname(self, arg):
        try:
            self.ttclient.change_nickname(arg)
        except UnicodeError:
            return _('Не коректное nickname')


    def help(self, arg=None):
        help_strings = []
        for i in list(self.commands_dict):
            try:
                help_strings.append(
                    '{}: {}'.format(i, self.commands_dict[i].help)
                )
            except AttributeError:
                pass
        return '\n'.join(help_strings)

    help.help = 'Возращает справку'