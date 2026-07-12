import vk_api
import time
import json

# ======= КОНФИГ =======
TOKEN = "vk1.a.YvDaIw4ocpDRQYO-y4uM8XqGPz5MviwLjEw41t3DkFdgU-Bqhd_ugtyvVx2V93OZiYZFuUPJW1mPHyyCY_FvxQj4mzSQ1Np0tPMQp-cj0pZ-wcdeo118f5IbMIT4yGGMHg3MX4l4FMEx1zNsU95krh8Zi4JLXjbxWpYLW_Vz7VCt7jTJuDFmPcoIW5ibawDgd7cJrwH-U8bDMZO0mqaIXw"
MY_ID = 621585494
# =======================

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()

def get_ai_response(text):
    # ЗДЕСЬ ПОТОМ ВСТАВИШЬ ВЫЗОВ МИСТРАЛ ИЛИ GPT
    return f"Ответ на твоё сообщение: {text}"

def send_message(peer_id, text):
    try:
        vk.messages.send(peer_id=peer_id, message=text[:4096], random_id=0)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def handle_command(text, peer_id):
    if text.startswith("/set_prompt "):
        new_prompt = text.replace("/set_prompt ", "").strip()
        with open("prompt.txt", "w", encoding="utf-8") as f:
            f.write(new_prompt)
        send_message(peer_id, "✅ Промт обновлён.")
        return True
    if text == "/stats":
        send_message(peer_id, "✅ Бот работает.")
        return True
    return False

print("✅ Бот запущен!")

while True:
    try:
        dialogs = vk.messages.getConversations(filter="unread", count=30)
        
        for item in dialogs.get('items', []):
            peer_id = item['conversation']['peer']['id']
            
            history = vk.messages.getHistory(peer_id=peer_id, count=5, rev=0)
            
            for msg in history.get('items', []):
                if msg['from_id'] != MY_ID:
                    text = msg.get('text', '').strip()
                    if not text:
                        continue
                    
                    # Команды от админа
                    if text.startswith("/") and msg['from_id'] == MY_ID:
                        handle_command(text, peer_id)
                        continue
                    
                    # Ответ ИИ
                    answer = get_ai_response(text)
                    send_message(peer_id, answer)
                    break
                    
    except Exception as e:
        print(f"Ошибка: {e}")
    
    time.sleep(3)