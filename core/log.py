import time
import traceback

""" 
	Provides logging methods and log file handling.
	Log files may be set up and added using addLogger() any output may be used.
	Log files are stored in a global list throughout program run time and will be written to each
	time a logging function is called.

	Call one of the logging functions to add a message, i.e log.panic(message) or log.notice(message).
	If no logger is set up prior to calling the function then it will silently fail.
"""
logfiles = []
levels = {
	'PANIC' : 0,
    'ALERT' : 1,
    'CRITICAL' : 2,
    'ERROR' : 3,
    'WARNING' : 4,
    'NOTICE' : 5,
    'INFO' : 6,
    'DEBUG' : 7,
}

def add_logger(file, level, verbose = False):
	global levels
	global logfiles
	if level == None:
		return True
	if level not in levels:
		return False
	if isinstance(file, str):
		file = open(file, 'a')
	logfiles.append((file, level, verbose))
	return True

""" 
	Gets the calling function by going down the stack trace to the defined
	point by the level. Some notes:
		level 0 - This is getCallingFunction, i.e THIS function.
		level 1 - This will be do_log because do_log called THIS.
		level 2 - This will be  one of the log calling functions, i.e 
																	log.panic()
																	log.notice()
																	log.debug()
		level 3 - This will be the true calling functions.
"""
def get_calling_function(levels):
	trace = traceback.extract_stack()
	if len(trace) > levels:
		frame = trace[-levels -1]
	else:
		frame = trace[0]
	return frame[2]

def do_log(loglevel, message):
	global levels
	global logfiles
	currentTime = time.strftime("%H:%M:%S", time.gmtime())
	function = get_calling_function(3)
	lightMessage = "[%s] %6s: %s\n" % (currentTime, loglevel, message)
	verboseMessage = "[%s] %8s: %20s(): %s\n" % (currentTime, loglevel, function, message)
	for (file, level, verbose) in logfiles:
		if levels[loglevel] <= levels[level]:
			if verbose:
				file.write(verboseMessage)
			else:
				file.write(lightMessage)
			file.flush()

""" The functions which may be called to log messages. """
def panic(message):
    do_log('PANIC', message)

def alert(message):
    do_log('ALERT', message)

def critical(message):
    do_log('CRITICAL', message)

def error(message):
    do_log('ERROR', message)

def warning(message):
    do_log('WARNING', message)

def notice(message):
    do_log('NOTICE', message)

def info(message):
    do_log('INFO', message)

def debug(message):
    do_log('DEBUG', message)
