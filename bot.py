// ============================================================
// ИГРА "ГОРОДА" с уровнями сложности, статистикой и банами
// ============================================================

// ---------- БАЗА ГОРОДОВ (по уровням) ----------
const CITIES_EASY = [
  "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
  "Нижний Новгород", "Челябинск", "Омск", "Самара", "Ростов-на-Дону",
  "Уфа", "Красноярск", "Воронеж", "Пермь", "Волгоград",
  "Краснодар", "Саратов", "Тюмень", "Тольятти", "Ижевск",
  "Барнаул", "Иркутск", "Ульяновск", "Хабаровск", "Владивосток",
  "Ярославль", "Махачкала", "Томск", "Оренбург", "Кемерово",
  "Новокузнецк", "Рязань", "Астрахань", "Набережные Челны", "Пенза",
  "Липецк", "Киров", "Чебоксары", "Калининград", "Тула",
  "Курск", "Ставрополь", "Сочи", "Тверь", "Магнитогорск",
  "Иваново", "Брянск", "Белгород", "Сургут", "Владимир"
];

const CITIES_MEDIUM = CITIES_EASY.concat([
  "Абакан", "Ангарск", "Архангельск", "Бийск", "Благовещенск",
  "Братск", "Великий Новгород", "Владикавказ", "Вологда", "Грозный",
  "Дзержинск", "Елец", "Жуковский", "Златоуст", "Иваново",
  "Йошкар-Ола", "Калуга", "Кемерово", "Киров", "Коломна",
  "Комсомольск-на-Амуре", "Королёв", "Кострома", "Курган", "Курск",
  "Липецк", "Люберцы", "Магнитогорск", "Мытищи", "Набережные Челны",
  "Нефтекамск", "Нефтеюганск", "Нижневартовск", "Нижний Тагил", "Новокузнецк",
  "Новороссийск", "Норильск", "Орёл", "Оренбург", "Орск",
  "Пенза", "Пермь", "Подольск", "Прокопьевск", "Псков",
  "Пятигорск", "Рубцовск", "Рыбинск", "Рязань", "Салават",
  "Северодвинск", "Смоленск", "Стерлитамак", "Сызрань", "Тамбов",
  "Тобольск", "Томск", "Улан-Удэ", "Уссурийск", "Хабаровск",
  "Чебоксары", "Череповец", "Чита", "Шахты", "Щёлково",
  "Энгельс", "Южно-Сахалинск", "Якутск", "Ярославль"
]);

// Сложный уровень — добавим ещё мировые города (транслитом или русскими названиями)
const CITIES_HARD = CITIES_MEDIUM.concat([
  "Нью-Йорк", "Лос-Анджелес", "Лондон", "Париж", "Токио",
  "Шанхай", "Пекин", "Сидней", "Мельбурн", "Дубай",
  "Берлин", "Рим", "Мадрид", "Лиссабон", "Амстердам",
  "Брюссель", "Вена", "Цюрих", "Женева", "Стокгольм",
  "Осло", "Хельсинки", "Копенгаген", "Рейкьявик", "Монреаль",
  "Торонто", "Чикаго", "Даллас", "Майами", "Сан-Франциско",
  "Бостон", "Вашингтон", "Мехико", "Буэнос-Айрес", "Лима",
  "Сантьяго", "Каракас", "Богота", "Кито", "Ла-Пас",
  "Асунсьон", "Монтевидео", "Йоханнесбург", "Каир", "Найроби",
  "Лагос", "Тунис", "Алжир", "Триполи", "Касабланка"
]);

// ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ГОРОДАМИ ----------
function normalizeCity(name) {
  return name.trim().toLowerCase();
}

function getLastLetter(city) {
  // Последняя буква (игнорируем мягкий/твёрдый знак, но для простоты оставим как есть)
  return city.slice(-1).toLowerCase();
}

function getCitiesByLevel(level) {
  if (level === 'easy') return CITIES_EASY;
  if (level === 'medium') return CITIES_MEDIUM;
  return CITIES_HARD;
}

