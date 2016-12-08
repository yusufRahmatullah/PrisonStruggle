import selenium.webdriver as wd
from PIL import Image
import re
import threading
import time
import json

# read config
with open('config.json', 'r') as f:
	config = json.load(f)

# global variable
b = None
captcha_data = None
is_run = False
USERNAME = config["username"]
PASSWORD = config["password"]
SLEEP_TIME = config["sleep_time"]
CYCLE_TIME = config["cycle_time"]

def get_train_data():
	global b
	
	for i in range(100):
		get_captcha_image(name = '{}.png'.format(i+1))

def segment_image():
	top = 4
	bottom = 14
	for i in range(1, 101):
		img = Image.open('{}.png'.format(i))
		for j in range(5):
			left = j*9+1
			right = left + 8
			name = '{}_{}.png'.format(i, j+1)
			im = img.crop((left, top, right, bottom))
			im.save(name)

def get_captcha_text(name='login.png'):
	global captcha_data
	
	top = 4
	bottom = 14
	
	if captcha_data == None:
		captcha_data = {}
		for i in range(10):
			img = Image.open('data-{}.png'.format(i))
			temp_data = list(img.getdata())
			cap_data = []
			for d in temp_data:
				cap_data.append(d + (255,))
			captcha_data[i] = cap_data
	
	img = Image.open(name)
	result = []
	for i in range(5):
		left = i * 9 + 1
		right = left + 8
		im = img.crop((left, top, right, bottom))
		temp_data = list(im.getdata())
		for key in captcha_data.iterkeys():
			if temp_data == captcha_data[key]:
				result.append(str(key))
				break
	return ''.join(result)
		
def get_captcha_image(name='0.png'):
	global b
	
	# b.get('http://www.prisonstruggle.com')
	b.maximize_window()
	b.save_screenshot('whole.png')
	imgs = b.find_elements_by_tag_name('img')
	for img in imgs:
		if 'Captcha-img' in img.get_attribute('src'):
			loc = img.location
			size = img.size
			img = Image.open('whole.png')
			left = int(loc['x'])
			top = int(loc['y'])
			right = int(loc['x'] + size['width'])
			bottom = int(loc['y'] + size['height'])
			im = img.crop((left, top, right, bottom))
			im.save(name)
	
def init():
	global b
	
	# b = wd.Chrome()
	b = wd.PhantomJS()
	#~ b.set_window_size()

def login():
	global b
	
	b.get('http://www.prisonstruggle.com')
	b.find_element_by_id('username').send_keys(USERNAME)
	b.find_element_by_id('password').send_keys(PASSWORD)
	get_captcha_image(name='login.png')
	captcha = get_captcha_text()
	print 'captcha:', captcha
	if len(captcha) != 5:
		login()
	inputs = b.find_elements_by_tag_name('input')
	for input in inputs:
		if input.get_attribute('name') == 'captcha':
			input.send_keys(captcha)
			break
	for input in inputs:
		if input.get_attribute('name') == 'submit':
			input.click()
			break
	login_check()

