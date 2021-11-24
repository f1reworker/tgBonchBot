
import asyncio
import time

from PIL import Image
from io import BytesIO
import aiogram.utils.markdown as fmt
from aiogram.utils.exceptions import BotBlocked, PollOptionsLengthTooLong
import aioschedule
import pyrebase
from aiogram import Bot, Dispatcher, executor, types
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

firebaseConfig = {
    "apiKey": "AIzaSyA6eRXO1BLuAZ3OTLvSwKbtj85Ow9E-gMo",
    "authDomain": "bonchbot.firebaseapp.com",
    "databaseURL": "https://bonchbot-default-rtdb.firebaseio.com",
    "projectId": "bonchbot",
    "storageBucket": "bonchbot.appspot.com",
    "messagingSenderId": "25320630490",
    "appId": "1:25320630490:web:c51273f6cf9e7a7fc3dde3"
    }
firebase = pyrebase.initialize_app(firebaseConfig)
db= firebase.database()

s=Service(ChromeDriverManager().install())
url = 'https://lk.sut.ru/cabinet/'
chrome_options = Options()
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")


#token = Bot(token="2087293427:AAEqHp5QE7BK_7G8JNlDUdbhtKi9EqpMQdI")
token = Bot(token="2057472245:AAHXiB2teJOWQa7CXwH0uLd8cJItn4YvD4A")
bot = Dispatcher(token)



@bot.message_handler(commands="start")
async def start(message: types.Message):
    user_id = message.from_user.id
    if str(user_id) in list(db.child("Users").get().val().keys()):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Расписание сегодня", "Расписание на неделю", "Мои оценки"]
        keyboard.add(*buttons)
        await message.answer("Вы уже зарегистрированы", reply_markup=keyboard)
    else:
        await message.answer("Введите логин от лк", reply_markup=types.ReplyKeyboardRemove())

def getMarks(userId):
    user = db.child("Users").child(str(userId)).get().val()
    driver = webdriver.Chrome(service = s, options = chrome_options)
    driver.get(url)
    try:
        login = WebDriverWait(driver, 1).until(
        EC.visibility_of_element_located((By.NAME, "users")))
    finally:
        login.send_keys(user["login"])
        driver.find_element(By.NAME,"parole").send_keys(user["password"])
        driver.find_element(By.NAME, "logButton").click()
        time.sleep(0.5)
        try: 
            button = ""
            button = WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.CLASS_NAME, "lm_item")))
        except Exception as e:
            print("Except" + str(e))
            driver.quit()
            pass
        else:
            button.click()
            try:
                diary = ""
                diary = WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.LINK_TEXT, "Дневник")))
            except Exception as e:
                print("Except" + str(e))
                driver.quit()
                pass
            else:
                diary.click()
                element = WebDriverWait(driver, 1).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, '[class="smalltab simple-little-table"]')))
                #driver.maximize_window()
                S = [element.location['x']+element.size['width']+40, element.location['y']+element.size['height']]
                driver.set_window_size(S[0],S[1]) # May need manual adjustment
                element.screenshot('sss.png')
                driver.quit()
                return ("sss.png")
getMarks("480420304")
@bot.message_handler(lambda message: message.text=="Мои оценки")
async def sendMarks(message: types.Message):
    await message.answer_document(open(getMarks(message.from_user.id), "rb"))

@bot.message_handler(lambda message: message.text != "Да" and  message.text != "Нет" and  message.text != "ранд"  and  message.text != "Хуй" and message.text != "Расписание сегодня" and message.text != "Расписание на неделю" and message.text != "Мои оценки")
async def auth(message: types.Message):        
    user_id = message.from_user.id
    if db.child("Users").child(user_id).get().val()!=None and len(list(db.child("Users").child(user_id).get().val()))<2:
        db.child("Users").child(user_id).update({"password": message.text})
        await message.answer(db.child("Users").child(user_id).get().val()["login"] + " " + db.child("Users").child(user_id).get().val()["password"])
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Да", "Нет"]
        keyboard.add(*buttons)
        await message.answer("Все верно?", reply_markup=keyboard)
    elif db.child("Users").child(user_id).get().val()==None:
        db.child("Users").child(user_id).update({"login": message.text})
        await message.answer("Введите пароль от лк")

