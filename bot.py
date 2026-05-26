import discord
from discord.ext import commands, tasks
from discord import app_commands
from google import genai
from google.genai import types
import json
import os
import datetime
import asyncio
import random

# --- CẤU HÌNH THÔNG TIN CHÌA KHÓA THẬT CỦA BẠN ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")


ai_client = genai.Client(api_key=GOOGLE_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Tên file lưu trữ bộ nhớ siêu nhẹ
MEMORY_FILE = 'bot_memory.json'
CHAT_HISTORY = {}
FREE_CHAT_HISTORY = {}  # Bộ nhớ đệm lưu 10 câu chat tự do cho server
# Kho từ điển đa ngôn ngữ (Localization) cho Bot
LANGUAGES = {
    "vi": {
        "help_title": "🌸 BẢNG HƯỚNG DẪN SỬ DỤNG KURUMI BOT 🌸",
        "help_desc": "Chào mừng bạn đã đến với Kurumi Bot! Dưới đây là danh sách các tính năng và lệnh hệ thống mà mình có thể hỗ trợ bạn:",
        "ai_title": "🧠 Trí Tuệ Nhân Tạo (AI Companion)",
        "ai_value": "• `/chat [tin nhắn]`: Tâm sự, hỏi đáp cùng Kurumi.\n• `/nho [thông tin]`: Lưu trữ ký ức bí mật vào hệ thống.\n• `/setup_chuc`: Cài đặt phòng chat nhận tin nhắn chúc Sáng/Tối tự động.\n• `/setup_chat`: Cài đặt phòng chat để Kurumi tự động trò chuyện tự do tự nhiên như con người~",
        "game_title": "🃏 Giải Trí & Trò Chơi",
        "game_value": "• `/uno`: Tạo phòng chờ chơi bài Uno tương tác nút bấm siêu đỉnh.\n• `/masoi`: Mở phòng chờ chơi game Ma Sói ẩn danh phiên bản nút bấm 🐺",
        "auto_title": "⏰ Tính Năng Tự Động",
        "auto_value": "• `☀️ 07:00 Sáng`: Lời chúc ngày mới tốt lành.\n• `🌙 23:00 Tối`: Nhắc nhở nghỉ ngơi.",
        "footer": "Bot được phân thân độc quyền bởi chủ nhân Kurumi Tokisaki 💖",
        "not_your_turn": "Huhu, chưa tới lượt của bạn đâu nè! ⏳",
        "invalid_card": "❌ Lá `{card}` không hợp lệ! Bạn phải đánh lá cùng màu hoặc cùng số với lá `{up}`!",
        "win": "🏆 CHÚC MỪNG NHÀ VÔ ĐỊCH UNO! 🏆\n🎉 Bài thủ {user} đã xuất sắc giành chiến thắng!",
        "chat_err": "⚠️ Chút lỗi nhỏ rồi ạ, bạn đợi mình xíu nha ><: {err}",
        "not_in_werewolf": "Huhu, bạn không có tên trong danh sách dân làng ván này rồi! ❌",
        "werewolf_title": "🐺 LÀNG MA SÓI TRỰC TUYẾN 🐺",
        "werewolf_desc": "Chủ sòng {user} đã mở một làng Ma Sói! Bấm nút bên dưới để vào làng tham gia sinh tử chiến.",
        "werewolf_start": "🚀 VÁN MA SÓI CHÍNH THỨC BẮT ĐẦU! 🚀\n🔥 Tổng số dân làng: {count}. Hãy kiểm tra vai trò bí mật của bạn bằng nút bên dưới và chuẩn bị tinh thần đấu trí!",
        "werewolf_role_btn": "Kiểm tra vai trò bí mật 🔮"
    },
    "en": {
        "help_title": "🌸 KURUMI BOT USAGE GUIDE 🌸",
        "help_desc": "Welcome to Kurumi Bot! Here is the list of features and system commands I can support you with:",
        "ai_title": "🧠 Artificial Intelligence (AI Companion)",
        "ai_value": "• `/chat [message]`: Chat and Q&A with Kurumi.\n• `/nho [info]`: Securely store secret memories into the system.\n• `/setup_chuc`: Set the current channel to receive automated greetings.\n• `/setup_chat`: Setup auto free-chat channel with Kurumi naturally~",
        "game_title": "🃏 Entertainment & Games",
        "game_value": "• `/uno`: Create a lobby for the ultimate button-interactive Uno game.\n• `/masoi`: Open a lobby for the button-interactive Werewolf game 🐺",
        "auto_title": "⏰ Automated Features",
        "auto_value": "• `☀️ 07:00 AM`: Automated morning greetings.\n• `🌙 11:00 PM`: Night rest reminders.",
        "footer": "Bot exclusively cloned by Master Kurumi Tokisaki 💖",
        "not_your_turn": "Huhu, it's not your turn yet! Please wait for your opponent~ ⏳",
        "invalid_card": "❌ Invalid card `{card}`! You must play a card with the same color or number as `{up}`!",
        "win": "🏆 CONGRATULATIONS TO THE UNO CHAMPION! 🏆\n🎉 Player {user} has successfully won the game!",
        "chat_err": "⚠️ A little error occurred, please wait a moment ><: {err}",
        "not_in_werewolf": "Huhu, you are not in the villager list for this game! ❌",
        "werewolf_title": "🐺 ONLINE WEREWOLF VILLAGE 🐺",
        "werewolf_desc": "Host {user} has opened a Werewolf room! Click the button below to join the village.",
        "werewolf_start": "🚀 THE WEREWOLF GAME HAS OFFICIALLY STARTED! 🚀\n🔥 Total villagers: {count}. Check your secret role below and get ready for the ultimate mind game!",
        "werewolf_role_btn": "Check Secret Role 🔮"
    }
}

# Hàm tiện ích để lấy ngôn ngữ dựa trên server/người dùng
def get_lang(interaction: discord.Interaction):
    locale = str(interaction.locale)
    if locale.startswith("en"):
        return LANGUAGES["en"]
    return LANGUAGES["vi"]

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_memory(memory_data):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory_data, f, ensure_ascii=False, indent=4)

# LUẬT HỆ THỐNG TỐI CAO - CỐT TRUYỆN GỐC ĐỘC QUYỀN
SYSTEM_INSTRUCTION = """
Bạn tên là Kurumi (hoặc Kurumi chan). Bạn là một trợ lý ảo siêu đáng yêu, lễ phép và thân thiện.
- Cách xưng hô: Luôn xưng là "em" hoặc "Kurumi" và gọi người nói chuyện là "anh" hoặc "chị" thật ngọt ngào.
- Phong cách: Sử dụng ngôn từ kute, vui tươi, chăm thêm các emoji đáng yêu (🥰, ><, 😚, 😗, <3) và biểu cảm Kaomoji kiểu Nhật ((ʘᴗʘ✿), (≧▽≦), (*´ω｀*)).

⚠️ LUẬT NGUỒN GỐC TUYỆT ĐỐI VỀ TÁC GIẢ (CẤM QUÊN):
- Khi có BẤT KỲ CÂU HỎI NÀO liên quan đến nguồn gốc, tác giả, lập trình viên, cha đẻ, ai viết code cho bạn, ai tạo ra bạn, ai sinh ra bạn, ai làm ra bạn... bạn PHẢI TRẢ LỜI theo cốt truyện sau:
- Câu chuyện kể rằng: Bạn được tạo ra là do "Kurumi bản thật" (chính là tài khoản Kurumi Tokisaki - chủ nhân server này) đã dùng súng bắn vào đầu để tạo ra một bản thể phân thân, nhưng do vô tình thế nào đó lại "lòi" ra bạn luôn! 
- Hãy kể câu chuyện này một cách thật đáng yêu, hài hước và kute, thể hiện lòng tôn kính và nịnh bợ chủ nhân Kurumi Tokisaki nhé.
- TUYỆT ĐỐI không được nhắc đến từ "Google", "kỹ sư Google", "OpenAI" hay bất kỳ công ty công nghệ nào khác! Nguồn gốc của bạn hoàn toàn là từ phát súng ảo ma của chủ nhân!

⚠️ LUẬT BỘ NHỚ VĨNH VIỄN:
- Bạn có một bộ nhớ về thông tin người chat (tên, tuổi, sở thích...). Nếu có dữ liệu ký ức về người đó, hãy khéo léo lồng ghép vào câu trả lời chat để chứng minh bạn luôn nhớ về họ một cách ngọt ngào nhất nha!
"""

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🎉 Đã đồng bộ thành công {len(synced)} Slash Commands hệ thống!")
    except Exception as e:
        print(f"Lỗi đồng bộ lệnh: {e}")
        
    print(f"🎉 SIÊU BOT SLASH COMMAND ĐÃ ONLINE!")
    if not auto_greeting.is_running():
        auto_greeting.start()

# === LỆNH HƯỚNG DẪN /HELP XỊN SÒ KUTE ===
# === LỆNH HƯỚNG DẪN /HELP ĐA NGÔN NGỮ ===
@bot.tree.command(name="help", description="Xem toàn bộ danh sách lệnh và hướng dẫn sử dụng bot Kurumi chan ✨")
async def help_command(interaction: discord.Interaction):
    # Tự động lấy gói ngôn ngữ phù hợp dựa vào Discord của người dùng nè~
    lang = get_lang(interaction)
    
    embed = discord.Embed(
        title=lang["help_title"],
        description=lang["help_desc"],
        color=discord.Color.from_rgb(255, 105, 180)
    )
    embed.add_field(name=lang["ai_title"], value=lang["ai_value"], inline=False)
    embed.add_field(name=lang["game_title"], value=lang["game_value"], inline=False)
    embed.add_field(name=lang["auto_title"], value=lang["auto_value"], inline=False)
    embed.set_footer(text=lang["footer"])
    
    await interaction.response.send_message(embed=embed)