// ---------- ОБРАБОТЧИК ВЕБ-ЗАПРОСОВ ----------
export default {
  async fetch(request, env) {
    const BOT_TOKEN = env.BOT_TOKEN;
    const KV = env.CITY_BOT; // твой KV Namespace
    const url = new URL(request.url);

    // ---- Вебхук от Telegram ----
    if (url.pathname === '/webhook' && request.method === 'POST') {
      try {
        const body = await request.json();
        const message = body.message;
        const callback = body.callback_query;

        // Обработка callback (кнопки)
        if (callback) {
          await handleCallback(callback, BOT_TOKEN, KV);
          return new Response('OK', { status: 200 });
        }

        // Обработка обычных сообщений
        if (message && message.text) {
          await handleMessage(message, BOT_TOKEN, KV);
          return new Response('OK', { status: 200 });
        }

        return new Response('Ignored', { status: 200 });
      } catch (e) {
        return new Response('Error: ' + e.message, { status: 500 });
      }
    }

    // ---- Корневой путь для проверки ----
    return new Response('City Bot is running!', { status: 200 });
  }
};

// ---------- ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ----------
async function handleMessage(message, BOT_TOKEN, KV) {
  const chatId = message.chat.id;
  const userId = message.from.id;
  const text = message.text.trim();

  // Проверка бана
  const bannedList = await KV.get('banned', 'json') || [];
  if (bannedList.includes(userId)) {
    await sendMessage(chatId, '🚫 Ты забанен. Обратись к администратору.', BOT_TOKEN);
    return;
  }

  // Команды админа (только для твоего ID)
  if (userId === 600630325) {
    if (text.startsWith('/ban ')) {
      const targetId = parseInt(text.split(' ')[1]);
      if (!isNaN(targetId)) {
        await banUser(targetId, KV);
        await sendMessage(chatId, `✅ Пользователь ${targetId} забанен.`, BOT_TOKEN);
      }
      return;
    }
    if (text.startsWith('/unban ')) {
      const targetId = parseInt(text.split(' ')[1]);
      if (!isNaN(targetId)) {
        await unbanUser(targetId, KV);
        await sendMessage(chatId, `✅ Пользователь ${targetId} разбанен.`, BOT_TOKEN);
      }
      return;
    }
  }

  // Обработка команд игры
  if (text === '/start') {
    await sendStart(chatId, BOT_TOKEN);
    return;
  }

  if (text === '/stats') {
    await sendStats(userId, chatId, BOT_TOKEN, KV);
    return;
  }

  if (text === '/newgame') {
    await newGame(userId, chatId, BOT_TOKEN, KV);
    return;
  }

  if (text === '/giveup') {
    await giveUp(userId, chatId, BOT_TOKEN, KV);
    return;
  }

  // Если текст — это название города (игра активна)
  await processCityGuess(userId, chatId, text, BOT_TOKEN, KV);
}

// ---------- ОБРАБОТЧИК НАЖАТИЙ КНОПОК ----------
async function handleCallback(callback, BOT_TOKEN, KV) {
  const chatId = callback.message.chat.id;
  const userId = callback.from.id;
  const data = callback.data;

  // Проверка бана
  const bannedList = await KV.get('banned', 'json') || [];
  if (bannedList.includes(userId)) {
    await sendMessage(chatId, '🚫 Ты забанен.', BOT_TOKEN);
    return;
  }

  if (data === 'newgame') {
    await newGame(userId, chatId, BOT_TOKEN, KV);
    await answerCallback(callback.id, 'Новая игра начата!', BOT_TOKEN);
    return;
  }

  if (data === 'stats') {
    await sendStats(userId, chatId, BOT_TOKEN, KV);
    await answerCallback(callback.id, '', BOT_TOKEN);
    return;
  }

  if (data === 'giveup') {
    await giveUp(userId, chatId, BOT_TOKEN, KV);
    await answerCallback(callback.id, 'Ты сдался', BOT_TOKEN);
    return;
  }

  if (data.startsWith('level_')) {
    const level = data.replace('level_', '');
    await setLevel(userId, chatId, level, BOT_TOKEN, KV);
    await answerCallback(callback.id, `Уровень сложности: ${level}`, BOT_TOKEN);
    return;
  }
}

// ---------- ОСНОВНАЯ ИГРОВАЯ ЛОГИКА ----------