def gym():
	global b
	
	b.get('http://www.prisonstruggle.com/gym.php')
	if not bot_check_general():
		return
	imgs = b.find_elements_by_tag_name('img')
	for img in imgs:
		try:
			if 'Energy' in img.get_attribute('onmouseover'):
				bar_text = re.findall('\d+', img.get_attribute('onmouseover'))
				bar_value = int(bar_text[0])
				max_bar_value = int(bar_text[1])
				if bar_value != max_bar_value:
					print 'energy not in max condition: {}/{}'.format(bar_value, max_bar_value)
					return
				else:
					print 'Energy: {}/{}'.format(bar_value, max_bar_value)
					break
		except Exception as e:
			# print '[gym 1]', e
			pass
	buttons = b.find_elements_by_class_name('button')
	# get stat
	stats = []
	tds = b.find_elements_by_tag_name('td')
	for td in tds:
		try:
			if td.get_attribute('width') == '35%':
				stats.append(td)
		except Exception as e:
			# print '[gym 2]', e
			pass
	values = []
	for stat in stats:
		try:
			temp = re.findall('[\d\,]+', stat.text)
			if ',' in temp[0]:
				_temp = temp[0].replace(',', '')
			else:
				_temp = temp[0]
			values.append(int(_temp))
		except Exception as e:
			pass
	try:
		buttons = b.find_elements_by_class_name('button')
		if values[0]/values[1] >= 3:	# ratio of strength and defend
			print '[gym] train defend because defend is too small: {} << {}'.format(values[1], values[0])
			buttons[1].click()
		elif values[0] > values[2]:	# strength more than speed:
			print '[gym] train speed because speed less than strength: {} < {}'.format(values[2], values[0])
			buttons[2].click()
		else:
			print '[gym] train strength because strength not yet trained: {}'.format(values[0])
			buttons[0].click()
	except Exception as e:
		pass
	
def crime():
	global b
	
	b.get('http://www.prisonstruggle.com/crime.php')
	# while True and not bot_check_alert():
	while True:
		try:
			# get max crime
			btns = b.find_elements_by_class_name('advBtn')
			print '[crime]len(btns):', len(btns)
			if btns==None:
				break
			av_crimes = []
			for btn in btns:
				try:
					if 'tick' in btn.get_attribute('src'):
						av_crimes.append(btn)
				except Exception as e:
					print '[crime in]', e
					pass
			print '[crime]len(av_crimes):', len(av_crimes)
			if len(av_crimes) == 0:
				break
			half = len(av_crimes)/2 - 1
			print '[crime]half:', half
			if half < 0:
				half = 0
			av_crimes[half].click()	
			shower_check()
		except Exception as e:
			print '[crime out]', e
			pass

def search_the_prison_yard():
	global b
	
	try:
		b.get('http://www.prisonstruggle.com/downtown.php')
		# imgs = b.find_elements_by_tag_name('img')
		# found = False
		# for img in imgs:
			# if 'delete' in img.get_attribute('src'):
				# found = True
				# break
		# if not found:
			# pass	# do search in prison yard
	except:
		pass

def bot_check_general():
	global b, captcha_data
	
	# b.get('http://www.prisonstruggle.com/mugcontract.php?section=accepted')
	if 'Bot Check' in b.page_source:
		if 'Warning:' in b.page_source:
			print '[Bot Check] Bot Detected by Advance'
			b.save_screenshot('adv_bot_{}.png'.format(time.time()))
			logout(True)
			for i in range(SLEEP_TIME, -1, -1):
				time.sleep(1)
			login_check()
			return True
			
		print '[Bot Check] Bot detected'
		# get image text
		LEFT = 489
		TOP = 449
		RIGHT = LEFT + 44
		BOTTOM = TOP + 10

		input_loc = (490, 473)
		btn_loc = (544, 468)

		if captcha_data == None:
			captcha_data = {}
			for i in range(10):
				img = Image.open('data-{}.png'.format(i))
				temp_data = list(img.getdata())
				cap_data = []
				for d in temp_data:
					cap_data.append(d + (255,))
				captcha_data[i] = cap_data
		
		b.save_screenshot('whole_bot.png')
		img = Image.open('whole_bot.png')
		# DEBUG
		img.crop((LEFT, TOP, RIGHT, BOTTOM)).save('whole_bot_cropped.png')
		img.crop((490, 473, 535, 486)).save('whole_bot_input.png')
		img.crop((544, 468, 579, 490)).save('whole_bot_button.png')
		result = []
		for i in range(5):
			lefts = i * 9 + LEFT
			right = lefts + 8
			top = TOP
			bottom = BOTTOM
			im = img.crop((lefts, top, right, bottom))
			for y in range(im.size[1]):
				for x in range(im.size[0]):
					if im.getpixel((x, y)) != (255, 255, 255, 255):
						im.putpixel((x, y), (0, 0, 0, 255))
			bot = list(im.getdata())
			for key in captcha_data.iterkeys():
				if bot == captcha_data[key]:
					result.append(str(key))
					break
		if len(result) != 5:
			b.save_screenshot('whole_bot.png')
			return False
		bot_text = ''.join(result)
		print '[Bot Check] result:', bot_text

		# get input and fill
		inputs = b.find_elements_by_tag_name('input')
		for i in inputs:
			try:
				if -2 <= (i.size[0] - input_loc[0]) <= 2 and -2 <= (i.size[1] - input_loc[1]) <= 2:
					i.send_keys(bot_text)
					print '[Bot Check] get_input_fill found'
					break
			except Exception as e:
				pass

		# get and click verify button
		inputs = b.find_elements_by_tag_name('input')
		for i in inputs:
			try:
				if i.get_attribute('type') == 'submit':
					if -2 <= (i.size[0] - btn_loc[0]) <= 2 and -2 <= (i.size[1] - btn_loc[1]) <= 2:
						i.click()
						print '[Bot Check] get_click_button found'
						break
			except Exception as e:
				pass
	return True