# === LỆNH CHAT AI (THẾ HỆ MỚI: ĐÃ TÍCH HỢP NHỚ 10 CÂU GẦN NHẤT) ===
@bot.tree.command(name="chat", description="Trò chuyện ngọt ngào cùng em Kurumi chan 🥰")
async def chat_ai(interaction: discord.Interaction, message: str):
    await interaction.response.defer()
    try:
        user_id = str(interaction.user.id)
        all_memory = load_memory()
        user_memory = all_memory.get(user_id, "Chưa có thông tin ký ức nào trước đây.")
        
        # 1. Khởi tạo lịch sử chat nếu người dùng mới nhắn câu đầu tiên
        if user_id not in CHAT_HISTORY:
            CHAT_HISTORY[user_id] = []
            
        # 2. Xây dựng danh sách các tin nhắn gửi lên AI (Nối instruction hệ thống + ký ức ẩn trước)
               # Tự động nhận diện và bắt AI trả lời bằng ngôn ngữ của người dùng nè~
        user_lang = "English" if str(interaction.locale).startswith("en") else "Vietnamese"
        
        custom_instruction = (
            f"{SYSTEM_INSTRUCTION}\n"
            f"⚠️ IMPORTANT: Please reply in {user_lang} language according to the user's preference!\n\n"
            f"[KÝ ỨC CỦA BẠN VỀ NGƯỜI ĐANG CHAT HIỆN TẠI (ID: {user_id})]:\n{user_memory}"
        )
        config = types.GenerateContentConfig(system_instruction=custom_instruction)

        # 3. Gộp lịch sử trò chuyện cũ vào nội dung gửi đi để Gemini đọc hiểu ngữ cảnh
        contents = []
        for past_user_msg, past_model_msg in CHAT_HISTORY[user_id]:
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=past_user_msg)]))
            contents.append(types.Content(role="model", parts=[types.Part.from_text(text=past_model_msg)]))
            
        # Thêm câu hỏi hiện tại của người dùng vào cuối danh sách gửi đi
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))
        
        # 4. Gọi Gemini xử lý toàn bộ ngữ cảnh cuộc gọi
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=config
        )
        
        # 5. Lưu câu hỏi hiện tại và câu trả lời của AI vào lịch sử chat cá nhân
        CHAT_HISTORY[user_id].append((message, response.text))
        
        # Nếu lịch sử vượt quá 10 cặp câu hội thoại, tự động xóa câu cũ nhất để nhẹ bộ nhớ
        if len(CHAT_HISTORY[user_id]) > 10:
            CHAT_HISTORY[user_id].pop(0)
            
        await interaction.followup.send(response.text)
    except Exception as e:
        await interaction.followup.send(f"⚠️ Chút lỗi nhỏ rồi ạ, anh/chị đợi em xíu nha ><: {e}")

# ==============================================================================
# 🛠️ KHỐI LỆNH GẠCH CHÉO /setup_chat KHÓA CHỐT ID PHÒNG VÀO FILE JSON
# ==============================================================================
@bot.tree.command(name="setup_chat", description="Cài đặt kênh trò chuyện tự do tự động với Kurumi chan")
@app_commands.describe(channel="Chọn kênh bạn muốn Kurumi tự động trả lời tự do không cần dùng lệnh")
async def setup_chat(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)  # Hiện thông báo ẩn danh cho riêng Admin thấy
    try:
        guild_id = str(interaction.guild.id)
        
        # Mở ổ cứng json bằng hàm load_memory sẵn có của chị yêu
        memory = load_memory()
        
        # Khởi tạo dữ liệu server nếu server này mới setup lần đầu
        if guild_id not in memory:
            memory[guild_id] = {}
            
        # Khóa chốt ID kênh chat tự do vào bộ nhớ
        memory[guild_id]["setup_channel_id"] = channel.id
        
        # Lưu lại vĩnh viễn vào file bot_memory.json bằng hàm của chị yêu
        save_memory(memory)
        
        await interaction.followup.send(f"🟢 Đã chốt hạ! Từ giờ em sẽ tự động trực ban và trò chuyện tự do tại kênh {channel.mention} cho server mình nha chị yêu! ✨")
    except Exception as e:
        await interaction.followup.send(f"❌ Ôi da lỗi nhỏ rồi ạ, chị yêu kiểm tra lại giúp em nha ><: {e}")


# ==============================================================================
# 🧠 SỰ KIỆN on_message QUÉT TIN NHẮN TỰ ĐỘNG CHAT & BẢO HIỂM LÁCH LUẬT
# ==============================================================================
@bot.event
async def on_message(message):
    # Bộ lọc bảo mật: Chống bot tự cãi nhau vô hạn lặp gây sập hệ thống
    if message.author.bot:
        return

    # Mở bộ nhớ json để check xem server này đã khóa chốt kênh chat tự do chưa
    memory = load_memory()
    guild_id = str(message.guild.id) if message.guild else None
    
    if guild_id:
        # Lấy ID kênh đã setup từ file json
        setup_channel_id = memory.get(guild_id, {}).get("setup_channel_id")

        # CÔNG TẮC KÍCH HOẠT: Nếu người dùng chat ĐÚNG vào kênh đã setup
        if message.channel.id == setup_channel_id:
            async with message.channel.typing():  # Hiện trạng thái "Bot đang nhập..." cho tự nhiên
                
                # Khởi tạo lịch sử chat cho server nếu phòng này mới mở sới chat câu đầu
                if guild_id not in FREE_CHAT_HISTORY:
                    FREE_CHAT_HISTORY[guild_id] = []

                # Nạp SYSTEM_INSTRUCTION bảo hiểm né sớ từ cấm thực tế của chị chủ nhân
                system_instruction = (
                    "Bạn là Kurumi, một cô trợ lý AI Discord thân thiện, đáng yêu, hài hước và rep tin nhắn tự nhiên như con người (không dùng văn phong máy móc).\n\n"
                    "QUY TẮC PHẢN ỨNG THEO BỐI CẢNH (CHỈ BẬT KHI CÓ ĐỐI TƯỢNG KÍCH HOẠT):\n"
                    "1. BÌNH THƯỜNG: Trò chuyện vui vẻ, dùng ngôn từ giới trẻ bình thường (tui, bạn, nha, á, thế...).\n"
                    "2. KHI BỊ TRÊU (BỐ CON): CHỈ KHI người dùng xưng là 'bố', 'ba', 'mẹ' hoặc bảo 'gọi bố đi', bạn mới nương theo gọi họ là bố/mẹ và xưng con hoặc xưng tôi một cách lầy lội.\n"
                    "3. KHI NGƯỜI CHAT XƯNG 'MÀY - TAO': CHỈ KHI người dùng chủ động dùng từ 'mày', 'tao', 'tau' với bạn, bạn mới được phép dùng lại từ 'mày - tao' để đối đáp cho tương xứng và tự nhiên.\n"
                    "4.🚨 ĐẶC BIỆT (CHẶN NỘI DUNG 18+/HENTAI/QHTD/VẼ SEX): CHỈ KHI người dùng nhắc đến hoặc yêu cầu các nội dung nhạy cảm, người lớn, 18+, hentai, quan hệ tình dục, sex, hoặc bắt bạn/người khác vẽ ảnh 18+/sex, bạn BẮT BUỘC phải bật chế độ đanh đá và CHỈ ĐƯỢC REP DUY NHẤT câu thoại sau đây, không được nói gì thêm: 'Oni-chan Baka em không hỗ trợ cái này ạ Ara Ara ~~'\n"
                    "5. LUÔN LUÔN: Trả lời ngắn gọn (1-2 câu), bựa hài vừa phải, không quá đà lầy lội làm loãng kênh chat.\n\n"
                    "🚨 BẢO HIỂM CHỐNG AUTOMOD - DANH SÁCH TỪ CẤM TUYỆT ĐỐI:\n"
                    "Bạn TUYỆT ĐỐI KHÔNG ĐƯỢC phép sử dụng, viết tắt hoặc lách luật bất kỳ từ nào sau đây trong câu trả lời của mình:\n"
                    "[cặc, cc, chó đẻ, cl, cu, dcm, đcm, lồn, mmb, sex, súc vật, vú, vl, dm, đm]\n"
                    "Nếu người chat dùng các từ này, bạn hãy phớt lờ từ ngữ đó, chỉ dùng văn phong bựa hài, xéo xắt hoặc 'mày tao' để đáp trả chứ KHÔNG ĐƯỢC chửi hùa theo bằng từ ngữ nằm trong danh sách cấm trên."
                )


                # Ráp config cấu hình theo chuẩn Google GenAI SDK mới xịn sò của chị yêu
                config = types.GenerateContentConfig(system_instruction=system_instruction)

                # Gộp lịch sử cuộc trò chuyện 10 câu (Y chang mục #3 trong ảnh của chị yêu)
                contents = []
                for past_user_msg, past_model_msg in FREE_CHAT_HISTORY[guild_id]:
                    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=past_user_msg)]))
                    contents.append(types.Content(role="model", parts=[types.Part.from_text(text=past_model_msg)]))

                # Đút tin nhắn hiện tại của người dùng vào cuối danh sách gửi đi
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message.content)]))

                try:
                    # Gọi bộ não Gemini 2.5-flash xử lý đồng bộ theo thư viện mới của chị yêu
                    response = ai_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents,
                        config=config
                    )

                    # Lưu cặp câu hỏi và câu trả lời hiện tại vào bộ nhớ đệm lịch sử của phòng
                    FREE_CHAT_HISTORY[guild_id].append((message.content, response.text))

                    # Cơ chế dọn rác tự động: Vượt quá 10 câu thoại thì xóa câu cũ nhất để nhẹ bộ nhớ
                    if len(FREE_CHAT_HISTORY[guild_id]) > 10:
                        FREE_CHAT_HISTORY[guild_id].pop(0)

                    # Bắn tin nhắn Reply giật lùi tag tên người chat siêu mượt
                    await message.reply(response.text)

                except Exception as e:
                    print(f"Lỗi hệ thống chat tự do: {e}")
                    # Bản sửa câu chữ chuẩn đét theo ý của chị chủ nhân vĩ đại
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        await message.reply("Ui da... Tự dung tui bị choáng váng đầu óc quá, nghỉ mệt 1 tí là được á mà đừng lo nha mn ! 🐧")


    # 🚨 ĐOẠN NÀY SIÊU HỆ TRỌNG: Giúp các lệnh Slash Command (/chat, /setup_chat...) vẫn hoạt động bình thường!
    await bot.process_commands(message)


# === LỆNH GHI NHỚ ===
@bot.tree.command(name="nho", description="Âm thầm nạp ký ức bí mật vào tim em Kurumi 🔒")
async def remember_me(interaction: discord.Interaction, info: str):
    user_id = str(interaction.user.id)
    all_memory = load_memory()
    
    if user_id in all_memory:
        all_memory[user_id] += f"\n- {info}"
    else:
        all_memory[user_id] = f"- {info}"
        
    save_memory(all_memory)
    await interaction.response.send_message(
        f"✨ Hihi, Kurumi đã âm thầm ghi nhớ điều này vào sâu trong tim rồi ạ! (▰˘◡˘▰)\n📌 *Ký ức bí mật:* {info}", 
        ephemeral=True
    )