async function processCityGuess(userId, chatId, city, BOT_TOKEN, KV) {
  // Получаем данные пользователя
  const userKey = `user_${userId}`;
  let userData = await KV.get(userKey, 'json');
  if (!userData) {
    userData = { score: 0, wins: 0, losses: 0, level: 'medium', game: null };
  }

  const game = userData.game;
  if (!game || !game.active) {
    await sendMessage(chatId, '⚠️ Нет активной игры. Напиши /newgame или нажми «Новая игра».', BOT_TOKEN);
    return;
  }

  // Проверяем город
  const cityNorm = normalizeCity(city);
  const citiesList = getCitiesByLevel(userData.level || 'medium');
  const citiesSet = new Set(citiesList.map(c => normalizeCity(c)));

  if (!citiesSet.has(cityNorm)) {
    await sendMessage(chatId, `❌ Город «${city}» не найден в моей базе для выбранного уровня. Попробуй другой.`, BOT_TOKEN);
    return;
  }

  if (game.usedCities && game.usedCities.includes(cityNorm)) {
    await sendMessage(chatId, `⚠️ Город «${city}» уже называли. Назови другой.`, BOT_TOKEN);
    return;
  }

  const lastLetter = getLastLetter(city);
  if (lastLetter !== game.lastLetter) {
    await sendMessage(chatId, `❌ Город должен начинаться на букву *«${game.lastLetter.toUpperCase()}»*!`, BOT_TOKEN, 'Markdown');
    return;
  }

  // Город принят
  game.usedCities.push(cityNorm);
  // Ищем ответ бота
  const available = citiesList.filter(c => {
    const norm = normalizeCity(c);
    return norm.startsWith(lastLetter) && !game.usedCities.includes(norm);
  });

  if (available.length === 0) {
    // Бот не может ответить -> победа игрока
    game.active = false;
    userData.wins = (userData.wins || 0) + 1;
    userData.score = (userData.score || 0) + 1;
    await KV.put(userKey, JSON.stringify(userData));
    await sendMessage(chatId,
      `🎉 *Поздравляю! Ты выиграл!*\n`
      + `Названо городов: ${game.usedCities.length}\n`
      + `Очков: +1. Всего: ${userData.score}\n`
      + `Побед: ${userData.wins}`,
      BOT_TOKEN, 'Markdown'
    );
    // Предлагаем новую игру
    await sendGameMenu(chatId, BOT_TOKEN);
    return;
  }

  // Бот выбирает город
  const botCity = available[Math.floor(Math.random() * available.length)];
  game.usedCities.push(normalizeCity(botCity));
  const newLastLetter = getLastLetter(botCity);
  game.lastLetter = newLastLetter;
  await KV.put(userKey, JSON.stringify(userData));

  await sendMessage(chatId,
    `✅ Твой город *${city}* принят!\n`
    + `Мой ответ: *${botCity}*\n\n`
    + `Теперь назови город на букву *«${newLastLetter.toUpperCase()}»*.\n`
    + `Список использованных: ${game.usedCities.length} городов.`,
    BOT_TOKEN, 'Markdown'
  );
}

// ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------

