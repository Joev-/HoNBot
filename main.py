import sys, time, signal, re
from hashlib import md5
from random import randint, uniform

try:
    from lib.honcore.client import HoNClient
    from lib.honcore.packetdef import *
    from lib.honcore.exceptions import *
except ImportError:
    print "HoNCore could not be found in the lib folder, please ensure it is available."

try:
    from lib.megahal import MegaHAL
except ImportError:
    print "Megahal could not be found in the lib folder, please ensure it is available."

from core import log
import config

# Some nicer constants for message types
MSG_W = "Whisper"
MSG_P = "Private Message"
MSG_N = "Normal"

def strip_clan(player):
    r = re.compile(r'(\[\w{3,4}\])?(\w+)')
    return r.match(player).group(2)

class HoNBot(MegaHAL):
    def __init__(self, brainfile):
        super(HoNBot, self).__init__(brainfile=brainfile)
        self.is_quitting = False
        self.nickname = config.username
        self.owners = config.owners
        self.replyrate = float(config.replyrate)
        self.replynick = float(config.replynick)

    def create_reply(self, message):
        """
        Create a response from the bot's algorithms and returns that.
        """
        response = self.get_reply(message)

        # During the early days of the bot's brain, he'd often just copy the sentence word for word.
        if response.lower() == message.lower():
            log.info("Duplicate message, not responding")
            return

        if response == "I don't know enough to answer yet!":
            log.info("Not enough knowledge to answer yet")
            return
        
        # Don't send empty messages
        if response == "":
            return
        
        return response

    def check_replying(self, event, message):
        """
        Decides if the bot is to reply to the message or not.
        """
        # Get the default reply rate.
        r = self.replyrate

        # Whispers and Private Messages can have 100% reply rate.
        if event == MSG_W or event == MSG_P:
            # Event is one of the above, so just return here.
            return True

        # Check if someone is speaking to the bot, if so a specific
        # reply rate is used.
        if message.lower().find(strip_clan(self.nickname).lower()) != -1:
            r = self.replynick

        # Now roll the dice
        if round(uniform(0, 99), 3) <= r:
            return True
        return False