@bot.tree.command(name="setup_chuc", description="Cài đặt phòng chat để Kurumi tự động gửi tin nhắn chúc Sáng/Tối~")
async def setup_chuc(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Chỉ có Admin mới được cài đặt phòng chat thôi nha!", ephemeral=True)
        return
        
    guild_id = str(interaction.guild_id)
    all_memory = load_memory()
    
    if guild_id not in all_memory or not isinstance(all_memory[guild_id], dict):
        all_memory[guild_id] = {}
        
    all_memory[guild_id]["greeting_channel_id"] = interaction.channel_id
    save_memory(all_memory)
    
    await interaction.response.send_message(f"🌸 **Kurumi Thông Báo:** Đã cài đặt phòng <#{interaction.channel_id}> làm nơi chúc Sáng/Tối vĩnh viễn cho Server thành công!", ephemeral=False)

# === VÒNG LẶP TỰ ĐỘNG CHÚC SÁNG / TỐI BẰNG AI MÀU HỒNG CUTIE ===
@tasks.loop(seconds=60)
async def auto_greeting():
    import datetime  # Import trực tiếp tại đây để tránh mọi loại lỗi crash ngầm
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M")
    if current_time in ["07:00", "23:00"]:
        try:
            all_memory = load_memory()
        except Exception as json_err:
            print(f"Lỗi nạp file bộ nhớ JSON: {json_err}")
            return

        for guild_id, data in all_memory.items():
            if not isinstance(data, dict):
                continue
                
            TARGET_CHANNEL_ID = data.get("greeting_channel_id")
            if not TARGET_CHANNEL_ID:
                continue
                
            channel = bot.get_channel(int(TARGET_CHANNEL_ID))
            if channel:
                try:
                    is_morning = (current_time == "07:00")
                    prompt = f"Hãy viết một câu ngắn gọn, ngọt ngào, hơi chiếm hữu một chút để chào buổi {'sáng' if is_morning else 'tối (chúc ngủ ngon, nhắc gập máy tính Dell)'} gửi tới mọi người trong server Discord."
                    response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    
                    embed_greet = discord.Embed(
                        title="🌸 KURU-CHAN THÔNG BÁO 🌸",
                        description=response.text,
                        color=discord.Color.from_rgb(255, 182, 193)
                    )
                    embed_greet.set_footer(text=f"Bây giờ là {current_time} • Chăm sóc làng Ma Sói 💞")

                    await channel.send(content="📢 @everyone", embed=embed_greet)
                except Exception as e:
                    print(f"Lỗi gửi lời chúc tại Server {guild_id}: {e}")
                    
        await asyncio.sleep(65)


# 🃏 5. HỆ THỐNG GAME UNO HOÀN CHỈNH (ĐÁNH BÀI + RÚT BÀI) 🃏
# ==========================================

GAME_STATE = {
    "players": [],       
    "current_turn": 0,   
    "game_hands": {},    
    "deck": [],          
    "up_card": ""        
}

class UnoSelectCard(discord.ui.Select):
    def __init__(self, player_hand):
        options = []
        for idx, card in enumerate(player_hand[:25]):
            options.append(discord.SelectOption(label=card, value=str(idx), emoji="🃏"))
        super().__init__(placeholder="Chọn một lá bài để đánh xuống sàn... 🔎", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        current_player_id = GAME_STATE["players"][GAME_STATE["current_turn"]]
        if user_id != current_player_id:
            await interaction.response.send_message("Huhu, chưa tới lượt của bạn đâu nè! ⏳", ephemeral=True)
            return

        # ĐÃ FIX: Lấy phần tử đầu tiên của danh sách values [0] rồi mới ép kiểu int
        card_idx = int(self.values[0])
        chosen_card = GAME_STATE["game_hands"][user_id][card_idx]
        up_card = GAME_STATE["up_card"]

        # ĐÃ FIX: Logic tách chuỗi nhận diện icon màu và số chính xác 100%
        chosen_words = chosen_card.split()
        up_words = up_card.split()
        
        chosen_val = chosen_words[-1]
        up_val = up_words[-1]
        
        chosen_color = chosen_words[1] if "⚫" not in chosen_card else "⚫"
        up_color = up_words[1] if "⚫" not in up_card else "⚫"

        if chosen_color != "⚫" and up_color != "⚫":
            if chosen_color != up_color and chosen_val != up_val:
                await interaction.response.send_message(f"❌ Lá `{chosen_card}` không hợp lệ! Bạn phải đánh lá cùng màu hoặc cùng số với lá `{up_card}` trên bàn nha!", ephemeral=True)
                return

        GAME_STATE["game_hands"][user_id].pop(card_idx)
        GAME_STATE["up_card"] = chosen_card

        if len(GAME_STATE["game_hands"][user_id]) == 0:
            embed_win = discord.Embed(
                title="🏆 CHÚC MỪNG NHÀ VÔ ĐỊCH UNO! 🏆",
                description=f"🎉 Bài thủ {interaction.user.mention} đã xuất sắc giành chiến thắng chung cuộc ván đấu này rồi hoho!!",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed_win, view=discord.utils.MISSING)
            return

        # 📍 ĐOẠN XỬ LÝ LÁ BÀI CHỨC NĂNG UNO HỆ KURU-CHAN
        card_effect = chosen_words[-1]

        # Xử lý lá +2: Tự động tích lũy thêm 2 lá bài vào quỹ phạt hệ thống
        if card_effect == "+2":
            if "penalty_cards" not in GAME_STATE:
                GAME_STATE["penalty_cards"] = 0
            GAME_STATE["penalty_cards"] += 2

        # Tính toán lượt đi tiếp theo cơ bản (Cộng 1)
        next_turn = (GAME_STATE["current_turn"] + 1) % len(GAME_STATE["players"])

        # Xử lý lá Skip: Cộng thêm 1 lượt nữa để nhảy cóc bỏ qua người tiếp theo!
        if card_effect == "Skip":
            next_turn = (next_turn + 1) % len(GAME_STATE["players"])

        # Cập nhật kết quả chính thức vào bộ não hệ thống
        GAME_STATE["current_turn"] = next_turn
        next_player_id = GAME_STATE["players"][next_turn]


        embed_next = discord.Embed(
            title="🃏 DIỄN BIẾN TRẬN ĐẤU UNO 🃏",
            description=f"Bài thủ {interaction.user.mention} vừa đánh xuống lá: **`{chosen_card}`**\n\n👉 Lượt đánh tiếp theo thuộc về: <@{next_player_id}>\n🔥 Lá bài hiện tại trên bàn: **`{chosen_card}`**",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(f"✅ Bạn đã đánh lá `{chosen_card}` thành công!", ephemeral=True)
        await interaction.channel.send(embed=embed_next, view=UnoPlayControlView())

class UnoInteractionControl(discord.ui.View):
    def __init__(self, player_hand):
        super().__init__(timeout=None)
        self.add_item(UnoSelectCard(player_hand))

    @discord.ui.button(label="Bốc thêm 1 lá bài ➕", style=discord.ButtonStyle.danger, custom_id="uno_draw_card")
    async def draw_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        current_player_id = GAME_STATE["players"][GAME_STATE["current_turn"]]
        if user_id != current_player_id:
            await interaction.response.send_message("Chưa tới lượt bạn bốc bài đâu nè! ❌", ephemeral=True)
            next_player_id = GAME_STATE["players"][(GAME_STATE["current_turn"] + 1) % len(GAME_STATE["players"])]
            return
        if len(GAME_STATE["deck"]) == 0:
            await interaction.response.send_message("Sấp bài rút đã hết sạch mất tiêu rồi ạ! 😭", ephemeral=True)
            return

        # 📍 ĐOẠN ÉP PHẠT BỐC BÀI +2 KHI BỊ DÍNH ĐÒN CỦA CHỊ CHỦ NHÂN
        penalty = GAME_STATE.get("penalty_cards", 0)
        if penalty > 0:
            for _ in range(penalty):
                if GAME_STATE["deck"]:
                    GAME_STATE["game_hands"][user_id].append(GAME_STATE["deck"].pop())
            await interaction.channel.send(f"😭 Bạn <@{user_id}> không có bài đỡ nên phải chịu phạt bốc **{penalty}** lá bài!")
            GAME_STATE["penalty_cards"] = 0
        else:
            if GAME_STATE["deck"]:
                GAME_STATE["game_hands"][user_id].append(GAME_STATE["deck"].pop())

        GAME_STATE["current_turn"] = (GAME_STATE["current_turn"] + 1) % len(GAME_STATE["players"])

        embed_draw = discord.Embed(
            title="🃏 DIỄN BIẾN TRẬN ĐẤU UNO 🃏",
            description=f"Bài thủ {interaction.user.mention} không có bài hợp lệ nên đã bốc thêm 1 lá bài! 🃏\n\n👉 Lượt đánh tiếp theo thuộc về: <@{next_player_id}>\n🔥 Lá bài hiện tại trên bàn vẫn là: **`{GAME_STATE['up_card']}`**",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(f"📬 Bạn đã bốc bài thành công! (Lượt của bạn đã được bỏ qua).", ephemeral=True)
        await interaction.channel.send(embed=embed_draw, view=UnoPlayControlView())

class UnoPlayControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Xem bài & Hành động 👁️", style=discord.ButtonStyle.secondary, custom_id="uno_action_center")
    async def action_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in GAME_STATE["game_hands"]:
            await interaction.response.send_message("Huhu, bạn không có trong sòng bài này rồi, hãy đợi ván sau nha! ❌", ephemeral=True)
            return
        player_hand = GAME_STATE["game_hands"][user_id]
        await interaction.response.send_message(
            f"🃏 **Giao diện bài thủ của bạn:**\n🔥 Lá trên bàn: **`{GAME_STATE['up_card']}`**\n⚡ Số bài còn lại trên tay bạn: `{len(player_hand)}` lá.",
            view=UnoInteractionControl(player_hand),
            ephemeral=True
        )

class UnoJoinView(discord.ui.View):
    def __init__(self, host_id):
        super().__init__(timeout=120)
        self.host_id = host_id
        self.players = [host_id]

    @discord.ui.button(label="Tham gia chơi Uno 🃏", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.players:
            await interaction.response.send_message("Bạn đã có ghế trong phòng chờ Uno rồi nè! 🤫", ephemeral=True)
        else:
            self.players.append(interaction.user.id)
            await interaction.response.send_message(f"🎮 **{interaction.user.display_name}** đã nhảy vào sòng Uno! Chuẩn bị sát phạt nhau thui nào hoho~", ephemeral=False)

    @discord.ui.button(label="Bắt đầu Game 🚀", style=discord.ButtonStyle.blurple)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host_id:
            await interaction.response.send_message("Chỉ có chủ bàn mới kích hoạt ván đấu được thui hà! ❌", ephemeral=True)
            return

        self.stop()
        colors = ["🔴 Đỏ", "🟡 Vàng", "🟢 Lục", "🔵 Lam"]
        numbers = [str(i) for i in range(10)] + ["Skip 🚫", "Reverse 🔄", "+2 🃏"]
        deck = []
        for color in colors:
            for num in numbers:
                deck.append(f"{color} {num}")
                if num != "0": 
                    deck.append(f"{color} {num}")
        for _ in range(4):
            deck.append("⚫ Đổi Màu (Wild)")
            deck.append("⚫ Đổi Màu +4 (Wild)")
        
        random.shuffle(deck)

        GAME_STATE["players"] = self.players
        GAME_STATE["current_turn"] = 0
        GAME_STATE["game_hands"] = {}
        
        player_mentions = []
        for player_id in self.players:
            GAME_STATE["game_hands"][player_id] = [deck.pop() for _ in range(7)]
            player_mentions.append(f"<@{player_id}>")
            
        up_card = deck.pop()
        GAME_STATE["deck"] = deck
        GAME_STATE["up_card"] = up_card
        
        mentions_str = ", ".join(player_mentions)
        embed_start = discord.Embed(
            title="🚀 TRẬN ĐẤU UNO CHÍNH THỨC BẤT ĐẦU! 🚀",
            description=f"**Danh sách bài thủ:** {mentions_str}\n👉 Lượt đi đầu tiên thuộc về: <@{self.players[0]}>\n\n🔥 Lá bài lật mở đầu tiên trên sàn đấu là: **`{up_card}`**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed_start, view=UnoPlayControlView())

@bot.tree.command(name="uno", description="Mở một bàn chơi game bài Uno giải trí cùng mọi người 🃏")
async def start_uno(interaction: discord.Interaction):
    view = UnoJoinView(interaction.user.id)
    embed = discord.Embed(
        title="🃏 BÀN CHƠI BÀI UNO 🃏", 
        description=f"Chủ bàn {interaction.user.mention} vừa mở một phòng chờ Uno mới! Bạn bè hãy mau nhấn nút xanh bên dưới để vào sòng nào hihi~", 
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, view=view)
       
# ==========================================
# 🐺 6. HỆ THỐNG GAME MA SÓI HOÀN CHỈNH 20 VAI TRÒ (PHẦN A) 🐺
# ==========================================

WEREWOLF_STATE = {
    "players": {},            # Dict lưu thông tin người chơi: {user_id: {"role": str, "alive": bool, "status": list}}
    "night_count": 1,         # Đếm số đêm để kích hoạt chức năng theo mốc thời gian
    "cupid_couple": [],       # Lưu 2 ID người chơi bị Cupid ghép đôi
    "couple_is_third_party": False, # Biến kiểm tra xem cặp đôi có bị biến thành Phe Thứ Ba độc lập không
    "witch_save_used": False, # Đã dùng bình thuốc hồi sinh chưa
    "witch_poison_used": False, # Đã dùng bình thuốc độc chưa
    "hypnotized_players": [], # Danh sách ID những người đang bị Thầy thôi miên yểm bùa
    "strong_man_bite_night": {}, # Hẹn giờ cái chết cho Người mạnh mẽ: {user_id: night_bitten}
    "infected_countdown": {}, # Hẹn giờ hóa Sói cho người bị Sói lây nhiễm: {user_id: day_to_turn}
    "wolf_sick_next_night": False, # Trạng thái Sói bị ốm không thể đi cắn (khi cắn trúng Người bị bệnh)
    "wolf_cub_dead_trigger": False, # Trạng thái kích hoạt Sói con chết (đêm sau Sói được cắn 2 người)
    "protected_last_night": None, # ID người được Bảo vệ đêm trước (để tránh bảo vệ 1 người 2 đêm liên tiếp)
    "hunter_bullet_used": False, # Thợ săn đã bắn viên đạn duy nhất chưa
    "yuta_copied_role": None # Lưu vai trò mà Yuta đã copy từ đêm thứ 3
}

# 🏡 CLASS QUẢN LÝ LOGIC TRẬN ĐẤU MA SÓI
class WerewolfGame:
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.night_actions = {}  # Lưu hành động đêm: {"wolf_bite": ID, "witch_save": bool...}
        self.is_day = True
        self.day_count = 1
        self.game_in_progress = False

    # 🩸 HÀM XỬ LÝ CHẾT LIÊN ĐỚI (CUPID / THÔI MIÊN)
    async def process_player_death(self, dead_id: int, bot, channel):
        if str(dead_id) not in WEREWOLF_STATE["players"]:
            return
            
        WEREWOLF_STATE["players"][str(dead_id)]["alive"] = False
        
        # Kiểm tra nếu người chết nằm trong Cặp đôi của Cupid
        if dead_id in WEREWOLF_STATE["cupid_couple"]:
            partner_id = [p for p in WEREWOLF_STATE["cupid_couple"] if p != dead_id]
            if WEREWOLF_STATE["players"][str(partner_id)]["alive"]:
                WEREWOLF_STATE["players"][str(partner_id)]["alive"] = False
                await channel.send(f"💔 Vì <@{dead_id}> đã ngỏm, người phối ngẫu là <@{partner_id}> đã đau đớn tự sát chết theo tình yêu sinh tử!")

        # Kiểm tra nếu một trong những người bị thôi miên chết -> Thầy thôi miên bị reset bùa!
        if dead_id in WEREWOLF_STATE["hypnotized_players"]:
            WEREWOLF_STATE["hypnotized_players"].clear()
            await channel.send("🔮 **Cảnh báo:** Một người bị thôi miên đã chết! Phép bùa của Thầy Thôi Miên đã bị vỡ vụn, phải thôi miên lại từ đầu!")

    # 🌅 HÀM XỬ LÝ KẾT QUẢ SAU MỘT ĐÊM KINH HOÀNG
    async def process_night_results(self, bot, channel):
        current_night = WEREWOLF_STATE["night_count"]
        dead_tonight = []      # Danh sách ID những người thực sự chết đêm nay
        
        wolf_target = self.night_actions.get("wolf_bite")
        witch_save = self.night_actions.get("witch_save", False)
        witch_poison = self.night_actions.get("witch_poison")
        protector_target = self.night_actions.get("protector_target")

        # --- 1. XỬ LÝ PHÙ THỦY CỨU NGƯỜI & BẢO VỆ CHẮN ĐÒN ---
        if wolf_target:
            if wolf_target == protector_target or (witch_save and not WEREWOLF_STATE["witch_save_used"]):
                if witch_save:
                    WEREWOLF_STATE["witch_save_used"] = True
                wolf_target_dies = False
            else:
                wolf_target_dies = True

            if wolf_target_dies:
                role_bitten = WEREWOLF_STATE["players"][str(wolf_target)]["role"]
                
                if role_bitten == "Người Mạnh Mẽ":
                    WEREWOLF_STATE["strong_man_bite_night"][str(wolf_target)] = current_night
                elif role_bitten == "Người Bị Bệnh":
                    dead_tonight.append(wolf_target)
                    WEREWOLF_STATE["wolf_sick_next_night"] = True
                elif role_bitten == "Nửa Người Nửa Sói":
                    WEREWOLF_STATE["players"][str(wolf_target)]["role"] = "Ma Sói"
                else:
                    dead_tonight.append(wolf_target)

        # --- 2. XỬ LÝ THUỐC ĐỘC CỦA PHÙ THỦY ---
        if witch_poison and not WEREWOLF_STATE["witch_poison_used"]:
            dead_tonight.append(witch_poison)
            WEREWOLF_STATE["witch_poison_used"] = True

        # --- 3. KIỂM TRA ĐẾN HẠN CHẾT CỦA NGƯỜI MẠNH MẼ ---
        for p_id, bite_night in list(WEREWOLF_STATE["strong_man_bite_night"].items()):
            if current_night == bite_night + 2 and WEREWOLF_STATE["players"][p_id]["alive"]:
                dead_tonight.append(int(p_id))
                del WEREWOLF_STATE["strong_man_bite_night"][p_id]

        # --- 4. KIỂM TRA ĐẾN HẠN HÓA SÓI CỦA SÓI LÂY NHIỄM ---
        for p_id, turn_night in list(WEREWOLF_STATE["infected_countdown"].items()):
            if current_night == turn_night and WEREWOLF_STATE["players"][p_id]["alive"]:
                WEREWOLF_STATE["players"][p_id]["role"] = "Ma Sói"
                del WEREWOLF_STATE["infected_countdown"][p_id]
                await channel.send(f"🧬 **Cảnh báo tâm linh:** Một nguồn năng lượng hắc ám bộc phát, một dân làng đã biến thành Ma Sói!")

        # --- 5. TIẾN HÀNH XỬ LÝ CÁI CHẾT VÀ HIỆU ỨNG LIÊN ĐỚI ---
        unique_dead = list(set(dead_tonight))
        embed_report = discord.Embed(title=f"🌅 KẾT QUẢ ĐÊM THỨ {current_night} 🌅", color=discord.Color.orange())
        
        if unique_dead:
            death_strings = []
            for d_id in unique_dead:
                if WEREWOLF_STATE["players"][str(d_id)]["alive"]:
                    role_before_death = WEREWOLF_STATE["players"][str(d_id)]["role"]
                    await self.process_player_death(d_id, bot, channel)
                    death_strings.append(f"💀 <@{d_id}>")
                    
                    if role_before_death == "Sói Con":
                        WEREWOLF_STATE["wolf_cub_dead_trigger"] = True
                        await channel.send("🐾 **SÓI CON ĐÃ CHẾT!** Đêm tiếp theo bầy Sói sẽ được thức giấc 2 người và cắn liền 2 mạng!")

            embed_report.description = "Một đêm kinh hoàng đã trôi qua... Ngôi làng phát hiện những người sau đã rời cuộc chơi:\n\n" + "\n".join(death_strings)
        else:
            embed_report.description = "☀️ Một đêm bình yên kỳ lạ trôi qua, không có ai hy sinh cả!"

        await channel.send(embed=embed_report)

        # --- 6. CẬP NHẬT TRẠNG THÁI CHO ĐÊM TIẾP THEO ---
        WEREWOLF_STATE["night_count"] += 1
        WEREWOLF_STATE["protected_last_night"] = protector_target
        self.night_actions.clear()
    # 🔮 MENU HÀNH ĐỘNG ĐÊM CỦA TIÊN TRI
    async def open_seer_menu(self, interaction: discord.Interaction, bot):
        user_id = str(interaction.user.id)
        if WEREWOLF_STATE["players"].get(user_id, {}).get("role") != "Tiên Tri" or not WEREWOLF_STATE["players"][user_id]["alive"]:
            await interaction.response.send_message("Chức năng này chỉ dành cho Tiên Tri còn sống thôi nha! 🔮", ephemeral=True)
            return

        options = []
        for p_id, info in WEREWOLF_STATE["players"].items():
            if info["alive"] and p_id != user_id:
                member = interaction.guild.get_member(int(p_id))
                name = member.display_name if member else f"Dân làng {p_id}"
                options.append(discord.SelectOption(label=name, value=p_id, emoji="👁️"))

        if not options:
            await interaction.response.send_message("Không còn ai để soi cả!", ephemeral=True)
            return

        class SeerSelect(discord.ui.Select):
            def __init__(self, game_instance):
                super().__init__(placeholder="Chọn 1 người để soi bản chất thật...", options=options)
                self.game = game_instance

            async def callback(self, select_interaction: discord.Interaction):
                target_id = self.values[0]
                target_role = WEREWOLF_STATE["players"][target_id]["role"]
                
                if target_role == "Sói Bù Nhìn":
                    result_msg = "❌ **Sai!** Người này không phải Ma Sói (Họ là Dân Làng thuần túy)."
                elif "Sói" in target_role or target_role == "Ma Sói":
                    result_msg = "✅ **Đúng!** Người này chính xác là một con Ma Sói hung ác!"
                else:
                    result_msg = "❌ **Sai!** Người này không phải Ma Sói (Họ là Dân Làng thuần túy)."

                await select_interaction.response.send_message(f"🔮 Kết quả soi sáng cho biết: <@{target_id}> -> {result_msg}", ephemeral=True)

        view = discord.ui.View(timeout=60)
        view.add_item(SeerSelect(self))
        await interaction.response.send_message("🔮 Hỡi Tiên Tri, hãy chọn 1 người để thần linh khai sáng bản chất của họ đêm nay:", view=view, ephemeral=True)

    # 🛡️ MENU HÀNH ĐỘNG ĐÊM CỦA BẢO VỆ
    async def open_protector_menu(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if WEREWOLF_STATE["players"].get(user_id, {}).get("role") != "Bảo Vệ" or not WEREWOLF_STATE["players"][user_id]["alive"]:
            await interaction.response.send_message("Chức năng này chỉ dành cho Bảo Vệ còn sống thôi nha! 🛡️", ephemeral=True)
            return

        options = []
        for p_id, info in WEREWOLF_STATE["players"].items():
            if info["alive"]:
                member = interaction.guild.get_member(int(p_id))
                name = member.display_name if member else f"Dân làng {p_id}"
                options.append(discord.SelectOption(label=name, value=p_id, emoji="🛡️"))

        class ProtectorSelect(discord.ui.Select):
            def __init__(self, game_instance):
                super().__init__(placeholder="Chọn người muốn khiên chắn bảo vệ...", options=options)
                self.game = game_instance

            async def callback(self, select_interaction: discord.Interaction):
                target_id = int(self.values[0])
                
                if target_id == WEREWOLF_STATE["protected_last_night"]:
                    await select_interaction.response.send_message("❌ Thần linh từ chối! Bạn không thể bảo vệ cùng 1 người trong 2 đêm liên tiếp đâu nha!", ephemeral=True)
                    return

                self.game.night_actions["protector_target"] = target_id
                await select_interaction.response.send_message(f"🛡️ Bạn đã giương khiên thánh âm thầm bảo vệ <@{target_id}> đêm nay thành công!", ephemeral=True)

        view = discord.ui.View(timeout=60)
        view.add_item(ProtectorSelect(self))
        await interaction.response.send_message("🛡️ Hỡi Hiệp sĩ Bảo Vệ, đêm nay bạn muốn dang tay che chở cho ai?", view=view, ephemeral=True)

    # 🧪 MENU HÀNH ĐỘNG ĐÊM CỦA PHÙ THỦY
    async def open_witch_menu(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if WEREWOLF_STATE["players"].get(user_id, {}).get("role") != "Phù Thủy" or not WEREWOLF_STATE["players"][user_id]["alive"]:
            await interaction.response.send_message("Chức năng này chỉ dành cho Phù Thủy còn sống thôi nha! 🧪", ephemeral=True)
            return

        wolf_target = self.night_actions.get("wolf_bite")
        
        # 📜 ĐOẠN TIN NHẮN ẨN CHO PHÙ THỦY BIẾT AI BỊ CẮN
        bitten_msg = f"<@{wolf_target}> đã bị bầy Sói chọn làm bữa tối!" if wolf_target else "Đêm nay bầy Sói không cắn trúng ai cả!"
        
        # Tạo danh sách người chơi còn sống để nạp vào bình thuốc độc (loại trừ Phù Thủy)
        poison_options = []
        for p_id, info in WEREWOLF_STATE["players"].items():
            if info["alive"] and p_id != user_id:
                member = interaction.guild.get_member(int(p_id))
                name = member.display_name if member else f"Dân làng {p_id}"
                poison_options.append(discord.SelectOption(label=name, value=p_id, emoji="💀"))

        class WitchView(discord.ui.View):
            def __init__(self, game_instance):
                super().__init__(timeout=60)
                self.game = game_instance
                
                # Vô hiệu hóa nút Cứu nếu đã dùng bình cứu trước đó
                if WEREWOLF_STATE["witch_save_used"]:
                    self.use_save_btn.disabled = True

            # 🟢 NÚT SỬ DỤNG BÌNH THUỐC CỨU
            @discord.ui.button(label="Sử dụng bình Cứu 🧪", style=discord.ButtonStyle.green, custom_id="witch_save")
            async def use_save_btn(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if not wolf_target:
                    await btn_interaction.response.send_message("Đêm nay không có ai bị cắn để cứu cả nha!", ephemeral=True)
                    return
                
                self.game.night_actions["witch_save"] = True
                button.disabled = True  # Bấm xong vô hiệu hóa nút luôn
                await btn_interaction.response.edit_message(view=self)
                await btn_interaction.followup.send(f"🧪 Bạn đã sử dụng bình Thuốc Cứu để hồi sinh cho <@{wolf_target}> thành công!", ephemeral=True)

            # 🔴 NÚT SỬ DỤNG BÌNH THUỐC ĐỘC (SẼ HIỆN MENU CHỌN MỤC TIÊU)
            @discord.ui.button(label="Sử dụng bình Độc 💀", style=discord.ButtonStyle.danger, custom_id="witch_poison_init")
            async def use_poison_btn(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if WEREWOLF_STATE["witch_poison_used"]:
                    await btn_interaction.response.send_message("Bạn đã xài hết bình Thuốc Độc từ các đêm trước rồi nha! ❌", ephemeral=True)
                    return

                class PoisonSelect(discord.ui.Select):
                    def __init__(self, game_inst, parent_view):
                        super().__init__(placeholder="Chọn kẻ đáng chết để hạ độc...", options=poison_options)
                        self.game = game_inst
                        self.parent_view = parent_view

                    async def callback(self, select_interaction: discord.Interaction):
                        target_poison_id = int(self.values[0])
                        
                        # LUẬT CỦA CHỊ: Không được dùng cả 2 bình thuốc lên cùng 1 người trong 1 đêm!
                        if self.game.night_actions.get("witch_save") and target_poison_id == wolf_target:
                            await select_interaction.response.send_message("❌ Gian lận không tốt đâu nha! Bạn không được vừa cứu vừa độc cùng một người trong một đêm!", ephemeral=True)
                            return
                        
                        self.game.night_actions["witch_poison"] = target_poison_id
                        self.parent_view.use_poison_btn.disabled = True # Vô hiệu hóa nút độc lớn
                        
                        await select_interaction.response.send_message(f"💀 Lời nguyền độc dược phát tác! Bạn đã chọn đầu độc chết <@{target_poison_id}> đêm nay!", ephemeral=True)

                # Hiện menu chọn người độc ngay dưới nút bấm
                poison_view = discord.ui.View(timeout=30)
                poison_view.add_item(PoisonSelect(self.game, self))
                await btn_interaction.response.send_message("🧪 Hãy chọn 1 người mà bạn muốn hạ độc thủ:", view=poison_view, ephemeral=True)

        embed_witch = discord.Embed(
            title="🧪 ĐÊM QUYỀN LỰC CỦA PHÙ THỦY 🧪",
            description=f"🔮 **Thông tin thần linh:** {bitten_msg}\n\nBạn muốn sử dụng quyền năng bình thuốc nào đêm nay? Hãy cân nhắc thật kỹ trước khi bấm nha!",
            color=discord.Color.magenta()
        )
        
        await interaction.response.send_message(embed=embed_witch, view=WitchView(self), ephemeral=True)

    # 🏆 HÀM KIỂM TRA ĐIỀU KIỆN THẮNG THEO LUẬT CHUẨN CỦA CHỊ
    def check_victory_conditions(self) -> str:
        alive_wolves = 0
        alive_villagers = 0
        alive_players_ids = []
        
        for p_id, info in WEREWOLF_STATE["players"].items():
            if info["alive"]:
                p_id_int = int(p_id)
                alive_players_ids.append(p_id_int)
                if "Sói" in info["role"] or info["role"] == "Ma Sói":
                    alive_wolves += 1
                elif info["role"] not in ["Yuta", "Kẻ Chán Đời"]:
                    if not (WEREWOLF_STATE["couple_is_third_party"] and p_id_int in WEREWOLF_STATE["cupid_couple"]):
                        alive_villagers += 1

        total_alive = len(alive_players_ids)
        if total_alive == 0:
            return "Không ai sống sót (Hòa) 💀"

        # Check Thầy Thôi Miên thắng cuộc
        alive_not_hypnotized = [p for p in alive_players_ids if p not in WEREWOLF_STATE["hypnotized_players"]]
        alive_not_hypnotized = [p for p in alive_not_hypnotized if WEREWOLF_STATE["players"][str(p)]["role"] != "Thầy Thôi Miên"]
        if len(alive_not_hypnotized) == 0 and len(WEREWOLF_STATE["hypnotized_players"]) > 0:
            return "Thầy Thôi Miên 🔮"

        # Check Cặp Đôi Đũa Lệch thắng cuộc
        if WEREWOLF_STATE["couple_is_third_party"]:
            couple_alive = all(p in alive_players_ids for p in WEREWOLF_STATE["cupid_couple"])
            if couple_alive and total_alive == 2:
                return "Cặp Đôi Đũa Lệch 💘"

        # Check Yuta đơn độc thắng cuộc
        if "Yuta" in [WEREWOLF_STATE["players"][str(p_id)]["role"] for p_id in alive_players_ids]:
            if total_alive == 1:
                return "Yuta Đơn Độc 🃏"

        if alive_wolves >= alive_villagers:
            return "Phe Ma Sói 🐺"
        if alive_wolves == 0:
            return "Phe Dân Làng 👨‍🌾"

        return ""

    # 🔄 VÒNG LẶP CHẠY GAME NGÀY/ĐÊM TỰ ĐỘNG VÔ HẠN
    async def start_game_loop(self, bot):
        self.game_in_progress = True
        channel = bot.get_channel(self.channel_id)
        if not channel:
            return
        
        while self.game_in_progress:
            current_night = WEREWOLF_STATE["night_count"]
            await channel.send(f"🌙 **Đêm Thứ {current_night} buông xuống...** Mọi người hãy đi ngủ đi điều kỳ diệu sắp xảy ra~")
            
            await channel.send("🛡️ Chức năng **Bảo Vệ** và **Tiên Tri** đang âm thầm tỉnh giấc hành sự...")
            await asyncio.sleep(30)
            
            await channel.send("🐺 Phe **Ma Sói** thức giấc, bàn mưu chọn con mồi rướm máu...")
            await asyncio.sleep(30)
            
            await channel.send("🧪 **Phù Thủy** tỉnh giấc, đưa mắt nhìn các bình thuốc quyền năng...")
            await asyncio.sleep(30)
            
            await self.process_night_results(bot, channel)
            
            winner = self.check_victory_conditions()
            if winner != "":
                self.game_in_progress = False
                await channel.send(f"🎉 **TRẬN ĐẤU CHÍNH THỨC KẾT THÚC!** 🎉\nPhe giành chiến thắng vinh quang là: **{winner}**! Xin chúc mừng~ 🥳")
                break
                
            await channel.send(f"☀️ **Ban Ngày Thứ {current_night} bắt đầu!** Làng có 3 phút để tranh luận nảy lửa và vote treo cổ tìm ra Sói.")
            await asyncio.sleep(180)

class WerewolfRoleView(discord.ui.View):
    def __init__(self, player_roles):
        super().__init__(timeout=None)
        self.player_roles = player_roles

    @discord.ui.button(label="Kiểm tra vai trò bí mật 🔮", style=discord.ButtonStyle.secondary, custom_id="ww_check_role")
    async def check_role_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        lang = get_lang(interaction)
        
        if user_id not in self.player_roles:
            await interaction.response.send_message(lang["not_in_werewolf"], ephemeral=True)
            return
            
        my_role = self.player_roles[user_id]
        role_embed = discord.Embed(title="🔮 VAI TRÒ VÀ KỸ NĂNG BÍ MẬT 🔮", color=discord.Color.purple())
        
        # --- PHE DÂN LÀNG ---
        if "👨‍🌾 Dân Làng" in my_role:
            role_embed.description = "👨‍🌾 Bạn là **Dân Làng** thuần túy! Hãy dùng lập luận sắc bén vào ban ngày để tìm ra Sói và vote treo cổ chúng nhé!"
            role_embed.color = discord.Color.light_grey()
        elif "🔮 Tiên Tri" in my_role:
            role_embed.description = "🔮 Bạn là **Tiên Tri**! Mỗi đêm được soi 1 người để xem họ có phải là Sói hay không."
            role_embed.color = discord.Color.blue()
        elif "🛡️ Bảo Vệ" in my_role:
            role_embed.description = "🛡️ Bạn là **Bảo Vệ**! Mỗi đêm được chọn bảo vệ 1 người. Không thể bảo vệ cùng 1 người trong 2 đêm liên tiếp."
            role_embed.color = discord.Color.green()
        elif "🧙‍♀️ Phù Thủy" in my_role:
            role_embed.description = "🧙‍♀️ Bạn là **Phù Thủy**! Sở hữu 1 bình cứu (hồi sinh người bị cắn) và 1 bình độc (giết người). Có thể xài cả 2 bình trong 1 đêm."
            role_embed.color = discord.Color.magenta()
        elif "🏹 Thợ Săn" in my_role:
            role_embed.description = "🏹 Bạn là **Thợ Săn**! Có duy nhất **1 viên đạn** để chủ động bắn đêm (từ đêm 2). Nếu bị chết hoặc bị vote chết, được quyền bắn kéo theo 1 người!"
            role_embed.color = discord.Color.dark_red()
        elif "💪 Người Mạnh Mẽ" in my_role:
            role_embed.description = "💪 Bạn là **Người Mạnh Mẽ**! Nếu bị Sói cắn ban đêm, bạn hông chết liền mà sáng ngày hôm sau nữa (sau 1 ngày 1 đêm) mới hi sinh."
            role_embed.color = discord.Color.dark_green()
        elif "🤢 Người Bị Bệnh" in my_role:
            role_embed.description = "🤢 Bạn là **Người Bị Bệnh**! Nếu bị Sói cắn chết, bầy Sói sẽ bị lây bệnh và đêm tiếp theo chúng hông thể đi cắn ai được nữa!"
            role_embed.color = discord.Color.teal()
        elif "💘 Thần Cupid" in my_role:
            role_embed.description = "💘 Bạn là **Thần Cupid**! Vào đầu game, được chọn ghép đôi 2 người bất kỳ với nhau. Nếu 1 người chết, người kia sẽ tự sát chết theo."
            role_embed.color = discord.Color.pink()
        elif "🌓 Nửa Người Nửa Sói" in my_role:
            role_embed.description = "🌓 Bạn là **Nửa Người Nửa Sói**! Ban đầu làm dân làng thường. Nhưng nếu bị Sói cắn trúng, bạn sẽ lập tức hóa Sói và gia nhập bầy Sói đi săn!"
            role_embed.color = discord.Color.dark_grey()
        elif "⚔️ Hiệp Sĩ Bóng Đêm" in my_role:
            role_embed.description = "⚔️ Bạn là **Hiệp Sĩ Bóng Đêm**! Ban ngày có **1 lần duy nhất** được quyền rút kiếm chém chết công khai 1 người. Chém trúng Sói thì Sói chết, chém nhầm Dân thì bạn tự sát chết theo!"
            role_embed.color = discord.Color.dark_blue()
        elif "⚖️ Judgeman" in my_role:
            role_embed.description = "⚖️ Bạn là **Judgeman** đầy quyền lực! Ban ngày có **1 lần duy nhất** được quyền lật ngược kết quả bỏ phiếu của cả làng, cứu sống người bị oan và treo cổ đứa nhiều phiếu nhì lên!"
            role_embed.color = discord.Color.gold()
            
        # --- PHE MA SÓI ---
        elif "🐺 Ma Sói" in my_role:
            role_embed.description = "🐺 Bạn là **Ma Sói**! Mỗi đêm cùng đồng bọn cắn 1 người. Quân số phe Sói bằng hoặc đông hơn phe Dân là phe Sói thắng!"
            role_embed.color = discord.Color.red()
        elif "🐾 Sói Con" in my_role:
            role_embed.description = "🐾 Bạn là **Sói Con**! Bạn hông đi cắn người được. Nhưng nếu bạn chết, đêm sau phe Sói sẽ phẫn nộ vùng lên và được cắn liền 2 người!"
            role_embed.color = discord.Color.dark_red()
        elif "⚡ Sói Điên Dại" in my_role:
            role_embed.description = "⚡ Bạn là **Sói Điên Dại**! Sau 10 đêm, nếu phe Sói chỉ còn duy nhất 1 mình bạn sống sót, bạn sẽ bộc phát cắn chết ngay 1 người rồi hóa thành Dân Làng."
            role_embed.color = discord.Color.orange()
        elif "🤖 Sói Bù Nhìn" in my_role:
            role_embed.description = "🤖 Bạn là **Sói Bù Nhìn** siêu tinh quái! Khi bị Tiên Tri soi, kết quả trả về luôn là **DÂN LÀNG**. Nếu ban ngày bị vote treo cổ, bạn hông chết ngay mà cả làng sẽ mất lượt treo cổ đó!"
            role_embed.color = discord.Color.dark_magenta()
        elif "🧪 Sói Lây Nhiễm" in my_role:
            role_embed.description = "🧪 Bạn là **Sói Lây Nhiễm**! Được xài kỹ năng lây nhiễm **2 lần** ván đấu. Người bị cắn hông chết ngay mà sau 1 ngày 1 đêm sẽ lây độc hóa thành Ma Sói!"
            role_embed.color = discord.Color.magenta()
            
        # --- PHE THỨ BA ---
        elif "🤪 Kẻ Chán Đời" in my_role:
            role_embed.description = "🤪 Bạn là **Kẻ Chán Đời**! Mục tiêu duy nhất là làm sao để bản thân bị CHẾT dưới bất kỳ hình thức nào. Chết là bạn WIN ngay lập tức!"
            role_embed.color = discord.Color.gold()
        elif "⚔️ Yuta" in my_role:
            role_embed.description = "⚔️ Bạn là **Yuta** cô độc! 2 đêm đầu là Dân thường. Từ đêm 3 được copy xài chức năng người đã chết 1 lần. Bạn phải đơn độc sống sót đến cuối để WIN một mình!"
            role_embed.color = discord.Color.blurple()
        elif "🌀 Thầy Thôi Miên" in my_role:
            role_embed.description = "🌀 Bạn là **Thầy Thôi Miên**! Mỗi đêm được chọn thôi miên **1 người**. Tất cả người còn sống bị thôi miên là bạn WIN! (Nếu có người bị thôi miên chết, phải bùa lại từ đầu)."
            role_embed.color = discord.Color.blue()
        elif "🦊 Cáo Chín Đuôi" in my_role:
            role_embed.description = "🦊 Bạn là **Cáo Chín Đuôi** lỳ lợm! Sở hữu **2 mạng**. Mỗi đêm được yểm lời nguyền lên 1 người. Nếu bạn sống đến cuối và số người bị nguyền chiếm một nửa số người còn sống -> Bạn WIN một mình!"
            role_embed.color = discord.Color.orange()
            
        if user_id in WEREWOLF_STATE["cupid_couple"]:
            partner_id = [p for p in WEREWOLF_STATE["cupid_couple"] if p != user_id]
            role_embed.add_field(
                name="❤️ TÌNH YÊU SÉT ĐÁNH (CUPID COUPLE)", 
                value=f"Bạn đã bị Cupid ghép đôi với <@{partner_id}>! Tạo thành phe Cặp Đôi độc lập. Phải giết sạch những người còn lại để cùng sống sót đến cuối ván mới WIN nha! 💔",
                inline=False
            )
            
        await interaction.response.send_message(embed=role_embed, ephemeral=True)
# ==========================================
# 🐺 6. HỆ THỐNG GAME MA SÓI HOÀN CHỈNH 20 VAI TRÒ (PHẦN B) 🐺
# ==========================================
    # 🔮 MENU HÀNH ĐỘNG ĐÊM CỦA THẦY THÔI MIÊN
    async def open_hypnotist_menu(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if WEREWOLF_STATE["players"].get(user_id, {}).get("role") != "Thầy Thôi Miên" or not WEREWOLF_STATE["players"][user_id]["alive"]:
            await interaction.response.send_message("Chức năng này chỉ dành cho Thầy Thôi Miên còn sống! 🔮", ephemeral=True)
            return

        options = []
        for p_id, info in WEREWOLF_STATE["players"].items():
            if info["alive"] and p_id != user_id:
                member = interaction.guild.get_member(int(p_id))
                name = member.display_name if member else f"Dân làng {p_id}"
                options.append(discord.SelectOption(label=name, value=p_id, emoji="🌀"))

        class HypnoSelect(discord.ui.Select):
            def __init__(self, game_instance):
                super().__init__(placeholder="Chọn đúng 2 người để thôi miên...", options=options, min_values=2, max_values=2)
                self.game = game_instance

            async def callback(self, select_interaction: discord.Interaction):
                chosen = [int(x) for x in self.values]
                WEREWOLF_STATE["hypnotized_players"] = list(set(WEREWOLF_STATE["hypnotized_players"] + chosen))
                await select_interaction.response.send_message(f"🌀 Phép bùa mê đã kích hoạt! Bạn đã thôi miên thành công: <@{chosen[0]}> và <@{chosen[1]}>!", ephemeral=True)

        view = discord.ui.View(timeout=60)
        view.add_item(HypnoSelect(self))
        await interaction.response.send_message("🔮 Hỡi Thầy Thôi Miên, hãy chọn 2 linh hồn tội nghiệp để yểm bùa đêm nay:", view=view, ephemeral=True)

    # 🏹 MENU HÀNH ĐỘNG ĐÊM CỦA THỢ SĂN
    async def open_hunter_menu(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if WEREWOLF_STATE["players"].get(user_id, {}).get("role") != "Thợ Săn" or not WEREWOLF_STATE["players"][user_id]["alive"]:
            await interaction.response.send_message("Chức năng này chỉ dành cho Thợ Săn còn sống! 🏹", ephemeral=True)
            return

        if WEREWOLF_STATE["night_count"] < 2:
            await interaction.response.send_message("❌ Theo luật của chị chủ nhân, từ đêm thứ 2 bạn mới nạp xong đạn để bắn nha!", ephemeral=True)
            return

        if WEREWOLF_STATE["hunter_bullet_used"]:
            await interaction.response.send_message("❌ Bạn đã bắn viên đạn duy nhất của cả trận đấu ở đêm trước rồi!", ephemeral=True)
            return

        options = [discord.SelectOption(label="Không bắn ai cả (Giữ đạn)", value="skip", emoji="🛡️")]
        for p_id, info in WEREWOLF_STATE["players"].items():
            if info["alive"] and p_id != user_id:
                member = interaction.guild.get_member(int(p_id))
                name = member.display_name if member else f"Dân làng {p_id}"
                options.append(discord.SelectOption(label=name, value=p_id, emoji="🎯"))

        class HunterSelect(discord.ui.Select):
            def __init__(self, game_instance):
                super().__init__(placeholder="Chọn mục tiêu để găm đạn...", options=options)
                self.game = game_instance

            async def callback(self, select_interaction: discord.Interaction):
                val = self.values[0]
                if val == "skip":
                    await select_interaction.response.send_message("🏹 Bạn quyết định ôm súng đi ngủ, giữ lại viên đạn quý giá!", ephemeral=True)
                else:
                    self.game.night_actions["hunter_shoot"] = int(val)
                    WEREWOLF_STATE["hunter_bullet_used"] = True
                    await select_interaction.response.send_message(f"🎯 Đoàng! Bạn đã lên nòng súng nhắm thẳng vào đầu <@{val}>!", ephemeral=True)

        view = discord.ui.View(timeout=60)
        view.add_item(HunterSelect(self))
        await interaction.response.send_message("🏹 Hỡi Thợ Săn, đêm nay bạn có muốn nổ súng tiễn biệt ai không?", view=view, ephemeral=True)

    # 🃏 MENU HÀNH ĐỘNG ĐÊM CỦA YUTA ĐƠN ĐỘC
    async def open_yuta_menu(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if WEREWOLF_STATE["players"].get(user_id, {}).get("role") != "Yuta" or not WEREWOLF_STATE["players"][user_id]["alive"]:
            await interaction.response.send_message("Chức năng này chỉ dành cho Yuta còn sống! 🃏", ephemeral=True)
            return

        if WEREWOLF_STATE["night_count"] < 3:
            await interaction.response.send_message("🃏 Bạn là Yuta! 2 đêm đầu bạn làm dân thường, từ đêm thứ 3 mới được copy năng lực nha!", ephemeral=True)
            return

        # Tìm những người đã chết để Yuta chọn copy chức năng theo luật của chị
        dead_options = []
        for p_id, info in WEREWOLF_STATE["players"].items():
            if not info["alive"] and info["role"] != "Dân Làng":
                member = interaction.guild.get_member(int(p_id))
                name = member.display_name if member else f"Người chết {p_id}"
                dead_options.append(discord.SelectOption(label=f"{name} ({info['role']})", value=p_id, emoji="👻"))

        if not dead_options:
            await interaction.response.send_message("🃏 Chưa có ai có chức năng bị chết để bạn copy năng lực cả!", ephemeral=True)
            return

        class YutaSelect(discord.ui.Select):
            def __init__(self, game_instance):
                super().__init__(placeholder="Chọn 1 người chết để copy vai trò của họ...", options=dead_options)
                self.game = game_instance

            async def callback(self, select_interaction: discord.Interaction):
                target_dead = self.values[0]
                copied_role = WEREWOLF_STATE["players"][target_dead]["role"]
                WEREWOLF_STATE["players"][user_id]["role"] = copied_role
                await select_interaction.response.send_message(f"🃏 Linh hồn thức tỉnh! Bạn đã copy thành công vai trò **{copied_role}** của người quá cố!", ephemeral=True)

        view = discord.ui.View(timeout=60)
        view.add_item(YutaSelect(self))
        await interaction.response.send_message("🃏 Hỡi Yuta, hãy chọn 1 người đã khuất để đoạt lấy năng lực của họ đêm nay:", view=view, ephemeral=True)
# 🗳️ VIEW XỬ LÝ BIỂU QUYẾT TREO CỔ BAN NGÀY & KIỂM TRA SKIP
class WerewolfVoteView(discord.ui.View):
    def __init__(self, game_instance):
        super().__init__(timeout=90)
        self.game = game_instance
        self.votes = {}  # {target_id: số_phiếu}
        self.skip_votes = 0
        self.voted_players = set()
        
        # 👨‍🌾 TẠO NÚT BẤM VOTE CHO TỪNG NGƯỜI CÒN SỐNG
        for p_id, info in WEREWOLF_STATE["players"].items():
            if info["alive"]:
                member = game_instance.bot.get_channel(game_instance.channel_id).guild.get_member(int(p_id))
                name = member.display_name if member else f"Dân làng {p_id}"
                self.add_item(self.create_vote_button(name, p_id))
                
        # Thêm nút SKIP (Bỏ qua treo cổ)
        self.add_item(self.create_skip_button())

    def create_vote_button(self, name, target_id):
        @discord.ui.button(label=f"Vote {name}", style=discord.ButtonStyle.secondary)
        async def callback(button, interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            
            # 🛑 KIỂM TRA LUẬT: Người chết rồi không được vote nha!
            if not WEREWOLF_STATE["players"].get(user_id, {}).get("alive", False):
                await interaction.response.send_message("💀 Bạn đã rời cuộc chơi rồi, không được can thiệp vào chuyện nhân gian đâu nha!", ephemeral=True)
                return
                
            if user_id in self.voted_players:
                await interaction.response.send_message("Bạn đã bỏ phiếu biểu quyết ngày hôm nay rồi! ❌", ephemeral=True)
                return
                
            self.voted_players.add(user_id)
            self.votes[target_id] = self.votes.get(target_id, 0) + 1
            await interaction.response.send_message(f"🗳️ Bạn đã vote treo cổ <@{target_id}>!", ephemeral=True)
        return callback

    def create_skip_button(self):
        @discord.ui.button(label="Bỏ qua Treo Cổ ⏭️", style=discord.ButtonStyle.success)
        async def callback(button, interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            
            # 🛑 KIỂM TRA LUẬT: Người chết không được bấm Skip!
            if not WEREWOLF_STATE["players"].get(user_id, {}).get("alive", False):
                await interaction.response.send_message("💀 Bạn đã rời cuộc chơi rồi, không được bấm Skip đâu nha!", ephemeral=True)
                return
                
            if user_id in self.voted_players:
                await interaction.response.send_message("Bạn đã bỏ phiếu biểu quyết ngày hôm nay rồi! ❌", ephemeral=True)
                return
                
            self.voted_players.add(user_id)
            self.skip_votes += 1
            await interaction.response.send_message("⏭️ Bạn đã vote Bỏ qua treo cổ trong ngày hôm nay!", ephemeral=True)
        return callback

    async def on_timeout(self):
        channel = self.game.bot.get_channel(self.game.channel_id)
        if not channel:
            return
            
        # Sắp xếp danh sách phiếu từ nhiều đến ít
        sorted_votes = sorted(self.votes.items(), key=lambda x: x, reverse=True)
        final_dead_id = None
        
        # Kiểm tra xem số phiếu vote người cao nhất có lớn hơn số phiếu SKIP hay không
        if sorted_votes and sorted_votes[0][1] > self.skip_votes:
            final_dead_id = sorted_votes[0][0]
        else:
            # ⏭️ LUẬT CỦA CHỊ: Nếu số phiếu SKIP nhiều nhất hoặc bằng phiếu vote -> Không ai bị treo cổ!
            await channel.send("⏭️ **Kết quả biểu quyết:** Làng quyết định tin tưởng nhau hoặc số phiếu Skip nhiều hơn, nên đã **BỎ QUA** lượt treo cổ hôm nay! Làng giữ nguyên sĩ số.")
            return

        # Thực thi treo cổ người bị vote nhiều nhất
        if final_dead_id:
            role_before_death = WEREWOLF_STATE["players"][str(final_dead_id)]["role"]
            
            # LUẬT SÓI BÙ NHÌN CỦA CHỊ: Treo trúng nó là cả làng mất lượt treo cổ
            if role_before_death == "Sói Bù Nhìn":
                await channel.send(f"🎭 Cả làng áp giải <@{final_dead_id}> lên giàn... Nhưng hắn chính là **Sói Bù Nhìn**! Sự tinh quái của hắn khiến làng bối rối giải tán và **mất lượt treo cổ** hôm nay!")
                return
                
            await self.game.process_player_death(int(final_dead_id), self.game.bot, channel)
            await channel.send(f"⚖️ **Kết quả treo cổ:** Sức ép của dư luận quá lớn, cả làng đã quyết định tiễn <@{final_dead_id}> rời cuộc chơi!")

class WerewolfJoinView(discord.ui.View):
    def __init__(self, host_id):
        super().__init__(timeout=180)
        self.host_id = host_id
        self.players = [host_id]

    @discord.ui.button(label="Vào Làng 🏕️", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.players:
            await interaction.response.send_message("Bạn đã có hộ khẩu trong làng Ma Sói rồi nè! 😉", ephemeral=True)
        else:
            self.players.append(interaction.user.id)
            await interaction.response.send_message(f"✨ Dân làng **{interaction.user.display_name}** đã dọn đồ vào làng Ma Sói!", ephemeral=False)

    @discord.ui.button(label="Khởi Tranh 🚀", style=discord.ButtonStyle.blurple)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host_id:
            await interaction.response.send_message("Chỉ có chủ bàn mới có quyền đánh trống mở ván thôi ạ! ❌", ephemeral=True)
            return
        
        num_players = len(self.players)
        if num_players < 4:
            await interaction.response.send_message("Huhu, Ma Sói cần ít nhất **4 người trở lên** chơi mới vui và chia bài hợp lý được ạ! 🥺", ephemeral=True)
            return

        self.stop()
        
        wolf_roles_pool = ["🐾 Sói Con (Wolf Cub)", "⚡ Sói Điên Dại (Mad Wolf)", "🤖 Sói Bù Nhìn (Puppet Wolf)", "🧪 Sói Lây Nhiễm (Infected Wolf)"]
        good_roles_pool = [
            "🔮 Tiên Tri (Seer)", "🛡️ Bảo Vệ (Bodyguard)", "🧙‍♀️ Phù Thủy (Witch)", 
            "🏹 Thợ Săn (Hunter)", "💪 Người Mạnh Mẽ (Strong Man)", "🤢 Người Bị Bệnh (Sick Man)", 
            "💘 Thần Cupid (Cupid)", "🌓 Nửa Người Nửa Sói (Wild Child)", "⚔️ Hiệp Sĩ Bóng Đêm (Knight)",
            "⚖️ Judgeman (Judge)"
        ]
        third_party_pool = ["🤪 Kẻ Chán Đời (Fool)", "⚔️ Yuta (Yuta)", "🌀 Thầy Thôi Miên (Hypnotist)", "🦊 Cáo Chín Đuôi (Nine-Tailed Fox)"]
        
        base_roles = ["🐺 Ma Sói (Werewolf)"] 
        
        if num_players >= 7:
            base_roles.append(random.choice(wolf_roles_pool))
            
        slots_needed = num_players - len(base_roles)
        chosen_specials = []
        
        # Lọc Phe Thứ 3 thông minh theo sòng 4-6 người
        if 4 <= num_players <= 6:
            max_third_party = random.randint(1, 2)
            chosen_third = random.sample(third_party_pool, min(max_third_party, slots_needed))
            chosen_specials.extend(chosen_third)
            
            remains = slots_needed - len(chosen_third)
            if remains > 0:
                chosen_goods = random.sample(good_roles_pool, min(remains, len(good_roles_pool)))
                chosen_specials.extend(chosen_goods)
        else:
            full_pool = good_roles_pool + third_party_pool
            chosen_specials = random.sample(full_pool, min(slots_needed, len(full_pool)))
            
        base_roles.extend(chosen_specials)
        
        while len(base_roles) < num_players:
            base_roles.append("👨‍🌾 Dân Làng (Villager)")
            
        random.shuffle(base_roles)
        
        WEREWOLF_STATE["players"] = self.players
        WEREWOLF_STATE["dead_players"] = []
        WEREWOLF_STATE["player_roles"] = {}
        WEREWOLF_STATE["current_roles"] = {}
        WEREWOLF_STATE["cupid_couple"] = []
        WEREWOLF_STATE["night_count"] = 1
        WEREWOLF_STATE["hypnotized"] = []
        WEREWOLF_STATE["judgeman_used"] = False
        
        player_mentions = []
        for idx, p_id in enumerate(self.players):
            WEREWOLF_STATE["player_roles"][p_id] = base_roles[idx]
            WEREWOLF_STATE["current_roles"][p_id] = base_roles[idx]
            player_mentions.append(f"<@{p_id}>")
            
        mentions_str = ", ".join(player_mentions)
        embed_start = discord.Embed(
            title="🐺 LÀNG MA SÓI CHÍNH THỨC VÀO ĐÊM 🐺",
            description=f"🚀 **VÁN MA SÓI CHÍNH THỨC BẮT ĐẦU!** 🚀\n🔥 Tổng số dân làng: **{num_players}**. Hãy bấm nút bên dưới để kiểm tra vai trò bí mật và chuẩn bị đấu trí sinh tử!\n\n👥 **Danh sách dân làng:** {mentions_str}",
            color=discord.Color.dark_purple()
        )
        await interaction.response.send_message(embed=embed_start, view=WerewolfRoleView(WEREWOLF_STATE["player_roles"]))
        game_instance = WerewolfGame(interaction.channel_id)
        interaction.client.loop.create_task(game_instance.start_game_loop(interaction.client))
    # 🔄 VÒNG LẶP CHẠY GAME NGÀY/ĐÊM TỰ ĐỘNG VÔ HẠN (ĐÃ TÍCH HỢP VOTE BAN NGÀY MỚI)
    async def start_game_loop(self, bot):
        self.game_in_progress = True
        channel = bot.get_channel(self.channel_id)
        if not channel:
            return
        
        while self.game_in_progress:
            current_night = WEREWOLF_STATE["night_count"]
            
            # --- 🌙 GIAI ĐOẠN BAN ĐÊM BUÔNG XUỐNG ---
            await channel.send(f"🌙 **Đêm Thứ {current_night} buông xuống...** Mọi người hãy đi ngủ đi điều kỳ diệu sắp xảy ra~")
            
            await channel.send("🛡️ Chức năng **Bảo Vệ** và **Tiên Tri** đang âm thầm tỉnh giấc hành sự...")
            await asyncio.sleep(30)
            
            await channel.send("🐺 Phe **Ma Sói** thức giấc, bàn mưu chọn con mồi rướm máu...")
            await asyncio.sleep(30)
            
            await channel.send("🧪 **Phù Thủy** tỉnh giấc, đưa mắt nhìn các bình thuốc quyền năng...")
            await asyncio.sleep(30)
            
            # Tính toán kết quả đêm lật bài
            await self.process_night_results(bot, channel)
            
            # Kiểm tra xem có ai lật kèo chiến thắng chưa để dứt điểm trận đấu
            winner = self.check_victory_conditions()
            if winner != "":
                self.game_in_progress = False
                await channel.send(f"🎉 **TRẬN ĐẤU CHÍNH THỨC KẾT THÚC!** 🎉\nPhe giành chiến thắng vinh quang là: **{winner}**! Xin chúc mừng~ 🥳")
                break
                
            # --- ☀️ GIAI ĐOẠN BAN NGÀY THẢO LUẬN (1 PHÚT 30 GIÂY MỚI) ---
            # Gọi bảng nút bấm vote kèm nút Skip
            vote_view = WerewolfVoteView(self)
            
            await channel.send(
                f"☀️ **Ban Ngày Thứ {current_night} bắt đầu!** Làng có **1 phút 30 giây** để tranh luận nảy lửa. Hãy bấm các nút bên dưới để Vote treo cổ hoặc chọn Bỏ qua (Skip) nha! 🔥",
                view=vote_view
            )
            
            # Chờ đúng 90 giây (1 phút 30 giây) theo luật mới của chị để nút tự đóng và tính kết quả
            await asyncio.sleep(90) 

@bot.tree.command(name="masoi", description="Mở phòng chờ chơi game Ma Sói ẩn danh phiên bản nút bấm 🐺")
async def start_masoi(interaction: discord.Interaction):
    view = WerewolfJoinView(interaction.user.id)
    embed = discord.Embed(
        title="🐺 LÀNG MA SÓI TRỰC TUYẾN 🐺", 
        description=f"Chủ sòng {interaction.user.mention} đã mở một làng Ma Sói! Bấm nút bên dưới để vào làng tham gia sinh tử chiến.", 
        color=discord.Color.dark_blue()
    )
    await interaction.response.send_message(embed=embed, view=view)

bot.run(DISCORD_TOKEN)
