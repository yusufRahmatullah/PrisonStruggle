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

#region image data capture
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
	
def extend_image_data(data):
	if len(data[0]) == 3:
		for i in xrange(len(data)):
			data[i] = data[i] + (255, )
	
def get_captcha_text(name='login.png'):
	global captcha_data
	
	top = 4
	bottom = 14
	
	load_captcha_data()
	
	img = Image.open(name)
	result = []
	for i in range(5):
		left = i * 9 + 1
		right = left + 8
		im = img.crop((left, top, right, bottom))
		temp_data = list(im.getdata())
		extend_image_data(temp_data)
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
	
def load_captcha_data():
	global captcha_data
	
	if captcha_data == None:
		captcha_data = {}
		for i in range(10):
			img = Image.open('data-{}.png'.format(i))
			temp_data = list(img.getdata())
			extend_image_data(temp_data)
			captcha_data[i] = temp_data

#endregion

#region bot check
def bot_check_general():
	global b, captcha_data
	
	# b.get('http://www.prisonstruggle.com/mugcontract.php?section=accepted')
	if 'Bot Check' in b.page_source:
		if 'Warning:' in b.page_source:
			print '[Bot Check] Bot Detected by Advance'
			gmtime = time.gmtime()
			_y = gmtime.tm_year
			_M = gmtime.tm_mon
			_d = gmtime.tm_mday
			_h = gmtime.tm_hour
			_m = gmtime.tm_min
			_s = gmtime.tm_sec
			b.save_screenshot('advance_{}-{}-{} {}-{}-{}.png'
			.format(_y, _M, _d, _h, _m, _s))
			with open('advance_{}-{}-{} {}-{}-{}.debug.txt'
			.format(_y, _M, _d, _h, _m, _s) ,'w') as f:
				f.write(b.page_source)
			logout(True)
			for i in range(SLEEP_TIME, -1, -1):
				time.sleep(1)
			login_check()
			
		print '[Bot Check] Bot detected'
		gmtime = time.gmtime()
		_y = gmtime.tm_year
		_M = gmtime.tm_mon
		_d = gmtime.tm_mday
		_h = gmtime.tm_hour
		_m = gmtime.tm_min
		_s = gmtime.tm_sec
		b.save_screenshot('bot_{}-{}-{} {}-{}-{}.png'
		.format(_y, _M, _d, _h, _m, _s))
		with open('bot_{}-{}-{} {}-{}-{}.debug.txt'
		.format(_y, _M, _d, _h, _m, _s) ,'w') as f:
			f.write(b.page_source)
		
		# get image text
		LEFT = 489
		TOP = 449
		RIGHT = LEFT + 44
		BOTTOM = TOP + 10

		input_loc = (490, 473)
		btn_loc = (544, 468)

		load_captcha_data()
		
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


#endregion 

#region main function
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

def crime():
	global b
	
	b.get('http://www.prisonstruggle.com/crime.php')
	try:
		buttons = b.find_elements_by_xpath('//input[@class="advBtn"][@src="images/buttons/tick.png"]')
		if len(buttons) > 0:
			buttons[-1].click()
			print('[crime] do crime at {}'.format(len(buttons)))
			shower_check()
	except Exception as e:
		print('[crime] err: {}'.format(e))

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

def failed_mug():
	global b
	
	bot_check_general()
	b.get('http://www.prisonstruggle.com/mugcontract.php?section=accepted')
	try:		
		try:
			num = b.find_element_by_xpath('//table[@id="contracts"]/tbody/tr[2]/td[3]').text
			script_text = b.find_element_by_xpath('//table[@id="contracts"]/tbody/tr[2]/td[7]').get_attribute('innerHTML')
			secs = int(re.findall('\d+', script_text)[0])
			print('[failed_mug] num mug: {}'.format(num))
		except Exception as e:
			print('[failed_mug] err: {}'.format(e))
		target = b.find_element_by_xpath('//img[@src="images/mugcontract/mug.png"]')
		target.click()
		return True
	except Exception as e:
		print('[failed_mug] err: {}'.format(e))
		return False
	
def gang_invite():
	global b
	
	b.get('http://www.prisonstruggle.com/ganginvites.php')
	try:
		b.find_element_by_xpath('//input[@class="advBtn"][@title="Decline"]').click()
	except Exception as e:
		print('[gang_invite] err: {}'.format(e))

def gym():
	global b
	
	bot_check_general()
	b.get('http://www.prisonstruggle.com/gym.php')
	try:
		_temp = b.find_element_by_xpath("//div[@id='sidebar']/div[@id='profile']/div[@class='bottom-information']/img[2]").get_attribute('onmouseover')
		_temp = re.findall('\d+', _temp)
		_val = int(_temp[0])
		_max = int(_temp[1])
		
		if _val != _max:
			# print '[gym] energy:{}'.format(_val) 
			return
		
		str_text = b.find_element_by_xpath("//td[@class='contentcontent']/table/tbody/tr[1]/td[2]").text
		str_temp = re.findall('[\d\,]+', str_text)[0]
		if ',' in str_temp:
			_str = int(re.sub(',', '', str_temp))
		else:
			_str = int(str_temp)
		spd_text = b.find_element_by_xpath("//td[@class='contentcontent']/table/tbody/tr[2]/td[2]").text
		spd_temp = re.findall('[\d\,]+', spd_text)[0]
		if ',' in spd_temp:
			_spd = int(re.sub(',', '', spd_temp))
		else:
			_spd = int(spd_temp)
		
		str_btn = b.find_element_by_xpath("//input[@class='button'][@name='gts']")
		spd_btn = b.find_element_by_xpath("//input[@class='button'][@name='gtss']")
		
		if _str > _spd:
			spd_btn.click()
			print '[gym] train speed'
		else:
			str_btn.click()
			print '[gym] train strength'
	except Exception as e:
		print('[gym new] err:{}'.format(e))