class HoNBotClient(HoNClient):
    def __init__(self, bot):
        super(HoNBotClient, self).__init__()
        self.bot = bot
        self.configure_client()
        self.logged_in = False
        self.__setup_events()
        self.channels = config.channels
        self.bot_commands = {}
        self.__setup_bot_commands()

    def __setup_events(self):
        self.connect_event(HON_SC_AUTH_ACCEPTED, self.on_auth_accepted)
        self.connect_event(HON_SC_CHANNEL_MSG, self.on_channel_message)
        self.connect_event(HON_SC_JOINED_CHANNEL, self.on_joined_channel)
        self.connect_event(HON_SC_ENTERED_CHANNEL, self.on_entered_channel)
        self.connect_event(HON_SC_WHISPER, self.on_whisper)
        self.connect_event(HON_SC_PM, self.on_private_message)

    def __setup_bot_commands(self):
        self.bot_commands['quit'] = self.c_quit
        self.bot_commands['replyrate'] = self.c_replyrate
        self.bot_commands['replynick'] = self.c_replynick
        self.bot_commands['join'] = self.c_join
        self.bot_commands['leave'] = self.c_leave
        self.bot_commands['shutup'] = self.c_stoptalking
        self.bot_commands['speak'] = self.c_starttalking

    def configure_client(self):
        """
        Configures the client with the following settings.
            `protocol`      Which chat protocol to use.
            `invisible`     Whether invisible mode should be used or not.
        """
        self._configure(protocol=config.protocol, invis=config.invis_mode)

    @property
    def is_logged_in(self):
        return self.logged_in
    
    def login(self):
        """
        Wrapper function for convience and logic,
        handles both logging in and connecting.
        """
        log.info("Logging in...")
        try:
            self._login(config.username, config.password)
        except MasterServerError, e:
            log.error(e)
            return False
        self.logged_in = True

        log.info("Connecting...")
        try:
            self._chat_connect()
        except ChatServerError, e:
            log.error(e)
            return False

    def connect(self):
        """
        Wrapper function, handles connecting only.
        Used to re-connect.
        """
        try:
            self._chat_connect()
        except ChatServerError, e:
            log.error(e)
            return False
        return True

    def logout(self):
        log.info("Disconnecting...")
        
        if not self.is_connected:
            self.logged_in = False
            return

        try:
            self._chat_disconnect()
        except ChatServerError, e:
            log.error(e)
        
        log.info("Logging out...")
        try:
            self._logout()
        except MasterServerError, e:
            log.error(e)
        self.logged_in = False
    
    def on_auth_accepted(self, *p):
        """
        Authenticated, join the default channels and set up some base things.
        """
        log.info("Connected as %s" % self.account.nickname)
        self.bot.nickname = self.account.nickname
        for channel in self.channels.keys():
            self.join_channel(channel)

    def on_joined_channel(self, channel, channel_id, topic, operators, users):
        log.info("\033[92mJoined \033[0m[%s - %s]" % (channel, topic))
        if channel not in self.channels:
            self.channels[channel] = {'speaking' : True, 'learning': True}

    def on_left_channel(self, channel):
        log.info("\033[92mLeft\033[0m [%s]" % channel)
        del self.channels[channel]

    def on_entered_channel(self, channel_id, user):
        log.info("(%s) \033[32m%s entered the channel.\033[0m" % (self.id_to_channel(channel_id), user.nickname))

    def on_channel_message(self, account_id, channel_id, message):
        player = self.id_to_nick(account_id)
        channel = self.id_to_channel(channel_id)
        log.info("(%s) %s: %s" % (channel, player, message))
        response = self.parse_message(MSG_N, player, channel, message)
        if response is not None:
            self.send_channel_message(response, channel_id)
            log.info("(%s) \033[96m%s\033[0m: %s" % (channel, self.bot.nickname, response))

    def on_whisper(self, player, message):
        log.info("\033[94m(Whisper from %s)\033[0m %s" % (player, message))
        response = self.parse_message(MSG_W, player, self.bot.nickname, message)
        if response is not None:
            self.send_whisper(player, response)
            log.info("\033[94m(Whispered to %s)\033[0m %s" % (player, response))

    def on_private_message(self, player, message):
        log.info("\033[34m(Private message from %s)\033[0m %s" % (player, message))
        response = self.parse_message(MSG_P, player, self.bot.nickname, message)
        if response is not None:
            self.send_private_message(player, response)
            log.info("\033[34m(Private message to %s)\033[0m %s" % (player, response))

    def parse_message(self, event, source, target, message):
        """
        Processes the message received and decides what a response would be.
            `event`     The type of message received. Either MSG_N, MSG_W or MSG_P.
            `source`    The location the message came from, usualy a player.
            `target`    The location the message went to. Either a channel, or one's self in the case of a whisper or PM.
            `message`   The actual message to be processed.
        """

        # Ignore the bot's own messages.
        if source == self.bot.nickname: return
        
        # Ignore empty messages
        if message == "": return

        # Search for commands or queries in the message
        if message[0] == "!":
            command = message[1:].split(" ")[0] # Split on spaces, and grab the first word, the command.
            args = message[2 + len(command):]   # Grab a list of arguments
            log.debug("(Command) %s: %s" % (command, ''.join(args)))
            if command in self.bot_commands:
                f = self.bot_commands[command]
                # Set the owner bit
                if strip_clan(source) in self.bot.owners:
                    owner = 1
                else:
                    owner = 0
                return f(source, target, args, owner)
        #elif message[0] == "?":
            ## A query
            #query = message[1:].split(" ")[0]
            #args = message[2 + len(query):]
            #log.debug("(Query) %s: %s" % (query, ''.join(args)))
        else:
            # If the bot is allowed to learn then let it learn!
            if (target in self.channels and self.channels[target]['learning']) or event == MSG_P or event == MSG_W:
                self.bot.learn(message)

            # Check if the bot is to reply with a generated response. 
            if ((target in self.channels and self.channels[target]['speaking']) or event == MSG_P or event == MSG_W) \
            and self.bot.check_replying(event, message):
                response = self.bot.create_reply(message)
                return response

        # If None is returned, then the bot does nothing.
        return None

    """ Command handlers for the bot. """
    def c_quit(self, source, target, args, owner):
        if owner:
            log.notice("%s told me to quit. :(" % source)
            self.bot.is_quitting = True
            self.logout()
        else:
            log.notice("%s is not authorised to use the `quit` command." % source)

    def c_replyrate(self, source, target, args, owner):
        rate = round(float(args.split()[0]), 3)
        if owner:
            self.bot.replyrate = rate
            log.notice("Reply rate set to %.2f%% by %s." % (rate, source))
            response = "Now replying to %.2f%% of messages." % rate
        else:
            log.notice("%s attempted to change my reply rate to %.2f%%." % (source, rate))
            response = "Only owners can change that."
        return response
    
    def c_replynick(self, source, target, args, owner):
        rate = round(float(args.split()[0]), 3)
        if owner:
            self.bot.replynick = rate
            log.notice("Nick reply rate set to %.2f%% by %s" % (rate, source))
            response = "Now replying to %.2f%% of messages containing my name" % rate
        else:
            log.notice("%s attempted to change my nick reply rate to %.2f%%." % (source, rate))
            response = "Only owners can change that."
        return response
    
    def c_join(self, source, target, args, owner):
        channels = args.split()
        if owner:
            for channel in channels:
                if channel in self.channels:
                    log.notice("Already in channel %s" % channel)
                    return
                self.join_channel(channel)
                response = None
        else:
            log.notice("%s attempted to invite me to the channel(s) %s." % (source, ''.join([c for c in channels])))
            response = "Only my owner may invite me to join another channel."
        return response    
    
    def c_leave(self, source, target, args, owner):
        channels = args.split()
        if owner:
            for channel in channels:
                if channel not in self.channels:
                    log.notice("Not in channel %s" % channel)
                    return
                self.leave_channel(channel)
                response = None
        else:
            log.notice("%s attempted to make me leave the channel(s) %s." % (source, ''.join([c for c in channels])))
            response = "Only my owner may make me leave a channel."
        return response

    def c_stoptalking(self, source, target, args, owner):
        if owner:
            if target in self.channels and self.channels[target]['speaking']:
                self.channels[target]['speaking'] = False
                response = "Okay :-("
        else:
            response = "Nope"
        return response

    def c_starttalking(self, source, target, args, owner):
        if owner:
            if target in self.channels and not self.channels[target]['speaking']:
                self.channels[target]['speaking'] = True
                response = "\o/"
        else:
            response = "Nope"
        return response

