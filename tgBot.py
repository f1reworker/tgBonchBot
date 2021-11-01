from aiogram import Bot, Dispatcher, types, executor
import time
import aiogram.utils.markdown as fmt

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pyrebase

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


token = Bot(token="2087293427:AAEqHp5QE7BK_7G8JNlDUdbhtKi9EqpMQdI")
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

@bot.message_handler(lambda message: message.text != "Да" and  message.text != "Нет"  and  message.text != "Хуй" and message.text != "Расписание сегодня" and message.text != "Расписание на неделю")
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
    message.reply("Сам хуй!")

@bot.message_handler(lambda message: message.text == "Расписание на неделю")
async def false(message: types.Message):
    user_id = message.from_user.id
    parseTable(db.child("Users").child(user_id).get().val(), user_id)

@bot.message_handler(lambda message: message.text == "Расписание сегодня")
async def false(message: types.Message):
    user_id = message.from_user.id
    schedule = db.child("Users Schedule").child(user_id).get().val()
    answer = ""
    for i in range(0, len(schedule)):
        answer += (schedule[i][0]+ 2*"\n" + fmt.hbold(schedule[i][1])+ "\n" + schedule[i][2]+"\n" +fmt.hcode(schedule[i][3]) + 3*"\n")
    await message.answer(answer, parse_mode=types.ParseMode.HTML)

def parseTable(user, user_id):
    driver = webdriver.Chrome(service = s, options = chrome_options)
    driver.get(url)
    try:
        login = WebDriverWait(driver, 1).until(
        EC.visibility_of_element_located((By.NAME, "users")))
    finally:
        login.send_keys(user["login"])
        driver.find_element(By.NAME,"parole").send_keys(user["password"])
        driver.find_element(By.NAME, "logButton").click()
        try:
            button = WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.CLASS_NAME, "lm_item")))
        finally:
            button.click()
            try:
                sch = WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.LINK_TEXT, "Расписание")))
            finally:
                sch.click()
                table = WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="rightpanel"]/div/table/tbody')))
                rows = table.find_elements(By.TAG_NAME, "tr")
                key = ""
                for row in rows:
                    matrixColumn = []
                    column = row.find_elements(By.TAG_NAME, "td")
                    if len(column)==1:
                        key = column[0].text.split("\n")[1].replace(".", "-")
                    else:
                        for col in column:
                            matrixColumn.append(col.text.replace("\n", " "))
                        db.child("Users Schedule").child(user_id).update({key: str(matrixColumn)})
                
                    



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
executor.start_polling(bot, skip_updates=True)