def failed_mug():
	global b

	b.get('http://www.prisonstruggle.com/mugcontract.php?section=accepted')
	if bot_check_general():
		imgs = b.find_elements_by_tag_name('img')
		target = None
		for img in imgs:
			try:
				if 'mug.png' in img.get_attribute('src'):
					target = img
					break
			except Exception as e:
				print '[failed_mug] ', e
				pass
		if target != None:
			target.click()
			return True
		else:
			print('[failed_mug] no contract')
	return False

def awake_check():
	global b
	
	try:
		b.get('http://www.prisonstruggle.com/gym.php')
		imgs = b.find_elements_by_tag_name('img')
		for img in imgs:
			try:
				if 'Awake' in img.get_attribute('onmouseover'):
					bar_text = re.findall('\d+', img.get_attribute('src'))
					bar_value = int(bar_text[0])
					if bar_value < 2:
						logout(True)
						login_check()
					break
			except Exception as e:
				# print '[awake_check in]', e
				pass
	except Exception as e:
		# print '[awake_check out]', e
		pass
		
def login_check():
	global b
	
	try:
		b.get('http://www.prisonstruggle.com/crime.php')
		if 'home.php' in b.page_source:
			login()
	except:
		pass

def daily_visit_check():
	global b
	
	try:
		if '<span style="color:#8b0000;">Daily Visits</span>' in b.page_source:
			b.get('http://prisonstruggle.com/dailyvisits.php')
		else:
			pass
		# if '<span href="dailyvisits.php">Daily Visits</span>' in b.page_source:
			# pass	# do something
	except:
		pass

def search_the_prison_yard_and_vote_check():
	global b
	
	try:
		if '<span style="color:darkred;">Search the Prison Yard</span>' in b.page_source:
			search_the_prison_yard()
			vote()
			b.get('http://prisonstruggle.com/gym.php')
	except:
		pass

def money_check(threshold=5000):
	global b
	
	try:
		temp = re.findall('\$\s+\d+\,?\d+', b.page_source)
		money_string = re.split('\s+', temp[0])[1]
		money = int(re.sub(',', '', money_string))
		print '[money_check]money: {}'.format(money)
		if money >= threshold:
			b.get('http://prisonstruggle.com/bank.php?dep=1')
	except Exception as e:
		# money not found or below 1K
		pass

def vote():
	global b
	
	# vote in top web games
	b.get('http://www.prisonstruggle.com/vote.php?on=9')
	try:
		b.find_element_by_id('bVote').click()
	except:
		pass
	
	# vote in apex web gaming
	b.get('http://www.prisonstruggle.com/vote.php?on=5')
	try:
		spans = b.find_elements_by_tag_name('span')
		for span in spans:
			if 'Vote For Prison Struggle' == span.text:
				span.click()
				break
	except:
		pass
	
	# vote the other, just visiting
	b.get('http://www.prisonstruggle.com/vote.php?on=7')
	b.get('http://www.prisonstruggle.com/vote.php?on=1')
	b.get('http://www.prisonstruggle.com/vote.php?on=3')
	b.get('http://www.prisonstruggle.com/vote.php?on=6')
	b.get('http://www.prisonstruggle.com/vote.php?on=8')