def init():
	global b
	
	# b = wd.Firefox()
	# b = wd.Chrome()
	b = wd.PhantomJS()
	b.set_window_size(1366, 768)

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
	
def login_check():
	global b
	
	try:
		b.get('http://www.prisonstruggle.com/crime.php')
		if 'home.php' in b.page_source:
			login()
	except:
		pass

def logout(isUseLongPause):
	global b
	
	print 'Logging out...'
	b.get('http://www.prisonstruggle.com/index.php?action=logout')
	if isUseLongPause:
		for _i in range(CYCLE_TIME, 0, -1):
			print 'cycle', _i
			for i in range(SLEEP_TIME, -1, -1):
				time.sleep(1)

def money_check():
	global b
	
	try:
		temp = re.findall('\$\s+\d+\,?\d+', b.page_source)
		money_string = re.split('\s+', temp[0])[1]
		money = int(re.sub(',', '', money_string))
		b.get('http://prisonstruggle.com/bank.php?dep=1')
	except Exception as e:
		pass
		
def print_personal_info():
	global b
	
	debug = ''
	try:
		first_idx = 4
		if 'View Gang Invites' in b.page_source:
			print('There is gang invites')
			# first_idx += 2
			gang_invite()
		b.get('http://www.prisonstruggle.com/index.php')
		general_info_path = '//table[@class="mainbox"]/tbody/tr[{}]/td[1]/table/tbody'.format(first_idx)
		
		hp = b.find_element_by_xpath('{}/tr[1]/td[4]'.format(general_info_path)).text
		level = b.find_element_by_xpath('{}/tr[2]/td[2]'.format(general_info_path)).text
		energy = b.find_element_by_xpath('{}/tr[2]/td[4]'.format(general_info_path)).text
		money = b.find_element_by_xpath('{}/tr[3]/td[2]'.format(general_info_path)).text
		awake = b.find_element_by_xpath('{}/tr[3]/td[4]'.format(general_info_path)).text
		bank = b.find_element_by_xpath('{}/tr[4]/td[2]'.format(general_info_path)).text
		nerve = b.find_element_by_xpath('{}/tr[4]/td[4]'.format(general_info_path)).text
		exp = b.find_element_by_xpath('{}/tr[5]/td[2]'.format(general_info_path)).text
		
		attributes_path = '//table[@class="mainbox"]/tbody/tr[{}]/td/table/tbody'.format(first_idx+2)
		
		strength = b.find_element_by_xpath('{}/tr[1]/td[2]'.format(attributes_path)).text
		defense = b.find_element_by_xpath('{}/tr[1]/td[4]'.format(attributes_path)).text
		speed = b.find_element_by_xpath('{}/tr[2]/td[2]'.format(attributes_path)).text
		total = b.find_element_by_xpath('{}/tr[2]/td[4]'.format(attributes_path)).text
				
		print('\n===========================')
		print('PERSONAL INFO')
		print('---------------------------')
		print('Level: {}'.format(level))
		print('Money: {}'.format(money))
		print('Bank: {}'.format(bank))
		print('Level: {}'.format(level))
		print('\n')
		print('HP: {}'.format(hp))
		print('Energy: {}'.format(energy))
		print('Awake: {}'.format(awake))
		print('HP: {}'.format(hp))
		print('Nerve: {}'.format(nerve))
		print('\n')
		print('Strength: {}'.format(strength))
		print('Defense: {}'.format(defense))
		print('Speed: {}'.format(speed))
		print('Total: {}'.format(total))
		print('===========================\n')
	except Exception as e:
		print('[personal info] err:{}'.format(e))

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

def search_the_prison_yard_and_vote_check():
	global b
	
	try:
		if '<span style="color:darkred;">Search the Prison Yard</span>' in b.page_source:
			search_the_prison_yard()
			vote()
			b.get('http://prisonstruggle.com/gym.php')
	except:
		pass

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
			
def worker():
	global b, is_run
	
	while is_run:
		login_check()
		print_personal_info()
		search_the_prison_yard_and_vote_check()
		money_check()
		daily_visit_check()
		money_check()
		awake_check()
		gym()
		if not failed_mug():
			crime()
		money_check()
		for i in xrange(SLEEP_TIME, -1, -1):
			if is_run:
				time.sleep(1)

#endregion

if __name__ == '__main__':
	init()
	login()
	is_run = True
	worker()
	#w1 = threading.Thread(target=worker, name='worker')
	#w1.daemon = True
	#w1.start()
