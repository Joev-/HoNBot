#Python HoN Bot

This is a fairly basic bot I wrote in Python for some fun and to test [HoNCore]https://github.com/Joev-/HoNCore while writing it.
It's main function is to observe, learn and respond using a Markov Chain Algorithm via a Python project called [MegaHAL]http://megahal.alioth.debian.org/.

I am releasing it here in the hope that it will be useful to others for learning and using, as I will no longer be using it or actively devloping it.

During the first few days what it says may not be very interesting, it's a good idea to leave it for a week before letting it speak.

I also seem to remember there being a bug where the bot would not follow his reply rate setting, but I think I may have fixed that.
I no longer work with it, or any of my HoN projects, so I'm not sure.

## Config.py

The configuration for the bot is fairly simple. It is all stored in and read from the config.py file.
Copy `config.example.py` to `config.py` and edit the settings to fit your needs.

* `username` Should be the username of the HoN account that the bot will log in using.
* `password` The password to the aformentioned account.
* `protocol` The current chat version protocol. You will need to update this after most 'large' patches.
* `invis_mode` Set to True if you want the bot to log in using the 'invisible' mode. You probably don't want to unless testing.

* `channels` A python dictionary of channels the bot will autojoin and the settings for that channel. Follow the same format as given in the exaple.

* `owners` A list of people who will have the ability to give bots commands.
* `replyrate` How likely the bot will be to respond to messages. The value is a percentage, so 5 would be a 5% chance to respond.
* `replynick` The reply rate for when someone says the bot's name in the channel.

## Commands

As this bot was fairly basic there are not that many commands yet, just a few basic ones to keep the bot under control.
Commands can be sent to the bot via whisper/pm or given in any channel the bot is in.
Only owners will be able to give commands.

* `!join channelname` Causes the bot to join the given channel.
* `!leave [channel1 channel2]` Causes the bot to leave the given channel(s).
* `!quit` Forces the bot to logout and exit, ending the program.
* `!replynick value` Sets the reply rate for the bot's nickname to the following value, **do not** append a '%' character.
* `!replyrate value` Sets the reply rate for all messages to the following value, **do not** append a '%' character.
* `!shutup` Forces the bot to stop responding to messages.
* `!speak` Allows the bot to respond to messages.