@bot.message_handler(lambda message: message.text == "Да")
async def true(message: types.Message):
    await message.answer("Проверка...")
    user_id = message.from_user.id
    login = db.child("Users").child(user_id).get().val()["login"]
    password= db.child("Users").child(user_id).get().val()["password"]
    if checkAuth(login, password):
        await message.answer("Вы зарегистрированы!", reply_markup=types.ReplyKeyboardRemove())
    else: 
        db.child("Users").child(user_id).remove()
        keyboards = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button = ["/start"]
        keyboards.add(*button)
        await message.answer("Введенные данные неверны!", reply_markup=keyboards)

@bot.message_handler(lambda message: message.text == "Нет")
async def false(message: types.Message):
    user_id = message.from_user.id
    db.child("Users").child(user_id).remove()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Расписание сегодня", "Расписание на неделю"]
    keyboard.add(*buttons)
    await message.answer("Введите логин от лк", reply_markup=keyboard)

@bot.message_handler(lambda message: message.text == "Хуй")
async def zxc(message: types.Message):
    await message.reply("Сам хуй!")

@bot.message_handler(lambda message: message.text == "Расписание на неделю")
async def scheduleWeek(message: types.Message):
    user_id = message.from_user.id
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text="Предыдущая неделя", callback_data="previousWeek"), types.InlineKeyboardButton(text="Следующая неделя", callback_data="nextWeek")]
    kb.add(*buttons)
    numberWeek = db.child("Number Week").get().val()
    answerSchedule = db.child("Table").child(user_id).child(numberWeek).get().val()
    answer = fmt.hbold("Неделя №") + fmt.hbold(str(numberWeek)) + "\n" + answerSchedule
    if answerSchedule!=None:
        answer = fmt.hbold("Неделя №") + fmt.hbold(str(numberWeek)) + "\n" + answerSchedule
        await message.answer(answer, parse_mode=types.ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    else:   await message.answer("Нет данных", reply_markup=kb)


@bot.callback_query_handler(text="nextWeek")
async def send_random_value(call: types.CallbackQuery):
    numberWeek = int(call.message.text.split("№")[1].split("\n")[0])
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text="Предыдущая неделя", callback_data="previousWeek"), types.InlineKeyboardButton(text="Следующая неделя", callback_data="nextWeek")]
    kb.add(*buttons)
    answerSchedule = db.child("Table").child(call.from_user.id).child(numberWeek+1).get().val()
    if answerSchedule!=None:
        answer = fmt.hbold("Неделя №") + fmt.hbold(str(numberWeek+1)) +  "\n" + answerSchedule
        await call.message.edit_text(answer, parse_mode=types.ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    else:   await call.message.edit_text(fmt.hbold("Неделя №") + fmt.hbold(str(numberWeek+1)) +  2*"\n" + "Данных нет.", parse_mode=types.ParseMode.HTML, reply_markup=kb)

@bot.callback_query_handler(text="previousWeek")
async def send_random_value(call: types.CallbackQuery):
    numberWeek = int(call.message.text.split("№")[1].split("\n")[0])
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text="Предыдущая неделя", callback_data="previousWeek"), types.InlineKeyboardButton(text="Следующая неделя", callback_data="nextWeek")]
    kb.add(*buttons)
    answerSchedule = db.child("Table").child(call.from_user.id).child(numberWeek-1).get().val()
    if numberWeek==1:   return
    if answerSchedule!=None:
        answer = fmt.hbold("Неделя №") + fmt.hbold(str(numberWeek-1)) +  "\n" + answerSchedule
        await call.message.edit_text(answer, parse_mode=types.ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    else:   await call.message.edit_text(fmt.hbold("Неделя №") + fmt.hbold(str(numberWeek-1)) +  2*"\n" + "Данных нет.", parse_mode=types.ParseMode.HTML, reply_markup=kb)

@bot.message_handler(lambda message: message.text == "Расписание сегодня")
async def scheduleDay(message: types.Message):
    user_id = message.from_user.id
    schedule = db.child("Users Schedule").child(user_id).get().val()
    answer = ""
    if schedule!=None:
        for les in schedule:
            if ("Спортивные площадки" in les[2]) or ("Дистанционно" in les[2]):  cab = les[2]
            else: cab = fmt.hlink(url="https://www.nav.sut.ru/?cab=k" + les[2].split("/")[-1] + "-" + les[2].split(";")[0].replace("-", "a"), title=les[2].split(";")[0].replace("-", "/")+"/"+les[2].split("/")[-1])
            answer += (les[0]+ "\n" + "     " + fmt.hbold(les[1].split("\n")[0]) + "\n" + "       " + fmt.hitalic(les[1].split("\n")[1])+ "\n" + "     " + cab+"\n" + "     " +les[3] + 2*"\n")
        await message.answer(answer, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
    else:   await message.answer("Сегодня нет занятий.")


def checkAuth(loginUser, passwordUser):
    driver = webdriver.Chrome(service = s, options = chrome_options)
    driver.get(url)
    try:
        login = WebDriverWait(driver, 1).until(
        EC.visibility_of_element_located((By.NAME, "users")))
    finally:
        login.send_keys(loginUser)
        driver.find_element(By.NAME,"parole").send_keys(passwordUser)
        driver.find_element(By.NAME, "logButton").click()
        time.sleep(0.5)
        try: 
            driver.find_element(By.CLASS_NAME, "lm_item")
        except UnexpectedAlertPresentException:
            driver.quit()
            return False
        else:
            driver.quit()
            return True

@bot.callback_query_handler(text="+")
async def send_random_value(call: types.CallbackQuery):
    teacher = call.message.text.split("\n")[-1][5:]+"|"+call.message.text.split("\n")[0]
    user_id = call.from_user.id
    timeLesson = call.message.text.split("\n")[0].split("-")[0].split("(")[-1].replace(".", ":")
    timeLesson = timeLesson.split(":")
    timeLesson = str(int(timeLesson[0])-3) + ":" + timeLesson[1]
    if len(timeLesson)==4:  timeLesson = "0"+timeLesson
    db.child("Schedule").child(timeLesson).update({user_id: teacher})
    admin = 2125738023
    await bot.bot.send_message(admin, user_id+teacher)


@bot.callback_query_handler(text="-")
async def send_random_value(call: types.CallbackQuery):
    user_id = call.from_user.id
    timeLesson = call.message.text.split("\n")[0].split("-")[0].split("(")[-1].replace(".", ":")
    timeLesson = timeLesson.split(":")
    timeLesson = str(int(timeLesson[0])-3) + ":" + timeLesson[1]
    if len(timeLesson)==4:  timeLesson = "0"+timeLesson
    db.child("Schedule").child(timeLesson).child(user_id).remove()

async def senMessage():
    admin = 2125738023
    await bot.bot.send_message(admin, f"*Рассылка началась \nБот оповестит когда рассылку закончит*", parse_mode='Markdown')
    receive_users, block_users = 0, 0
    users = db.child("Users").get().each()
    for user in users:
        kb = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(text="Да", callback_data="+"), types.InlineKeyboardButton(text="Нет", callback_data="-")]
        kb.add(*buttons)
        lesson = db.child("Users Schedule").child(user.key()).get().val()
        if lesson!=None:
            try:
                await bot.bot.send_message(user.key(), "На каких парах отмечать? Пожалуйста, не выбирайте пары, на которых преподаватель не начинает занятие.")
                for les in lesson:
                    if ("Спортивные площадки" in les[2]) or ("Дистанционно" in les[2]):  cab = les[2]
                    else: cab = fmt.hlink(url="https://www.nav.sut.ru/?cab=k" + les[2].split("/")[-1] + "-" + les[2].split(";")[0].replace("-", "a"), title=les[2].split(";")[0].replace("-", "/")+"/"+les[2].split("/")[-1])
                    await bot.bot.send_message(user.key(), les[0]+ "\n" + "     " + fmt.hbold(les[1].split("\n")[0]) + "\n" + "       " + fmt.hitalic(les[1].split("\n")[1])+ "\n" + "     " + cab+"\n" + "     " +les[3], parse_mode=types.ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
                receive_users+=1
            except BotBlocked:
                db.child("Users").child(user.key()).remove()
                db.child("Users Schedule").child(user.key()).remove()
                block_users += 1
    await bot.bot.send_message(admin, f"*Рассылка была завершена *\n"
                                                              f"получили сообщение: *{receive_users}*\n"
                                                              f"заблокировали бота: *{block_users}*\n", parse_mode='Markdown')
async def scheduler():
    aioschedule.every().day.at("05:30").do(senMessage)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    executor.start_polling(bot, skip_updates=False, on_startup=on_startup)