def bot_check_alert():
	global b
	from selenium.webdriver.support.ui import WebDriverWait as WDW
	from selenium.webdriver.support import expected_conditions as EC
	from selenium.common.exceptions import TimeoutException as TE
	
	try:
		WDW(b, 1).until(EC.alert_is_present(), 'bot detected')
		alert = b.switch_to.alert
		alert.accept()
		
		# execute anti-bot
		b.save_screenshot('whole_bot_{}.png'.format(time.time()))
		return True
	except TE:
		if 'Bot Check' in b.page_source:
			# get image text
			LEFT = 480
			TOP = 449
			RIGHT = 481 + 44
			BOTTOM = 449 + 10

			input_loc = (480, 465)
			btn_loc = (532, 465)

			if captcha_data == None:
				captcha_data = {}
				for i in range(10):
					img = Image.open('data-{}.png'.format(i))
					captcha_data[i] = list(img.getdata())

			b.save_screenshot('whole_bot.png')
			img = Image.open('whole_bot.png')
			result = []
			for i in range(5):
				lefts = i * LEFT + 1
				right = left + 8
				top = TOP
				bottom = BOTTOM
				im = img.crop((left, top, right, bottom))
				for y in range(im.size[1]):
					for y in range(im.size[0]):
						if im.getpixel((x, y)) != (255, 255, 255):
							im.putpixel((x, y), (0, 0, 0))
				bot = list(im.getdata())
				for key in captcha_data.iterkeys():
					if bot == captcha_data[key]:
						result.append(str(key))
						break
			bot_text = ''.join(result)

			# get input and fill
			inputs = b.find_elements_by_tag_name('input')
			for i in inputs:
				try:
					if -2 <= (i.size[0] - input_loc[0]) <= 2 and -2 <= (i.size[1] - input_loc[1]) <= 2:
						i.send_keys(bot_text)
						break
				except:
					pass

			# get and click verify button
			inputs = b.find_elements_by_tag_name('input')
			for i in inputs:
				try:
					if i.get_attribute('type') == 'submit':
						if -2 <= (i.size[0] - btn_loc[0]) <= 2 and -2 <= (i.size[1] - btn_loc[1]) <= 2:
							i.click()
							break
				except:
					pass

		# call failed_mug again
		failed_mug()
		print 'no alert'
		return False

def shower_check():
	global b, is_run
	
	try:
		wait_text = b.find_element_by_id('diveffectjail').text
		wait_time = int(re.findall('\d+', wait_text)[1])
		print 'In shower'
		for i in xrange(wait_time, -1, -1):
			if is_run:
				time.sleep(1)
		b.get('http://www.prisonstruggle.com/crime.php')
	except:
		print 'Not in shower'

def logout(isUseLongPause):
	global b
	
	print 'Logging out...'
	b.get('http://www.prisonstruggle.com/index.php?action=logout')
	if isUseLongPause:
		for _i in range(CYCLE_TIME, 0, -1):
			print 'cycle', _i
			for i in range(SLEEP_TIME, -1, -1):
				time.sleep(1)
	
	
def worker():
	global b, is_run
	
	while is_run:
		login_check()
		search_the_prison_yard_and_vote_check()
		money_check()
		daily_visit_check()
		money_check()
		awake_check()
		gym()
		if failed_mug():
			crime()
		money_check()
		for i in xrange(SLEEP_TIME, -1, -1):
			if is_run:
				time.sleep(1)
	
if __name__ == '__main__':
	init()
	login()
	is_run = True
	worker()
	#w1 = threading.Thread(target=worker, name='worker')
	#w1.daemon = True
	#w1.start()
