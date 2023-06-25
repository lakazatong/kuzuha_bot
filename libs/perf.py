import subprocess, json
from python_utils.utils.all import *

# ~ 1.41s per play (without map download)
# up to date with latest pp updates
# using this for '~rs' command only
# otherwise uses oppai-ng for ~top, ~scores (~compare uses ~scores behind)

cmd = f'dotnet libs/PerformanceCalculator/PerformanceCalculator.dll simulate'

def perf_osu(beatmap_id, mods, combo, misses, goods=None, mehs=None, acc=None):
	mods = ' -m '+' -m '.join(mods) if mods != [] else ''
	if acc:
		print(f'{cmd} osu {beatmap_id} -j{mods} -a {acc} -c {combo} -X {misses}')
		return json.loads(subprocess.check_output(f'{cmd} osu {beatmap_id} -j{mods} -a {acc} -c {combo} -X {misses}', shell=True))
	else:
		print(f'{cmd} osu {beatmap_id} -j{mods} -c {combo} -G {goods} -M {mehs} -X {misses}')
		return json.loads(
			subprocess.check_output(f'{cmd} osu {beatmap_id} -j{mods} -c {combo} -G {goods} -M {mehs} -X {misses}', shell=True))

def perf_taiko(beatmap_id, mods, combo, goods, misses, acc=None):
	mods = ' -m '+' -m '.join(mods) if mods != [] else ''
	if acc:
		return json.loads(subprocess.check_output(f'{cmd} osu {beatmap_id} -j{mods} -a {acc} -c {combo} -X {misses}', shell=True))
	else:
		return json.loads(
			subprocess.check_output(f'{cmd} osu {beatmap_id} -j{mods} -c {combo} -G {goods} -X {misses}', shell=True))

def perf_fruits(beatmap_id, mods, combo, droplets, tiny, misses, acc=None):
	mods = ' -m '+' -m '.join(mods) if mods != [] else ''
	if acc:
		return json.loads(subprocess.check_output(f'{cmd} osu {beatmap_id} -j{mods} -a {acc} -c {combo} -X {misses}', shell=True))
	else:
		return json.loads(
			subprocess.check_output(f'{cmd} osu {beatmap_id} -j{mods} -c {combo} -G {droplets} -M {tiny} -X {misses}', shell=True))

def perf_mania(beatmap_id, mods, score):
	mods = ' -m '+' -m '.join(mods) if mods != [] else ''
	return json.loads(subprocess.check_output(f'{cmd} mania {beatmap_id} -j{mods} -s {score}', shell=True))

def perf_pp_osu(*args):
	r = perf_osu(*args)
	performance = r['performance_attributes']
	aim_pp = performance['aim']
	speed_pp = performance['speed']
	acc_pp = performance['accuracy']
	fl_pp = performance['flashlight']
	total = aim_pp+speed_pp+acc_pp+fl_pp
	bonus_pp = performance['pp']-total
	return {
		'total': total+bonus_pp,
		'aim_pp': aim_pp,
		'speed_pp': speed_pp,
		'acc_pp': acc_pp,
		'fl_pp': fl_pp,
		'bonus_pp': bonus_pp
	}

def perf_pp_taiko(*args):
	r = perf_taiko(*args)
	performance = r['performance_attributes']
	diff_pp = performance['difficulty']
	acc_pp = performance['accuracy']
	total = diff_pp+acc_pp
	bonus_pp = performance['pp']-total
	return {
		'total': total+bonus_pp,
		'diff_pp': diff_pp,
		'acc_pp': acc_pp,
		'bonus_pp': bonus_pp
	}

def perf_pp_fruits(*args):
	r = perf_fruits(*args)
	performance = r['performance_attributes']
	aim_pp = performance['aim']
	speed_pp = performance['speed']
	acc_pp = performance['accuracy']
	fl_pp = performance['flashlight']
	total = aim_pp+speed_pp+acc_pp+fl_pp
	bonus_pp = performance['pp']-total
	return {
		'total': total+bonus_pp,
		'aim_pp': aim_pp,
		'speed_pp': speed_pp,
		'acc_pp': acc_pp,
		'fl_pp': fl_pp,
		'bonus_pp': bonus_pp
	}

def perf_pp_mania(*args):
	r = perf_mania(*args)
	performance = r['performance_attributes']
	aim_pp = performance['aim']
	speed_pp = performance['speed']
	acc_pp = performance['accuracy']
	fl_pp = performance['flashlight']
	total = aim_pp+speed_pp+acc_pp+fl_pp
	bonus_pp = performance['pp']-total
	return {
		'total': total+bonus_pp,
		'aim_pp': aim_pp,
		'speed_pp': speed_pp,
		'acc_pp': acc_pp,
		'fl_pp': fl_pp,
		'bonus_pp': bonus_pp
	}