async function sendMessage(chatId, text, BOT_TOKEN, parse_mode = null) {
  const payload = { chat_id: chatId, text };
  if (parse_mode) payload.parse_mode = parse_mode;
  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

async function answerCallback(callbackId, text, BOT_TOKEN) {
  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/answerCallbackQuery`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ callback_query_id: callbackId, text })
  });
}

async function sendStart(chatId, BOT_TOKEN) {
  const text = `🏙️ *Добро пожаловать в игру «Города»!*\n\n`
    + `Я называю город, а ты — следующий на последнюю букву.\n`
    + `Уровни сложности: легкий (50 городов), средний (150), сложный (300+).\n`
    + `Для начала выбери уровень или сразу нажми «Новая игра».\n\n`
    + `/newgame — начать игру\n`
    + `/stats — статистика\n`
    + `/giveup — сдаться\n`
    + `/level <easy|medium|hard> — сменить уровень`;
  const keyboard = {
    inline_keyboard: [
      [{ text: '🆕 Новая игра', callback_data: 'newgame' }],
      [{ text: '📊 Статистика', callback_data: 'stats' }, { text: '🏳️ Сдаться', callback_data: 'giveup' }],
      [{ text: '🟢 Лёгкий', callback_data: 'level_easy' }, { text: '🟡 Средний', callback_data: 'level_medium' }, { text: '🔴 Сложный', callback_data: 'level_hard' }]
    ]
  };
  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: 'Markdown', reply_markup: keyboard })
  });
}

async function sendGameMenu(chatId, BOT_TOKEN) {
  const keyboard = {
    inline_keyboard: [
      [{ text: '🆕 Новая игра', callback_data: 'newgame' }],
      [{ text: '📊 Статистика', callback_data: 'stats' }, { text: '🏳️ Сдаться', callback_data: 'giveup' }]
    ]
  };
  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text: 'Выбери действие:', reply_markup: keyboard })
  });
}

async function newGame(userId, chatId, BOT_TOKEN, KV) {
  const userKey = `user_${userId}`;
  let userData = await KV.get(userKey, 'json');
  if (!userData) {
    userData = { score: 0, wins: 0, losses: 0, level: 'medium', game: null };
  }

  const level = userData.level || 'medium';
  const citiesList = getCitiesByLevel(level);
  const available = citiesList.filter(c => {
    // Можно добавить проверку, чтобы не начинать с уже использованных
    return true; // Для простоты берём любой
  });
  const firstCity = available[Math.floor(Math.random() * available.length)];
  const lastLetter = getLastLetter(firstCity);

  userData.game = {
    active: true,
    usedCities: [normalizeCity(firstCity)],
    lastLetter: lastLetter,
    level: level
  };
  await KV.put(userKey, JSON.stringify(userData));

  await sendMessage(chatId,
    `🗺️ Начинаем игру (уровень: *${level}*)!\n`
    + `Я называю: *${firstCity}*\n\n`
    + `Твой ход! Напиши город на букву *«${lastLetter.toUpperCase()}»*.\n`
    + `Если хочешь сдаться — нажми кнопку.`,
    BOT_TOKEN, 'Markdown'
  );
  await sendGameMenu(chatId, BOT_TOKEN);
}

async function giveUp(userId, chatId, BOT_TOKEN, KV) {
  const userKey = `user_${userId}`;
  let userData = await KV.get(userKey, 'json');
  if (!userData || !userData.game || !userData.game.active) {
    await sendMessage(chatId, 'У тебя нет активной игры.', BOT_TOKEN);
    return;
  }

  userData.game.active = false;
  userData.losses = (userData.losses || 0) + 1;
  userData.score = (userData.score || 0) - 1;
  await KV.put(userKey, JSON.stringify(userData));

  await sendMessage(chatId,
    `🏳️ Ты сдался.\n`
    + `Названо городов: ${userData.game.usedCities.length}\n`
    + `Очков: -1. Всего: ${userData.score}\n`
    + `Поражений: ${userData.losses}`,
    BOT_TOKEN
  );
  await sendGameMenu(chatId, BOT_TOKEN);
}

async function sendStats(userId, chatId, BOT_TOKEN, KV) {
  const userKey = `user_${userId}`;
  let userData = await KV.get(userKey, 'json');
  if (!userData) {
    userData = { score: 0, wins: 0, losses: 0, level: 'medium' };
  }
  await sendMessage(chatId,
    `📊 *Твоя статистика:*\n`
    + `🏆 Очков: ${userData.score}\n`
    + `🎯 Побед: ${userData.wins || 0}\n`
    + `💔 Поражений: ${userData.losses || 0}\n`
    + `🎚️ Уровень: ${userData.level || 'medium'}`,
    BOT_TOKEN, 'Markdown'
  );
}

async function setLevel(userId, chatId, level, BOT_TOKEN, KV) {
  const userKey = `user_${userId}`;
  let userData = await KV.get(userKey, 'json');
  if (!userData) {
    userData = { score: 0, wins: 0, losses: 0, level: level };
  } else {
    userData.level = level;
  }
  // Если есть активная игра — завершаем её (можно предложить начать заново)
  if (userData.game && userData.game.active) {
    userData.game.active = false;
    // Поражение за смену уровня? Можно не штрафовать.
  }
  await KV.put(userKey, JSON.stringify(userData));
  await sendMessage(chatId, `✅ Уровень сложности изменён на *${level}*.\nТеперь начни новую игру.`, BOT_TOKEN, 'Markdown');
}

async function banUser(userId, KV) {
  let banned = await KV.get('banned', 'json') || [];
  if (!banned.includes(userId)) {
    banned.push(userId);
    await KV.put('banned', JSON.stringify(banned));
  }
}

async function unbanUser(userId, KV) {
  let banned = await KV.get('banned', 'json') || [];
  banned = banned.filter(id => id !== userId);
  await KV.put('banned', JSON.stringify(banned));
}