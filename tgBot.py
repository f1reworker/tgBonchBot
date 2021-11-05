
import asyncio
import time

import aiogram.utils.markdown as fmt
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

numberWeek = 0
#token = Bot(token="2087293427:AAEqHp5QE7BK_7G8JNlDUdbhtKi9EqpMQdI")
token = Bot(token="2057472245:AAHXiB2teJOWQa7CXwH0uLd8cJItn4YvD4A")
bot = Dispatcher(token)
@bot.message_handler(commands="start")
async def start(message: types.Message):
    user_id = message.from_user.id
    if str(user_id) in list(db.child("Users").get().val().keys()):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Расписание сегодня", "Расписание на неделю"]
        keyboard.add(*buttons)
        await message.answer("Вы уже зарегистрированы", reply_markup=keyboard)
    else:
        await message.answer("Введите логин от лк", reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(lambda message: message.text != "Да" and  message.text != "Нет" and  message.text != "ранд"  and  message.text != "Хуй" and message.text != "Расписание сегодня" and message.text != "Расписание на неделю")
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

#TODO докинуть номер недели, вытаскивать в изменении
@bot.message_handler(lambda message: message.text == "Расписание на неделю")
async def scheduleWeek(message: types.Message):
    await message.answer("Смотрим Ваше расписание.")
    user_id = message.from_user.id
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text="Предыдущая неделя", callback_data="previousWeek"), types.InlineKeyboardButton(text="Следующая неделя", callback_data="nextWeek")]
    kb.add(*buttons)
    numberWeek = 0
    answer = db.child("Table").child(user_id).child(numberWeek).get().val()
    if answer!=None:
        await message.answer(answer, parse_mode=types.ParseMode.HTML, reply_markup=kb)
    else:   await message.answer("Нет данных", reply_markup=kb)


@bot.callback_query_handler(text="nextWeek")
async def send_random_value(call: types.CallbackQuery):
    print(call)
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text="Предыдущая неделя", callback_data="previousWeek"), types.InlineKeyboardButton(text="Следующая неделя", callback_data="nextWeek")]
    kb.add(*buttons)
    await call.message.edit_text(db.child("Table").child(call.from_user.id).child(1).get().val(), parse_mode=types.ParseMode.HTML, reply_markup=kb)

@bot.callback_query_handler(text="previousWeek")
async def send_random_value(call: types.CallbackQuery):
    await call.message.answer("p[o[[po[")

@bot.message_handler(lambda message: message.text == "Расписание сегодня")
async def scheduleDay(message: types.Message):
    user_id = message.from_user.id
    schedule = db.child("Users Schedule").child(user_id).get().val()
    answer = ""
    if schedule!=None:
        for i in range(0, len(schedule)):
            answer += (schedule[i][0]+ 2*"\n" + fmt.hbold(schedule[i][1])+ "\n" + schedule[i][2]+"\n" +fmt.hcode(schedule[i][3]) + 3*"\n")
        await message.answer(answer, parse_mode=types.ParseMode.HTML)
    else:   await message.answer("Сегодня нет занятий.")
@bot.poll_answer_handler()
async def pollAnswer(answer: types.PollAnswer):
    user_id = answer["user"]["id"]
    timeSched = []
    for i in answer["option_ids"]:
        timeLesson = db.child("Users Schedule").child(user_id).child(int(i)).get().val()
        if timeLesson==None:    return
        timeLesson = timeLesson[0].split("-")[0].split("(")[-1].replace(".", ":")
        timeLesson = timeLesson.split(":")
        timeLesson = str(int(timeLesson[0])-3) + ":" + timeLesson[1]
        if len(timeLesson)==4:  timeLesson = "0"+timeLesson
        timeSched.append(timeLesson)
    for q in range (0, len(timeSched)):
            if timeSched[q]==timeSched[q-1] and len(timeSched)!=1:
                Sched = timeSched[q].split(":")
                timeSched = Sched[0]+":"+str(int(Sched[1])+5)
                if len(timeSched)==4:  timeSched = timeSched.split(":")[0]+":"+"0"+timeSched.split(":")[1]
                db.child("Schedule").child(timeSched).child(user_id).set(False)
                print(timeSched)
            else:
                print(timeSched[q])
                db.child("Schedule").child(timeSched[q]).child(user_id).set(False)
    print(timeSched)


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

async def senMessage():
    users = db.child("Users").get().each()
    for user in users:
        options = []
        lesson = db.child("Users Schedule").child(user.key()).get().val()

        if lesson!=None:    
            for les in lesson:
                if len(les[1])>40:
                    lesone = les[1][:41] + ".."
                else:
                    lesone = les[1]
                options.append(les[0]+" "+ lesone +" "+les[2]+" "+les[3])
            options.append("Не отмечать")
            bot.bot.send_poll(is_anonymous=False, allows_multiple_answers=True, question="На каких парах отмечать? Пожалуйста, не выбирайте пары, на которых преподаватель не начинает занятие. Если ин яз, то тыкнуть на 2 пункта, сорри это мой говнокод, вскоре исправлю.", 
        options=options, chat_id=user.key())
#TODO: добавить время закрытия
async def scheduler():
    aioschedule.every().day.at("13:08").do(senMessage)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    executor.start_polling(bot, skip_updates=False, on_startup=on_startup)

