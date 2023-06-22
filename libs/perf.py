import subprocess
from libs.utils.debug import *
from libs.utils.format import *
from libs.utils.json import *
from libs.utils.list import *
from libs.utils.os import *
from libs.utils.str import *
from libs.utils.unsorted import *
from libs.utils.web import *

# ~ 1.41s per play (without map download)
# up to date with latest pp updates
# using this for '~rs' command only
# otherwise uses oppai-ng for ~top, ~scores (~compare uses ~scores behind)

cmd = f'dotnet libs/PerformanceCalculator/PerformanceCalculator.dll simulate'

def perf_osu(beatmap_id, mods, acc, combo, nmiss):
	mods = ' -m '+' -m '.join(mods) if mods != [] else ''
	res = f'{cmd} osu {beatmap_id} -j{mods} -a {acc} -c {combo} -X {nmiss}'

	print(res)
	return json.loads(subprocess.check_output(res, shell=True))

def perf_taiko(beatmap_id, mods, acc, combo, nmiss):
	mods = ' -m '+' -m '.join(mods) if mods != [] else ''
	return json.loads(subprocess.check_output(f'{cmd} taiko {beatmap_id} -j{mods} -a {acc} -c {combo} -X {nmiss}', shell=True))

def perf_fruits(beatmap_id, mods, acc, combo, nmiss):
	mods = ' -m '+' -m '.join(mods) if mods != [] else ''
	return json.loads(subprocess.check_output(f'{cmd} catch {beatmap_id} -j{mods} -a {acc} -c {combo} -X {nmiss}', shell=True))

def perf_mania(beatmap_id, mods, score):
	mods = ' -m '+' -m '.join(mods) if mods != [] else ''
	return json.loads(subprocess.check_output(f'{cmd} mania {beatmap_id} -j{mods} -s {score}', shell=True))

def perf(mode, *args):
	match mode:
		case 'osu':
			return perf_osu(*args)
		case 'taiko':
			return perf_taiko(*args)
		case 'fruits':
			return perf_fruits(*args)
		case 'mania':
			return perf_mania(*args)
		case _:
			cprint('perf: Unknown '+mode, 'red')
			return None

def perf_pp_osu(*args, as_dict=False):
	r = perf_osu(*args)
	performance = r['performance_attributes']
	aim_pp = performance['aim']
	speed_pp = performance['speed']
	acc_pp = performance['accuracy']
	fl_pp = performance['flashlight']
	total = aim_pp+speed_pp+acc_pp+fl_pp
	bonus_pp = performance['pp']-total
	if as_dict:
		return {
			'total': total+bonus_pp,
			'aim_pp': aim_pp,
			'speed_pp': speed_pp,
			'acc_pp': acc_pp,
			'fl_pp': fl_pp,
			'bonus_pp': bonus_pp
		}
	else:
		return total+bonus_pp, aim_pp, speed_pp, acc_pp, fl_pp, bonus_pp

def perf_pp_taiko(*args, as_dict=False):
	r = perf_taiko(*args)
	performance = r['performance_attributes']
	diff_pp = performance['difficulty']
	acc_pp = performance['accuracy']
	total = diff_pp+acc_pp
	bonus_pp = performance['pp']-total
	if as_dict:
		return {
			'total': total+bonus_pp,
			'diff_pp': diff_pp,
			'acc_pp': acc_pp,
			'bonus_pp': bonus_pp
		}
	else:
		return total+bonus_pp, diff_pp, acc_pp, bonus_pp

def perf_pp_fruits(*args, as_dict=False):
	r = perf_fruits(*args)
	print_json(r)
	exit()
	performance = r['performance_attributes']
	aim_pp = performance['aim']
	speed_pp = performance['speed']
	acc_pp = performance['accuracy']
	fl_pp = performance['flashlight']
	total = aim_pp+speed_pp+acc_pp+fl_pp
	bonus_pp = performance['pp']-total
	if as_dict:
		return {
			'total': total+bonus_pp,
			'aim_pp': aim_pp,
			'speed_pp': speed_pp,
			'acc_pp': acc_pp,
			'fl_pp': fl_pp,
			'bonus_pp': bonus_pp
		}
	else:
		return total+bonus_pp, aim_pp, speed_pp, acc_pp, fl_pp, bonus_pp

def perf_pp_mania(*args, as_dict=False):
	r = perf_mania(*args)
	print_json(r)
	exit()
	performance = r['performance_attributes']
	aim_pp = performance['aim']
	speed_pp = performance['speed']
	acc_pp = performance['accuracy']
	fl_pp = performance['flashlight']
	total = aim_pp+speed_pp+acc_pp+fl_pp
	bonus_pp = performance['pp']-total
	if as_dict:
		return {
			'total': total+bonus_pp,
			'aim_pp': aim_pp,
			'speed_pp': speed_pp,
			'acc_pp': acc_pp,
			'fl_pp': fl_pp,
			'bonus_pp': bonus_pp
		}
	else:
		return total+bonus_pp, aim_pp, speed_pp, acc_pp, fl_pp, bonus_pp

def perf_pp(mode, *args):
	match mode:
		case 'osu':
			return perf_pp_osu(*args, as_dict=True)
		case 'taiko':
			return perf_pp_taiko(*args, as_dict=True)
		case 'fruits':
			return perf_pp_fruits(*args, as_dict=True)
		case 'mania':
			return perf_pp_mania(*args, as_dict=True)
		case _:
			cprint('perf: Unknown mode: '+mode, 'red')
			return None