def main():
    """
    The main event to call, the bot connects to HoN and starts
    processing events.
    Disconnects should be caught and automatic re-connection
    can be handled.

    Process:
        1. Attempt to log in.
        2. Attempt to connect.
        3. Troll noobies!
    """
    honbot = HoNBot('bot-brain')
    client = HoNBotClient(honbot)
    
    def sigint_handler(signal, frame):
        log.info("SIGINT, quitting")
        client.logout()
        sys.exit()

    signal.signal(signal.SIGINT, sigint_handler)

    reconnect_attempts = 0
    while not honbot.is_quitting:
        time.sleep(1) # Cooling..
        client.login()

        while client.is_logged_in and not honbot.is_quitting:
            if client.is_connected is True:
                # Reset the number of attempts.
                reconnect_attempts = 0
                # Do some stuff if I want
                time.sleep(1)
            else:
                reconnect_attempts += 1
                log.info("Disconnected from chat server")
                log.info("Reconnecting in 30 seconds (Attempts %d of 5)" % reconnect_attempts)
                time.sleep(30)
                try:
                    client.connect()
                except ChatServerError, e:
                    log.error(e)

if __name__ == "__main__":
    log.add_logger(sys.stdout, 'DEBUG', False) 
    log.add_logger('honbot.log', 'DEBUG', False)

    main()
